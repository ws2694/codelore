from fastapi import APIRouter

from backend.api.chat import router as chat_router
from backend.api.explore import router as explore_router
from backend.api.onboard import router as onboard_router
from backend.api.ingest import router as ingest_router
from backend.api.health import router as health_router
from backend.api.auth import router as auth_router
from backend.api.github import router as github_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(explore_router)
api_router.include_router(onboard_router)
api_router.include_router(ingest_router)
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(github_router)
