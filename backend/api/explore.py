"""Explore API — timeline, decision, semantic, expert, and impact queries."""

from fastapi import APIRouter, Query

from backend.services.elasticsearch_client import get_es_client
from backend.services.embedding_service import embed_text
from backend.models.schemas import SemanticSearchRequest, TimelineEntry

router = APIRouter(prefix="/explore", tags=["explore"])


# ── Helpers ──────────────────────────────────────────────────────────────


def _extract_title(index: str, src: dict) -> str:
    if "commits" in index:
        return src.get("why_summary", src.get("message", "")[:100])
    if "pr-events" in index:
        return src.get("title", "")
    if "docs" in index:
        return src.get("title", src.get("filename", ""))
    if "slack" in index:
        return src.get("thread_summary", src.get("text", "")[:100])
    if "decisions" in index:
        return src.get("title", "")
    return ""


def _extract_summary(index: str, src: dict) -> str:
    if "commits" in index:
        return src.get("message", "")[:200]
    if "pr-events" in index:
        return (src.get("comment_body") or src.get("body", ""))[:200]
    if "docs" in index:
        return src.get("content", "")[:200]
    if "slack" in index:
        return src.get("text", "")[:200]
    if "decisions" in index:
        return src.get("summary", "")[:200]
    return ""


def _extract_author(index: str, src: dict) -> str:
    if "commits" in index:
        return src.get("author", "unknown")
    if "pr-events" in index:
        return src.get("comment_author", src.get("author", "unknown"))
    if "docs" in index:
        return src.get("last_author", "unknown")
    if "slack" in index:
        return src.get("user", "unknown")
    if "decisions" in index:
        return src.get("decided_by", "unknown")
    return "unknown"


def _extract_date(index: str, src: dict) -> str:
    if "commits" in index:
        return src.get("date", "")
    if "pr-events" in index:
        return src.get("created_at", src.get("comment_date", ""))
    if "docs" in index:
        return src.get("last_updated", "")
    if "slack" in index:
        return src.get("timestamp", "")
    if "decisions" in index:
        return src.get("decided_at", "")
    return ""


def _pick_on_call(experts: list[dict]) -> dict | None:
    """Pick the best person to contact: recent activity + high commit count."""
    if not experts:
        return None
    max_commits = max(e["commits"] for e in experts) or 1
    max_recent = max(e.get("recent_commits", 0) for e in experts) or 1
    scored = []
    for e in experts:
        score = (
            0.4 * (e["commits"] / max_commits)
            + 0.6 * (e.get("recent_commits", 0) / max_recent)
        )
        scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def _calculate_risk(bus_factor: int, total_commits: int, co_change_count: int) -> dict:
    """Compute a risk assessment for a file."""
    risk_score = 0
    factors = []

    if bus_factor <= 1:
        risk_score += 3
        factors.append("Single contributor — high bus factor risk")
    elif bus_factor == 2:
        risk_score += 1
        factors.append("Only 2 contributors — moderate bus factor risk")

    if total_commits > 50:
        risk_score += 2
        factors.append(f"High churn ({total_commits} commits)")
    elif total_commits > 20:
        risk_score += 1
        factors.append(f"Moderate churn ({total_commits} commits)")

    if co_change_count > 8:
        risk_score += 2
        factors.append(f"Highly coupled — co-changes with {co_change_count} other files")
    elif co_change_count > 4:
        risk_score += 1
        factors.append(f"Moderately coupled — co-changes with {co_change_count} other files")

    level = "low" if risk_score <= 1 else "medium" if risk_score <= 3 else "high"
    return {"level": level, "score": risk_score, "factors": factors}


# ── Endpoints ────────────────────────────────────────────────────────────


