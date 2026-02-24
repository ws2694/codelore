"""GitHub API — proxy endpoints for repo browsing using the stored OAuth token."""

import httpx
from fastapi import APIRouter, HTTPException, Query

from backend.services.auth_store import get_auth_state, is_authenticated

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/repos")
async def list_repos(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=30, ge=1, le=100),
    sort: str = Query(default="updated"),
):
    """List the authenticated user's accessible repos."""
    if not is_authenticated():
        raise HTTPException(status_code=401, detail="Not authenticated with GitHub")

    state = get_auth_state()

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/user/repos",
            params={
                "per_page": per_page,
                "page": page,
                "sort": sort,
                "affiliation": "owner,collaborator,organization_member",
            },
            headers={
                "Authorization": f"token {state.github_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=15.0,
        )

    if resp.status_code != 200:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"GitHub API error: {resp.text[:200]}",
        )

    repos = resp.json()

    return {
        "repos": [
            {
                "full_name": r["full_name"],
                "name": r["name"],
                "owner": r["owner"]["login"],
                "description": r.get("description") or "",
                "language": r.get("language") or "",
                "stars": r.get("stargazers_count", 0),
                "updated_at": r.get("updated_at"),
                "private": r.get("private", False),
            }
            for r in repos
        ],
        "page": page,
        "per_page": per_page,
    }
