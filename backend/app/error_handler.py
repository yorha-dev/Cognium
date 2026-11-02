import asyncio
import logging
from dataclasses import dataclass
from typing import Callable, Awaitable
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class Error:
    event_type: str
    error_type: str
    description: str
    details: dict
    traceback: str
    timestamp: str

class ErrorHandler:
    _instance = None
    _loop = None
    _queue = None
    _task = None
    _sender = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    async def start(
        self,
        sender: Callable[[dict], Awaitable[None]]
    ) -> None:
        if self._task is not None and not self._task.done():
            return

        self._loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue()
        self._sender = sender
        self._task = asyncio.create_task(self._dispatch())

    def register(
        self,
        event_type:str,
        error_type: str,
        description: str,
        traceback: str,
        details: dict | None = None
    ) -> None:
        if self._loop is None or self._queue is None:
            logger.error("ErrorHandler has not started")
            return

        error = Error(
            event_type=event_type,
            error_type=error_type,
            description=description,
            details=details or {},
            traceback=traceback,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Book insertion without wait for consumer
        self._loop.call_soon_threadsafe(self._enqueue, error)

    def _enqueue(self, error: Error) -> None:
        try:
            self._queue.put_nowait(error)
        except asyncio.QueueFull:
            logger.error("Error event queue is full; event discarted")

    async def _dispatch(self) -> None:
        while True:
            error = await self._queue.get()

            try:
                payload = {
                    'type': "error",
                    'content': {
                        'event_type': error.event_type,
                        'error_type': error.error_type,
                        'description': error.description,
                        'details': error.details,
                        'timestamp': error.timestamp
                    }
                }

                await self._sender(payload)
            except Exception:
                logger.exception("Failed to dispatch error event")
            finally:
                self._task.cancel()

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()

        try:
            await self._task
        except asyncio.CancelledError:
            pass

        self._task = None
        self._queue = None
        self._loop = None
        self._sender = None
