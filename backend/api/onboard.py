"""Onboard API — generates guided learning paths via Agent Builder."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.services.agent_builder import get_agent_builder
from backend.services.sse_helpers import stream_response, sse_event, sse_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboard", tags=["onboard"])


def _start_prompt(module: str, topic: str) -> str:
    if module:
        return (
            f"[ONBOARD MODE] Generate step 1 of a learning path for the '{module}' module. "
            f"Start with the most important architectural decision, explain why it was made, "
            f"list the key files involved, and cite your sources. "
            f"At the end, tell me how many total steps there will be."
        )
    return (
        f"[ONBOARD MODE] Generate step 1 of a learning path for this codebase. "
        f"Topic: {topic}. Start with a high-level overview of the architecture, "
        f"the most important design decisions, and the key modules. "
        f"Cite your sources. At the end, tell me how many total steps there will be."
    )


def _next_prompt(current_step: int) -> str:
    return (
        f"[ONBOARD MODE] Continue to step {current_step + 1} of the learning path. "
        f"Explain the next most important concept, decision, or module. "
        f"Include key files, rationale, and sources. Keep your response concise."
    )


def _fallback_prompt(current_step: int) -> str:
    return (
        f"[ONBOARD MODE] Generate step {current_step + 1} of a codebase learning path. "
        f"The previous {current_step} steps already covered the basics. "
        f"Now explain the next most important concept, decision, or module "
        f"that hasn't been covered yet. Include key files, rationale, and sources. "
        f"Keep your response concise."
    )


def _extract(result: dict) -> str:
    response_data = result.get("response", {})
    return response_data.get("message", "") if isinstance(response_data, dict) else ""


# ── Non-streaming endpoints (kept for backward compatibility) ────────────


@router.post("/start")
async def start_onboarding(module: str = "", topic: str = "architecture"):
    """Start an onboarding learning path for a module or the whole codebase."""
    ab = get_agent_builder()

    try:
        result = await ab.converse(message=_start_prompt(module, topic))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent Builder error: {str(e)}")

    return {
        "step": 1,
        "content": _extract(result),
        "conversation_id": result.get("conversation_id"),
    }


@router.post("/next")
async def next_step(conversation_id: str, current_step: int = 1):
    """Continue to the next onboarding step."""
    ab = get_agent_builder()

    try:
        result = await ab.converse(
            message=_next_prompt(current_step),
            conversation_id=conversation_id,
        )
    except Exception:
        logger.warning(
            "Onboard step %d failed on conversation %s, starting fresh conversation",
            current_step + 1, conversation_id,
        )
        try:
            result = await ab.converse(message=_fallback_prompt(current_step))
        except Exception as e:
            logger.error("Onboard fallback also failed: %s", e, exc_info=True)
            raise HTTPException(status_code=502, detail=f"Agent Builder error: {str(e)}")

    return {
        "step": current_step + 1,
        "content": _extract(result),
        "conversation_id": result.get("conversation_id"),
    }


# ── Streaming endpoints ─────────────────────────────────────────────────

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.post("/start/stream")
async def start_onboarding_stream(module: str = "", topic: str = "architecture"):
    """Start onboarding with SSE streaming response."""

    async def event_generator():
        yield sse_event("status", {"phase": "thinking", "message": "Preparing your learning path..."})

        ab = get_agent_builder()

        try:
            result = await ab.converse(message=_start_prompt(module, topic))
        except Exception as e:
            logger.error("Agent Builder error during onboard start stream: %s", e, exc_info=True)
            yield sse_error(f"Agent Builder error: {e}", 502)
            return

        metadata = {
            "step": 1,
            "conversation_id": result.get("conversation_id"),
        }

        async for event in stream_response(_extract(result), metadata):
            yield event

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=_SSE_HEADERS)


@router.post("/next/stream")
async def next_step_stream(conversation_id: str, current_step: int = 1):
    """Continue onboarding with SSE streaming response."""

    async def event_generator():
        yield sse_event("status", {"phase": "thinking", "message": "Loading next step..."})

        ab = get_agent_builder()

        try:
            result = await ab.converse(
                message=_next_prompt(current_step),
                conversation_id=conversation_id,
            )
        except Exception:
            logger.warning(
                "Onboard step %d failed on conversation %s, trying fallback",
                current_step + 1, conversation_id,
            )
            try:
                result = await ab.converse(message=_fallback_prompt(current_step))
            except Exception as e:
                logger.error("Onboard fallback also failed: %s", e, exc_info=True)
                yield sse_error(f"Agent Builder error: {e}", 502)
                return

        metadata = {
            "step": current_step + 1,
            "conversation_id": result.get("conversation_id"),
        }

        async for event in stream_response(_extract(result), metadata):
            yield event

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=_SSE_HEADERS)
