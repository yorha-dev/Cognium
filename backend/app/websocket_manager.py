import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._send_locks: dict[WebSocket, asyncio.Lock] = {}

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()

        self._connections.add(ws)
        self._send_locks[ws] = asyncio.Lock()

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        self._send_locks.pop(ws, None)

    async def send_json(
        self,
        ws: WebSocket,
        payload: dict
    ) -> bool:
        lock = self._send_locks.get(ws)

        if lock is None:
            return False

        try:
            async with lock:
                await ws.send_json(payload)

            return True
        except Exception:
            logger.exception("WebSocket send failed")
            self.disconnect(ws)
            return False

    async def broadcast(self, payload: dict) -> None:
        connections = list(self._connections)

        if not connections:
            return

        await asyncio.gather(
            *(
                self.send_json(ws, payload)
                for ws in connections
            ),
            return_exceptions=True
        )

websocket_manager = WebSocketManager()