@router.get("/timeline/{filepath:path}")
async def get_file_timeline(filepath: str):
    """Get chronological history of a file across commits and PR events."""
    es = get_es_client()
    entries = []

    # Search commits that touched this file
    commits_result = es.search(
        index="codelore-commits",
        body={
            "query": {
                "bool": {
                    "should": [
                        {"wildcard": {"files_changed": f"*{filepath}*"}},
                        {"match": {"files_changed": filepath}},
                    ]
                }
            },
            "sort": [{"date": {"order": "desc"}}],
            "size": 50,
        },
    )

    for hit in commits_result["hits"]["hits"]:
        src = hit["_source"]
        entries.append({
            "date": src.get("date", ""),
            "sha": src.get("sha", ""),
            "title": src.get("why_summary", src.get("message", "")[:100]),
            "author": src.get("author", "unknown"),
            "event_type": "commit",
            "body": src.get("message", ""),
            "files": src.get("files_changed", []),
            "pr_number": src.get("pr_number"),
        })

    # Search PR events mentioning this file
    pr_result = es.search(
        index="codelore-pr-events",
        body={
            "query": {
                "bool": {
                    "should": [
                        {"wildcard": {"files_changed": f"*{filepath}*"}},
                        {"match": {"body": filepath}},
                        {"match": {"comment_body": filepath}},
                    ]
                }
            },
            "sort": [{"created_at": {"order": "desc"}}],
            "size": 30,
        },
    )

    for hit in pr_result["hits"]["hits"]:
        src = hit["_source"]
        entries.append({
            "date": src.get("created_at", src.get("comment_date", "")),
            "pr_number": src.get("pr_number"),
            "title": src.get("title", ""),
            "author": src.get("comment_author", src.get("author", "unknown")),
            "event_type": src.get("event_type", "pr_event"),
            "body": src.get("comment_body", src.get("body", "")),
            "files": src.get("files_changed", []),
        })

    # Search decisions affecting this file
    decisions_result = es.search(
        index="codelore-decisions",
        body={
            "query": {
                "bool": {
                    "should": [
                        {"wildcard": {"affected_files": f"*{filepath}*"}},
                        {"match": {"affected_files": filepath}},
                    ]
                }
            },
            "sort": [{"decided_at": {"order": "desc"}}],
            "size": 10,
        },
    )

    for hit in decisions_result["hits"]["hits"]:
        src = hit["_source"]
        entries.append({
            "date": src.get("decided_at", ""),
            "title": f"Decision: {src.get('title', '')}",
            "author": src.get("decided_by", "unknown"),
            "event_type": "decision",
            "body": src.get("summary", ""),
            "files": src.get("affected_files", []),
        })

    # Sort all entries by date descending
    entries.sort(key=lambda e: e.get("date", ""), reverse=True)

    return {"filepath": filepath, "entries": entries, "total": len(entries)}


@router.get("/decisions")
async def get_decisions(
    query: str = Query(default=None, description="Optional search filter"),
    limit: int = Query(default=20, le=100),
):
    """Get synthesized decisions, optionally filtered by query."""
    es = get_es_client()

    if query:
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "summary^2", "rationale", "tags"],
                }
            },
            "sort": [{"importance": {"order": "desc"}}],
            "size": limit,
        }
    else:
        body = {
            "query": {"match_all": {}},
            "sort": [{"importance": {"order": "desc"}}],
            "size": limit,
        }

    result = es.search(index="codelore-decisions", body=body)
    decisions = []
    for hit in result["hits"]["hits"]:
        src = hit["_source"]
        src.pop("embedding", None)
        decisions.append(src)

    return {"decisions": decisions, "total": result["hits"]["total"]["value"]}


@router.post("/semantic-search")
async def semantic_search(req: SemanticSearchRequest):
    """Search across all indices using kNN vector similarity."""
    es = get_es_client()
    query_vector = embed_text(req.query)

    target_indices = req.indices or [
        "codelore-commits",
        "codelore-pr-events",
        "codelore-docs",
        "codelore-decisions",
    ]

    results = []
    for index in target_indices:
        try:
            resp = es.search(
                index=index,
                body={
                    "knn": {
                        "field": "embedding",
                        "query_vector": query_vector,
                        "k": min(req.limit, 10),
                        "num_candidates": 100,
                    },
                    "size": min(req.limit, 10),
                    "_source": {"excludes": ["embedding"]},
                },
            )
            for hit in resp["hits"]["hits"]:
                src = hit["_source"]
                results.append({
                    "index": index.replace("codelore-", ""),
                    "score": round(hit["_score"], 4),
                    "title": _extract_title(index, src),
                    "summary": _extract_summary(index, src),
                    "author": _extract_author(index, src),
                    "date": _extract_date(index, src),
                    "metadata": src,
                })
        except Exception:
            continue

    results.sort(key=lambda r: r["score"], reverse=True)
    return {"query": req.query, "results": results[: req.limit]}


