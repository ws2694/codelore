"""Ingest API — trigger data ingestion from GitHub."""

from fastapi import APIRouter, HTTPException, BackgroundTasks

from backend.config import get_settings
from backend.services.github_ingester import GitHubIngester

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
    target_repo = repo or settings.github_repo

    if not target_repo:
        raise HTTPException(
            status_code=400,
            detail="No repo specified. Pass 'repo' param or set GITHUB_REPO in .env",
        )

    async def run_ingestion():
        _ingest_status["running"] = True
        try:
            ingester = GitHubIngester(repo=target_repo)
            stats = await ingester.ingest_all()
            _ingest_status["last_stats"] = stats
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
