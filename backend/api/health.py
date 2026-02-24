"""Health API — check connectivity and index status."""

from fastapi import APIRouter

from backend.services.elasticsearch_client import get_es_client
from backend.models.schemas import HealthResponse

router = APIRouter(tags=["health"])

INDEX_NAMES = [
    "codelore-commits",
    "codelore-pr-events",
    "codelore-docs",
    "codelore-slack",
    "codelore-decisions",
]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check Elasticsearch connectivity and index document counts."""
    es = get_es_client()

    try:
        es.info()
        es_healthy = True
    except Exception:
        es_healthy = False

    indices = {}
    if es_healthy:
        for idx in INDEX_NAMES:
            try:
                if es.indices.exists(index=idx):
                    count = es.count(index=idx)["count"]
                    indices[idx] = count
                else:
                    indices[idx] = -1  # Does not exist
            except Exception:
                indices[idx] = -1

    status = "healthy" if es_healthy and all(v >= 0 for v in indices.values()) else "degraded"
    if not es_healthy:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        elasticsearch=es_healthy,
        indices=indices,
    )
