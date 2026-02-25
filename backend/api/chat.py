"""Chat API — proxies questions to Agent Builder."""

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.config import get_settings
from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.agent_builder import get_agent_builder
from backend.services.auth_store import get_auth_state
from backend.services.sse_helpers import stream_response, sse_event, sse_error
from backend.services import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_repo_context() -> str:
    """Return a repo-scoping prefix for agent messages."""
    repo = get_auth_state().selected_repo or get_settings().github_repo
    if repo:
        return f"[REPO: {repo}] IMPORTANT: Only query data where repo == \"{repo}\". "
    return ""


def _prepare_message(request: ChatRequest) -> str:
    repo_ctx = _get_repo_context()
    message = request.question
    if request.mode == "onboard":
        message = f"{repo_ctx}[ONBOARD MODE] {message}"
    elif request.mode == "explore":
        message = f"{repo_ctx}[EXPLORE MODE] {message}"
    else:
        message = f"{repo_ctx}{message}"
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


async def _converse_cached(request: ChatRequest) -> dict:
    """Call Agent Builder with caching. Skip cache for ongoing conversations."""
    repo = get_auth_state().selected_repo or get_settings().github_repo or ""

    # Only cache first-turn questions (no conversation_id = fresh question)
    cache_key = None
    if not request.conversation_id:
        cache_key = f"chat:{repo}:{request.mode}:{request.question}"
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info("Chat cache hit: %s", request.question[:50])
            return cached

    ab = get_agent_builder()
    result = await ab.converse(
        message=_prepare_message(request),
        conversation_id=request.conversation_id,
    )

    if cache_key:
        cache.put(cache_key, result)

    return result


@router.post("/ask", response_model=ChatResponse)
async def ask(request: ChatRequest):
    """Send a question to CodeLore agent and get a sourced answer."""
    try:
        result = await _converse_cached(request)
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

        try:
            result = await _converse_cached(request)
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
