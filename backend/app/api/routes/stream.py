import asyncio
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.services.event_bus import event_bus, format_sse

router = APIRouter(tags=["stream"])


async def _event_generator() -> AsyncIterator[str]:
    queue = await event_bus.subscribe()
    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15)
                yield format_sse(event)
            except asyncio.TimeoutError:
                yield "event: ping\ndata: {}\n\n"
    finally:
        await event_bus.unsubscribe(queue)


@router.get("/stream/events")
async def stream_events() -> StreamingResponse:
    return StreamingResponse(_event_generator(), media_type="text/event-stream")
