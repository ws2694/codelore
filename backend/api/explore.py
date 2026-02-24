"""Explore API — timeline and decision queries directly against Elasticsearch."""

from fastapi import APIRouter, Query

from backend.services.elasticsearch_client import get_es_client
from backend.models.schemas import TimelineEntry

router = APIRouter(prefix="/explore", tags=["explore"])


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
                    },
                }
            },
            "size": 0,
        },
    )

    experts = []
    for bucket in result["aggregations"]["top_authors"]["buckets"]:
        experts.append({
            "author": bucket["key"],
            "commits": bucket["doc_count"],
            "last_active": bucket["last_active"]["value_as_string"],
        })

    return {"module": module, "experts": experts}


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