@router.get("/experts/{module}")
async def get_module_experts(module: str, limit: int = 5):
    """Find the top contributors for a given module/file path."""
    es = get_es_client()

    result = es.search(
        index="codelore-commits",
        body={
            "query": {
                "wildcard": {"files_changed": f"*{module}*"}
            },
            "aggs": {
                "top_authors": {
                    "terms": {"field": "author", "size": limit},
                    "aggs": {
                        "last_active": {"max": {"field": "date"}},
                        "first_commit": {"min": {"field": "date"}},
                        "recent_commits": {
                            "filter": {
                                "range": {"date": {"gte": "now-90d"}}
                            }
                        },
                    },
                },
                "total_commits": {"value_count": {"field": "sha"}},
                "unique_authors": {"cardinality": {"field": "author"}},
            },
            "size": 0,
        },
    )

    aggs = result["aggregations"]
    experts = []
    for bucket in aggs["top_authors"]["buckets"]:
        experts.append({
            "author": bucket["key"],
            "commits": bucket["doc_count"],
            "last_active": bucket["last_active"]["value_as_string"],
            "first_commit": bucket["first_commit"]["value_as_string"],
            "recent_commits": bucket["recent_commits"]["doc_count"],
        })

    on_call = _pick_on_call(experts) if experts else None

    return {
        "module": module,
        "experts": experts,
        "on_call": on_call,
        "bus_factor": aggs["unique_authors"]["value"],
        "total_commits": aggs["total_commits"]["value"],
    }


@router.get("/impact/{filepath:path}")
async def get_file_impact(filepath: str, limit: int = 10):
    """Analyze change impact, co-change patterns, and risk for a file."""
    es = get_es_client()

    result = es.search(
        index="codelore-commits",
        body={
            "query": {
                "bool": {
                    "should": [
                        {"wildcard": {"files_changed": f"*{filepath}*"}},
                        {"term": {"files_changed": filepath}},
                    ]
                }
            },
            "aggs": {
                "unique_authors": {"cardinality": {"field": "author"}},
                "top_authors": {
                    "terms": {"field": "author", "size": 5},
                    "aggs": {
                        "last_active": {"max": {"field": "date"}},
                        "recent_commits": {
                            "filter": {"range": {"date": {"gte": "now-90d"}}}
                        },
                    },
                },
                "change_frequency": {
                    "date_histogram": {
                        "field": "date",
                        "calendar_interval": "month",
                    }
                },
                "latest_change": {"max": {"field": "date"}},
                "co_changed_files": {
                    "terms": {
                        "field": "files_changed",
                        "size": limit + 10,
                    }
                },
            },
            "size": 0,
        },
    )

    aggs = result["aggregations"]
    total_commits = result["hits"]["total"]["value"]

    # Build co-change list, filtering out the queried file
    co_changes = []
    for bucket in aggs["co_changed_files"]["buckets"]:
        fp = bucket["key"]
        if fp == filepath or filepath in fp or fp in filepath:
            continue
        co_changes.append({
            "path": fp,
            "shared_commits": bucket["doc_count"],
            "coupling_ratio": round(bucket["doc_count"] / max(total_commits, 1), 2),
        })
    co_changes = co_changes[:limit]

    # Build experts list
    experts = []
    for bucket in aggs["top_authors"]["buckets"]:
        experts.append({
            "author": bucket["key"],
            "commits": bucket["doc_count"],
            "last_active": bucket["last_active"]["value_as_string"],
            "recent_commits": bucket["recent_commits"]["doc_count"],
        })

    on_call = _pick_on_call(experts) if experts else None

    change_frequency = [
        {"month": bucket["key_as_string"], "count": bucket["doc_count"]}
        for bucket in aggs["change_frequency"]["buckets"]
        if bucket["doc_count"] > 0
    ]

    bus_factor = aggs["unique_authors"]["value"]
    latest_val = aggs["latest_change"]["value"]
    latest_change = aggs["latest_change"].get("value_as_string") if latest_val else None

    risk_level = _calculate_risk(
        bus_factor=bus_factor,
        total_commits=total_commits,
        co_change_count=len(co_changes),
    )

    return {
        "filepath": filepath,
        "total_commits": total_commits,
        "bus_factor": bus_factor,
        "latest_change": latest_change,
        "risk_level": risk_level,
        "change_frequency": change_frequency,
        "co_changes": co_changes,
        "experts": experts,
        "on_call": on_call,
    }


@router.get("/popular-files")
async def get_popular_files(limit: int = Query(default=8, le=30)):
    """Get the most frequently changed files across all commits."""
    es = get_es_client()

    result = es.search(
        index="codelore-commits",
        body={
            "query": {"match_all": {}},
            "aggs": {
                "top_files": {
                    "terms": {"field": "files_changed", "size": limit * 3},
                }
            },
            "size": 0,
        },
    )

    files = []
    for bucket in result["aggregations"]["top_files"]["buckets"]:
        filepath = bucket["key"]
        # Skip lockfiles and generated files
        if any(skip in filepath.lower() for skip in [
            "package-lock", "yarn.lock", ".lock", ".min.", ".map",
        ]):
            continue
        files.append({
            "path": filepath,
            "commits": bucket["doc_count"],
        })
        if len(files) >= limit:
            break

    return {"files": files}
