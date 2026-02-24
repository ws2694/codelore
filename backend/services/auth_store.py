"""In-memory auth state for single-user local tool."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AuthState:
    github_token: str = ""
    github_user: str = ""
    github_avatar_url: str = ""
    selected_repo: str = ""
    authenticated_at: str = ""
    scopes: list[str] = field(default_factory=list)


_state = AuthState()


def get_auth_state() -> AuthState:
    return _state


def set_auth(token: str, user: str, avatar_url: str, scopes: list[str]) -> None:
    _state.github_token = token
    _state.github_user = user
    _state.github_avatar_url = avatar_url
    _state.scopes = scopes
    _state.authenticated_at = datetime.utcnow().isoformat()


def set_selected_repo(repo: str) -> None:
    _state.selected_repo = repo


def clear_auth() -> None:
    global _state
    _state = AuthState()


def is_authenticated() -> bool:
    return bool(_state.github_token)
