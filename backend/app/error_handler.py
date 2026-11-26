import asyncio
import logging
from dataclasses import dataclass
from typing import Callable, Awaitable
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    NETWORK = 'network'
    DATABASE = 'database'
    INFERENCE = 'inference'
    FILE = 'file'
    INTERNAL = 'internal'
    UNKNOW = 'unknow'

class ErrorSeverity(Enum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'

@dataclass
class Error:
    category: ErrorCategory
    severity: ErrorSeverity
    code: str
    detail: str
    description: str
    source: str
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
        category: ErrorCategory,
        severity: ErrorSeverity,
        code: str,
        detail: str,
        description: str,
        source: str,
        traceback: str,
    ) -> None:
        if self._loop is None or self._queue is None:
            logger.error("ErrorHandler has not started")
            return

        error = Error(
            category=category,
            severity=severity,
            code=code,
            detail=detail,
            description=description,
            source=source,
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
                        'category': str(error.category),
                        'severity': str(error.severity),
                        'code': error.code,
                        'detail': str(error.detail),
                        'description': error.description,
                        'source': error.source,
                        'traceback': error.traceback,
                        'timestamp': error.timestamp
                    }
                }

                await self._sender(payload)
            except Exception:
                logger.exception("Failed to dispatch error event")

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
