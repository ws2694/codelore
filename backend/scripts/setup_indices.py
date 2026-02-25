"""Create all 5 CodeLore Elasticsearch indices with proper mappings."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.elasticsearch_client import get_es_client

# Shared embedding field config: int8_hnsw quantization for ~4x memory savings
_EMBEDDING_FIELD = {
    "type": "dense_vector",
    "dims": 384,
    "index": True,
    "similarity": "cosine",
    "index_options": {"type": "int8_hnsw"},
}

INDICES = {
    "codelore-commits": {
        "mappings": {
            "_source": {"excludes": ["embedding"]},
            "properties": {
                "sha": {"type": "keyword"},
                "message": {"type": "text", "analyzer": "standard"},
                "author": {"type": "keyword"},
                "author_email": {"type": "keyword"},
                "date": {"type": "date"},
                "files_changed": {"type": "keyword"},
                "additions": {"type": "integer"},
                "deletions": {"type": "integer"},
                "diff_summary": {"type": "text"},
                "why_summary": {"type": "text"},
                "repo": {"type": "keyword"},
                "branch": {"type": "keyword"},
                "pr_number": {"type": "integer"},
                "impact_score": {"type": "float"},
                "embedding": _EMBEDDING_FIELD,
            },
        },
    },
    "codelore-pr-events": {
        "mappings": {
            "_source": {"excludes": ["embedding"]},
            "properties": {
                "pr_number": {"type": "integer"},
                "title": {"type": "text"},
                "body": {"type": "text"},
                "author": {"type": "keyword"},
                "state": {"type": "keyword"},
                "created_at": {"type": "date"},
                "merged_at": {"type": "date"},
                "closed_at": {"type": "date"},
                "event_type": {"type": "keyword"},
                "comment_body": {"type": "text"},
                "comment_author": {"type": "keyword"},
                "comment_date": {"type": "date"},
                "review_state": {"type": "keyword"},
                "files_changed": {"type": "keyword"},
                "labels": {"type": "keyword"},
                "linked_issues": {"type": "keyword"},
                "repo": {"type": "keyword"},
                "decision_extracted": {"type": "text"},
                "decision_confidence": {"type": "float"},
                "embedding": _EMBEDDING_FIELD,
            },
        },
    },
    "codelore-docs": {
        "mappings": {
            "_source": {"excludes": ["embedding"]},
            "properties": {
                "doc_id": {"type": "keyword"},
                "path": {"type": "keyword"},
                "filename": {"type": "keyword"},
                "doc_type": {"type": "keyword"},
                "title": {"type": "text"},
                "content": {"type": "text"},
                "section": {"type": "text"},
                "last_updated": {"type": "date"},
                "last_author": {"type": "keyword"},
                "repo": {"type": "keyword"},
                "version": {"type": "integer"},
                "embedding": _EMBEDDING_FIELD,
            },
        },
    },
    "codelore-slack": {
        "mappings": {
            "_source": {"excludes": ["embedding"]},
            "properties": {
                "thread_id": {"type": "keyword"},
                "channel": {"type": "keyword"},
                "user": {"type": "keyword"},
                "text": {"type": "text"},
                "timestamp": {"type": "date"},
                "thread_summary": {"type": "text"},
                "linked_prs": {"type": "integer"},
                "linked_commits": {"type": "keyword"},
                "linked_files": {"type": "keyword"},
                "repo": {"type": "keyword"},
                "embedding": _EMBEDDING_FIELD,
            },
        },
    },
    "codelore-decisions": {
        "mappings": {
            "_source": {"excludes": ["embedding"]},
            "properties": {
                "decision_id": {"type": "keyword"},
                "title": {"type": "text"},
                "summary": {"type": "text"},
                "rationale": {"type": "text"},
                "alternatives_considered": {"type": "text"},
                "decided_by": {"type": "keyword"},
                "decided_at": {"type": "date"},
                "status": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "affected_files": {"type": "keyword"},
                "affected_modules": {"type": "keyword"},
                "related_commits": {"type": "keyword"},
                "related_prs": {"type": "integer"},
                "source_type": {"type": "keyword"},
                "source_ids": {"type": "keyword"},
                "repo": {"type": "keyword"},
                "importance": {"type": "float"},
                "superseded_by": {"type": "keyword"},
                "embedding": _EMBEDDING_FIELD,
            },
        },
    },
}


def setup_indices(force: bool = False):
    es = get_es_client()

    print(f"Connected to Elasticsearch: {es.info()['version']['number']}")

    for index_name, index_body in INDICES.items():
        if es.indices.exists(index=index_name):
            if force:
                print(f"  Deleting existing index: {index_name}")
                es.indices.delete(index=index_name)
            else:
                print(f"  Index {index_name} already exists (use --force to recreate)")
                continue

        es.indices.create(index=index_name, body=index_body)
        print(f"  Created index: {index_name}")

    print("\nAll indices ready:")
    for index_name in INDICES:
        if es.indices.exists(index=index_name):
            count = es.count(index=index_name)["count"]
            print(f"  {index_name}: {count} docs")


def optimize_indices():
    """Post-ingestion optimization: force merge to 1 segment and set refresh interval."""
    es = get_es_client()
    print("Optimizing indices...")

    for index_name in INDICES:
        if not es.indices.exists(index=index_name):
            print(f"  Skipping {index_name} (does not exist)")
            continue

        # Set longer refresh interval for production reads
        es.indices.put_settings(
            index=index_name,
            body={"index": {"refresh_interval": "30s"}},
        )

        # Force merge to 1 segment — maximizes kNN and search performance
        count = es.count(index=index_name)["count"]
        if count > 0:
            print(f"  Force merging {index_name} ({count} docs) to 1 segment...")
            es.indices.forcemerge(
                index=index_name,
                max_num_segments=1,
                wait_for_completion=True,
            )
            print(f"  Done: {index_name}")
        else:
            print(f"  Skipping {index_name} (empty)")

    print("Optimization complete.")


if __name__ == "__main__":
    force = "--force" in sys.argv
    optimize = "--optimize" in sys.argv

    if optimize:
        optimize_indices()
    else:
        setup_indices(force=force)
