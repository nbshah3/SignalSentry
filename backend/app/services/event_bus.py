from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List


class EventBus:
    def __init__(self) -> None:
        self._subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def publish(self, event: Dict[str, Any]) -> None:
        async with self._lock:
            subscribers = list(self._subscribers)
        for queue in subscribers:
            await queue.put(event)

    async def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers.append(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        async with self._lock:
            if queue in self._subscribers:
                self._subscribers.remove(queue)


event_bus = EventBus()


def format_sse(event: Dict[str, Any]) -> str:
    payload = json.dumps(event)
    return f"data: {payload}\n\n"
