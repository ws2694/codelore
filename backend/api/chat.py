"""Chat API — proxies questions to Agent Builder."""

from fastapi import APIRouter, HTTPException

from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.agent_builder import get_agent_builder

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
async def ask(request: ChatRequest):
    """Send a question to CodeLore agent and get a sourced answer."""
    ab = get_agent_builder()

    # Prepend mode instruction if not default Ask
    message = request.question
    if request.mode == "onboard":
        message = f"[ONBOARD MODE] {message}"
    elif request.mode == "explore":
        message = f"[EXPLORE MODE] {message}"

    try:
        result = await ab.converse(
            message=message,
            conversation_id=request.conversation_id,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent Builder error: {str(e)}")

    # Extract answer from Agent Builder response (nested under "response")
    response_data = result.get("response", {})
    answer = response_data.get("message", "") if isinstance(response_data, dict) else ""
    conversation_id = result.get("conversation_id")

    # Parse sources from the answer (Agent Builder includes them in the response text)
    sources = []
    steps = result.get("steps", [])
    for step in steps:
        if "tool_calls" in step:
            for call in step["tool_calls"]:
                sources.append({
                    "tool": call.get("tool_id", ""),
                    "params": call.get("params", {}),
                })

    return ChatResponse(
        answer=answer,
        conversation_id=conversation_id,
        sources=sources,
    )
