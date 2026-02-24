"""Chat API — proxies questions to Agent Builder."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.agent_builder import get_agent_builder
from backend.services.sse_helpers import stream_response, sse_event, sse_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _prepare_message(request: ChatRequest) -> str:
    message = request.question
    if request.mode == "onboard":
        message = f"[ONBOARD MODE] {message}"
    elif request.mode == "explore":
        message = f"[EXPLORE MODE] {message}"
    return message


def _parse_sources(result: dict) -> list[dict]:
    sources = []
    for step in result.get("steps", []):
        if "tool_calls" in step:
            for call in step["tool_calls"]:
                sources.append({
                    "tool": call.get("tool_id", ""),
                    "params": call.get("params", {}),
                })
    return sources


@router.post("/ask", response_model=ChatResponse)
async def ask(request: ChatRequest):
    """Send a question to CodeLore agent and get a sourced answer."""
    ab = get_agent_builder()

    try:
        result = await ab.converse(
            message=_prepare_message(request),
            conversation_id=request.conversation_id,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent Builder error: {str(e)}")

    response_data = result.get("response", {})
    answer = response_data.get("message", "") if isinstance(response_data, dict) else ""

    return ChatResponse(
        answer=answer,
        conversation_id=result.get("conversation_id"),
        sources=_parse_sources(result),
    )


@router.post("/ask/stream")
async def ask_stream(request: ChatRequest):
    """Send a question to CodeLore agent with SSE streaming response."""

    async def event_generator():
        yield sse_event("status", {"phase": "thinking", "message": "Searching codebase memory..."})

        ab = get_agent_builder()

        try:
            result = await ab.converse(
                message=_prepare_message(request),
                conversation_id=request.conversation_id,
            )
        except Exception as e:
            logger.error("Agent Builder error during chat stream: %s", e, exc_info=True)
            yield sse_error(f"Agent Builder error: {e}", 502)
            return

        response_data = result.get("response", {})
        answer = response_data.get("message", "") if isinstance(response_data, dict) else ""

        metadata = {
            "conversation_id": result.get("conversation_id"),
            "sources": _parse_sources(result),
        }

        async for event in stream_response(answer, metadata):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
