"""Auth API — GitHub OAuth flow and session management."""

from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Query

from backend.config import get_settings
from backend.services.auth_store import (
    get_auth_state,
    set_auth,
    set_selected_repo,
    clear_auth,
    is_authenticated,
)

router = APIRouter(prefix="/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/github/url")
async def get_github_auth_url():
    """Return the GitHub OAuth authorization URL for the frontend to redirect to."""
    settings = get_settings()
    if not settings.github_client_id:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_CLIENT_ID not configured. Add it to .env",
        )

    params = urlencode({
        "client_id": settings.github_client_id,
        "scope": "repo read:user",
        "redirect_uri": "http://localhost:3000/auth/callback",
    })
    return {"url": f"{GITHUB_AUTHORIZE_URL}?{params}"}


@router.get("/github/callback")
async def github_callback(code: str = Query(...)):
    """Exchange the OAuth code for an access token and fetch user info."""
    settings = get_settings()

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )

    if token_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to exchange code with GitHub")

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        error = token_data.get("error_description", "Unknown error")
        raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {error}")

    scopes = token_data.get("scope", "").split(",")

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )

    if user_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch GitHub user info")

    user_data = user_resp.json()

    set_auth(
        token=access_token,
        user=user_data.get("login", ""),
        avatar_url=user_data.get("avatar_url", ""),
        scopes=scopes,
    )

    return {
        "authenticated": True,
        "user": user_data.get("login"),
        "avatar_url": user_data.get("avatar_url"),
        "name": user_data.get("name"),
    }


@router.get("/status")
async def auth_status():
    """Return current auth state — works with both OAuth and .env tokens."""
    state = get_auth_state()
    settings = get_settings()

    has_oauth = is_authenticated()
    has_env_token = bool(settings.github_token)

    return {
        "authenticated": has_oauth or has_env_token,
        "method": "oauth" if has_oauth else ("env" if has_env_token else None),
        "user": state.github_user if has_oauth else None,
        "avatar_url": state.github_avatar_url if has_oauth else None,
        "selected_repo": state.selected_repo or settings.github_repo or None,
        "oauth_configured": bool(settings.github_client_id),
    }


@router.post("/logout")
async def logout():
    """Clear the stored OAuth token and session."""
    clear_auth()
    return {"authenticated": False}


@router.post("/select-repo")
async def select_repo(repo: str = Query(...)):
    """Set the active repository for the session."""
    if not is_authenticated():
        settings = get_settings()
        if not settings.github_token:
            raise HTTPException(status_code=401, detail="Not authenticated")
    set_selected_repo(repo)
    return {"selected_repo": repo}
