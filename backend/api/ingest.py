"""Ingest API — trigger data ingestion from GitHub."""

import logging

from fastapi import APIRouter, HTTPException, BackgroundTasks

from backend.config import get_settings
from backend.services.github_ingester import GitHubIngester, delete_repo_data
from backend.services.auth_store import get_auth_state, is_authenticated
from backend.scripts.setup_indices import optimize_indices
from backend.services import cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])

_ingest_status = {"running": False, "last_stats": None}


@router.post("/repo")
async def trigger_ingestion(
    background_tasks: BackgroundTasks,
    repo: str | None = None,
):
    """Trigger full GitHub repo ingestion (runs in background)."""
    if _ingest_status["running"]:
        raise HTTPException(status_code=409, detail="Ingestion already in progress")

    settings = get_settings()
    auth = get_auth_state()

    target_repo = repo or auth.selected_repo or settings.github_repo
    token = auth.github_token if is_authenticated() else settings.github_token

    if not target_repo:
        raise HTTPException(
            status_code=400,
            detail="No repo specified. Sign in with GitHub and select a repo, or set GITHUB_REPO in .env",
        )

    if not token:
        raise HTTPException(
            status_code=401,
            detail="No GitHub token available. Sign in with GitHub or set GITHUB_TOKEN in .env",
        )

    async def run_ingestion():
        _ingest_status["running"] = True
        try:
            ingester = GitHubIngester(token=token, repo=target_repo)
            stats = await ingester.ingest_all()
            _ingest_status["last_stats"] = stats
            # Invalidate explore cache — data has changed
            cache.invalidate_all()
            # Post-ingestion: force merge to 1 segment for faster kNN + search
            try:
                optimize_indices()
            except Exception as e:
                logger.warning("Post-ingestion optimization failed (non-fatal): %s", e)
        finally:
            _ingest_status["running"] = False

    background_tasks.add_task(run_ingestion)

    return {
        "status": "started",
        "repo": target_repo,
        "message": "Ingestion started in background. Check /api/ingest/status for progress.",
    }


@router.get("/status")
async def get_ingest_status():
    """Check the status of the current or last ingestion."""
    return {
        "running": _ingest_status["running"],
        "last_stats": _ingest_status["last_stats"],
    }


@router.delete("/repo")
async def delete_repo(repo: str):
    """Delete all indexed data for a specific repo."""
    if not repo:
        raise HTTPException(status_code=400, detail="repo parameter is required")
    deleted = delete_repo_data(repo)
    cache.invalidate_all()
    total = sum(deleted.values())
    return {
        "status": "deleted",
        "repo": repo,
        "deleted_total": total,
        "deleted_per_index": deleted,
    }
