from pydantic import BaseModel
from datetime import datetime


class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    mode: str = "ask"  # ask, onboard, explore


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str | None = None
    sources: list[dict] = []
    confidence: str | None = None


class IngestRequest(BaseModel):
    repo: str | None = None


class IngestStats(BaseModel):
    commits: int = 0
    prs: int = 0
    docs: int = 0
    decisions: int = 0


class TimelineEntry(BaseModel):
    date: str
    sha: str | None = None
    pr_number: int | None = None
    title: str
    author: str
    event_type: str  # commit, pr_opened, review_comment, decision
    body: str | None = None
    files: list[str] = []


class OnboardStep(BaseModel):
    step_number: int
    total_steps: int
    title: str
    content: str
    key_files: list[str] = []
    sources: list[dict] = []


class SemanticSearchRequest(BaseModel):
    query: str
    indices: list[str] | None = None
    limit: int = 20


class HealthResponse(BaseModel):
    status: str
    elasticsearch: bool
    indices: dict[str, int] = {}
