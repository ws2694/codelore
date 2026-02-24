"""SSE streaming utilities for chunked typewriter-style responses."""

import asyncio
import json
import re
from collections.abc import AsyncGenerator


def chunk_text(text: str, target_size: int = 25) -> list[str]:
    """Split text into chunks at word/sentence boundaries for typewriter effect."""
    if not text:
        return []

    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= target_size:
            chunks.append(remaining)
            break

        # Look for a sentence break (.!? followed by space) in a window
        window = remaining[: target_size + 15]
        sentence_break = -1
        for m in re.finditer(r"[.!?]\s", window):
            if m.end() >= target_size // 2:
                sentence_break = m.end()
                break

        if sentence_break > 0:
            split_at = sentence_break
        else:
            last_space = window.rfind(" ")
            split_at = last_space + 1 if last_space > 0 else target_size

        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:]

    return chunks


def sse_event(event_type: str, data: dict) -> str:
    """Format a single SSE event string."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def sse_error(message: str, code: int = 500) -> str:
    """Format an SSE error event."""
    return sse_event("error", {"message": message, "code": code})


async def stream_response(
    text: str,
    metadata: dict,
    chunk_delay: float = 0.03,
    target_chunk_size: int = 25,
) -> AsyncGenerator[str, None]:
    """Generate SSE events: status(streaming) -> metadata -> chunks -> done."""
    yield sse_event("status", {"phase": "streaming", "message": "Generating response..."})
    yield sse_event("metadata", metadata)

    for chunk in chunk_text(text, target_chunk_size):
        yield sse_event("chunk", {"text": chunk})
        await asyncio.sleep(chunk_delay)

    yield sse_event("done", {})
