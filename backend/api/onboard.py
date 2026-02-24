"""Onboard API — generates guided learning paths via Agent Builder."""

import logging

from fastapi import APIRouter, HTTPException

from backend.services.agent_builder import get_agent_builder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboard", tags=["onboard"])


@router.post("/start")
async def start_onboarding(module: str = "", topic: str = "architecture"):
    """Start an onboarding learning path for a module or the whole codebase."""
    ab = get_agent_builder()

    if module:
        prompt = (
            f"[ONBOARD MODE] Generate step 1 of a learning path for the '{module}' module. "
            f"Start with the most important architectural decision, explain why it was made, "
            f"list the key files involved, and cite your sources. "
            f"At the end, tell me how many total steps there will be."
        )
    else:
        prompt = (
            f"[ONBOARD MODE] Generate step 1 of a learning path for this codebase. "
            f"Topic: {topic}. Start with a high-level overview of the architecture, "
            f"the most important design decisions, and the key modules. "
            f"Cite your sources. At the end, tell me how many total steps there will be."
        )

    try:
        result = await ab.converse(message=prompt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent Builder error: {str(e)}")

    response_data = result.get("response", {})
    content = response_data.get("message", "") if isinstance(response_data, dict) else ""

    return {
        "step": 1,
        "content": content,
        "conversation_id": result.get("conversation_id"),
    }


@router.post("/next")
async def next_step(conversation_id: str, current_step: int = 1):
    """Continue to the next onboarding step."""
    ab = get_agent_builder()

    prompt = (
        f"[ONBOARD MODE] Continue to step {current_step + 1} of the learning path. "
        f"Explain the next most important concept, decision, or module. "
        f"Include key files, rationale, and sources. Keep your response concise."
    )

    try:
        result = await ab.converse(
            message=prompt,
            conversation_id=conversation_id,
        )
    except Exception:
        # Conversation context may have exceeded the LLM token limit.
        # Fall back to a fresh conversation with the step context in the prompt.
        logger.warning(
            "Onboard step %d failed on conversation %s, starting fresh conversation",
            current_step + 1, conversation_id,
        )
        fallback_prompt = (
            f"[ONBOARD MODE] Generate step {current_step + 1} of a codebase learning path. "
            f"The previous {current_step} steps already covered the basics. "
            f"Now explain the next most important concept, decision, or module "
            f"that hasn't been covered yet. Include key files, rationale, and sources. "
            f"Keep your response concise."
        )
        try:
            result = await ab.converse(message=fallback_prompt)
        except Exception as e:
            logger.error("Onboard fallback also failed: %s", e, exc_info=True)
            raise HTTPException(status_code=502, detail=f"Agent Builder error: {str(e)}")

    response_data = result.get("response", {})
    content = response_data.get("message", "") if isinstance(response_data, dict) else ""

    return {
        "step": current_step + 1,
        "content": content,
        "conversation_id": result.get("conversation_id"),
    }
