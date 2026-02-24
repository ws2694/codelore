"""Seed all 5 CodeLore indices with realistic synthetic data for demo purposes."""

import sys
import os
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from elasticsearch.helpers import bulk
from backend.services.elasticsearch_client import get_es_client
from backend.services.embedding_service import embed_text

REPO = "acme/webapp"
AUTHORS = ["sarah", "mike", "alex", "jordan", "priya"]
MODULES = ["auth", "payments", "notifications", "api", "database"]

BASE_DATE = datetime(2024, 1, 15)


def ts(days_offset: int) -> str:
    return (BASE_DATE + timedelta(days=days_offset)).isoformat() + "Z"


COMMITS = [
    {"sha": "a1b2c3d4e5f6", "msg": "Initial JWT authentication implementation", "author": "sarah", "day": 0, "files": ["src/auth/jwt.ts", "src/auth/middleware.ts", "src/auth/types.ts"], "adds": 342, "dels": 0},
    {"sha": "b2c3d4e5f6a7", "msg": "Add refresh token rotation for security", "author": "sarah", "day": 5, "files": ["src/auth/refresh.ts", "src/auth/jwt.ts"], "adds": 156, "dels": 23},
    {"sha": "c3d4e5f6a7b8", "msg": "Migrate session storage from Postgres to Redis\n\nPostgres p99 latency was 45ms for session lookups.\nRedis brings this down to ~3ms. See ADR-012.", "author": "sarah", "day": 15, "files": ["src/auth/session.ts", "src/config/redis.ts", "docker-compose.yml"], "adds": 234, "dels": 89},
    {"sha": "d4e5f6a7b8c9", "msg": "Implement Stripe payment integration", "author": "mike", "day": 20, "files": ["src/payments/stripe.ts", "src/payments/types.ts", "src/payments/webhook.ts"], "adds": 567, "dels": 0},
    {"sha": "e5f6a7b8c9d0", "msg": "Add idempotent webhook processing\n\nAfter production incident where failed webhooks caused duplicate charges.\nNow using idempotency keys stored in Redis.", "author": "mike", "day": 35, "files": ["src/payments/webhook.ts", "src/payments/idempotency.ts"], "adds": 189, "dels": 45},
    {"sha": "f6a7b8c9d0e1", "msg": "Set webhook retry count to 5 with exponential backoff\n\nStripe uses 5 retries. Mike's analysis: 99.7% of transient failures resolve within 4 retries.", "author": "mike", "day": 38, "files": ["src/payments/webhook.ts", "src/config/constants.ts"], "adds": 34, "dels": 12},
    {"sha": "a7b8c9d0e1f2", "msg": "Add email notification service using SendGrid", "author": "alex", "day": 25, "files": ["src/notifications/email.ts", "src/notifications/templates/"], "adds": 278, "dels": 0},
    {"sha": "b8c9d0e1f2a3", "msg": "Implement rate limiting middleware\n\nUsing sliding window algorithm with Redis backend.\nLimits: 100 req/min for authenticated, 20/min for anonymous.", "author": "jordan", "day": 45, "files": ["src/api/middleware/rateLimit.ts", "src/api/middleware/index.ts"], "adds": 145, "dels": 8},
    {"sha": "c9d0e1f2a3b4", "msg": "Migrate from REST to GraphQL for user service\n\nMobile app needs flexible data fetching. REST was causing\nover-fetching on slow connections. See PR #42.", "author": "priya", "day": 55, "files": ["src/api/graphql/schema.ts", "src/api/graphql/resolvers/user.ts", "src/api/graphql/types.ts"], "adds": 456, "dels": 234},
    {"sha": "d0e1f2a3b4c5", "msg": "Add database connection pooling with pgbouncer", "author": "jordan", "day": 60, "files": ["src/database/pool.ts", "docker-compose.yml", "src/config/database.ts"], "adds": 89, "dels": 34},
    {"sha": "e1f2a3b4c5d6", "msg": "Implement OAuth2 social login (Google, GitHub)", "author": "sarah", "day": 70, "files": ["src/auth/oauth.ts", "src/auth/providers/google.ts", "src/auth/providers/github.ts"], "adds": 312, "dels": 0},
    {"sha": "f2a3b4c5d6e7", "msg": "Add PCI compliance: tokenize all card data", "author": "mike", "day": 80, "files": ["src/payments/tokenization.ts", "src/payments/stripe.ts", "src/payments/types.ts"], "adds": 198, "dels": 67},
    {"sha": "a3b4c5d6e7f8", "msg": "Build subscription billing with custom proration\n\nStripe Billing didn't support our proration model.\nBuilt in-house to handle mid-cycle plan changes.", "author": "mike", "day": 90, "files": ["src/payments/subscription.ts", "src/payments/proration.ts"], "adds": 543, "dels": 0},
    {"sha": "b4c5d6e7f8a9", "msg": "Add real-time notification via WebSocket\n\nChose WebSocket over SSE because we need bidirectional\ncommunication for typing indicators.", "author": "alex", "day": 95, "files": ["src/notifications/ws.ts", "src/notifications/channels.ts"], "adds": 267, "dels": 45},
    {"sha": "c5d6e7f8a901", "msg": "Deprecate GraphQL subscriptions in favor of WS\n\nGraphQL subscriptions had memory leaks under load.\nDirect WebSocket is more predictable.", "author": "priya", "day": 100, "files": ["src/api/graphql/schema.ts", "src/notifications/ws.ts"], "adds": 23, "dels": 156},
]

PR_EVENTS = [
    # PR #12: JWT Auth
    {"pr": 12, "title": "Implement JWT authentication", "body": "This PR introduces JWT-based authentication replacing the previous cookie-based sessions.\n\n## Changes\n- JWT token generation and validation\n- Middleware for protected routes\n- Refresh token rotation\n\n## Why\nWe need stateless auth for the new microservices architecture. Sessions don't scale across services without sticky routing.", "author": "sarah", "day": 0, "type": "pr_opened", "labels": ["auth", "breaking-change"]},
    {"pr": 12, "title": "Implement JWT authentication", "body": "Great implementation. One concern: have we considered token revocation? If a token is compromised, how do we invalidate it before expiry?", "author": "jordan", "day": 1, "type": "review_comment", "review_state": "changes_requested"},
    {"pr": 12, "title": "Implement JWT authentication", "body": "Good point @jordan. Added a token blacklist in Redis with TTL matching the JWT expiry. This gives us revocation without losing statelessness for the happy path.", "author": "sarah", "day": 2, "type": "review_comment"},

    # PR #28: Redis Sessions
    {"pr": 28, "title": "Migrate session storage to Redis", "body": "## Problem\nPostgres session lookups have p99 of 45ms, which is unacceptable for the auth middleware that runs on every request.\n\n## Solution\nMigrate to Redis. Benchmarks show p99 of 3ms.\n\n## Alternatives Considered\n- **Memcached**: Faster but no persistence. We need session persistence for graceful restarts.\n- **In-memory cache**: Not viable for multi-instance deployment.\n\nSee ADR-012 for the full analysis.", "author": "sarah", "day": 15, "type": "pr_opened", "labels": ["performance", "auth"]},
    {"pr": 28, "title": "Migrate session storage to Redis", "body": "Impressive benchmarks. Are we handling Redis connection failures gracefully? We shouldn't let a Redis outage take down auth entirely.", "author": "priya", "day": 16, "type": "review_comment", "review_state": "approved"},

    # PR #42: GraphQL Migration
    {"pr": 42, "title": "Migrate user API from REST to GraphQL", "body": "## Motivation\nThe mobile app is experiencing significant over-fetching. The user profile endpoint returns 47 fields but mobile only needs 8 on the main screen.\n\n## Approach\n- Apollo Server with TypeScript code-first schema\n- Dataloader for N+1 prevention\n- Keep REST endpoints active during migration (6-month deprecation)\n\n## Performance\n- Payload size: 12KB -> 2.8KB for mobile profile view\n- Latency: similar (graphql adds ~5ms overhead but saves on transfer)", "author": "priya", "day": 55, "type": "pr_opened", "labels": ["api", "mobile"]},
    {"pr": 42, "title": "Migrate user API from REST to GraphQL", "body": "Concern: GraphQL subscriptions for real-time features. The spec is still evolving and I've seen memory leaks in production with Apollo Subscriptions. Can we defer subscriptions to a separate WebSocket layer?", "author": "alex", "day": 56, "type": "review_comment"},
    {"pr": 42, "title": "Migrate user API from REST to GraphQL", "body": "Agreed @alex. Let's implement queries and mutations only for now. Real-time will go through the dedicated WebSocket service you're building.", "author": "priya", "day": 56, "type": "review_comment"},

    # PR #67: Webhook Retry
    {"pr": 67, "title": "Add idempotent webhook processing with retry logic", "body": "## Incident Response\nOn 2024-02-20, a Stripe webhook delivery failure caused 3 duplicate charges totaling $847. Root cause: our webhook handler wasn't idempotent.\n\n## Fix\n- Idempotency keys stored in Redis (24h TTL)\n- Exponential backoff: 5 retries at 1s, 2s, 4s, 8s, 16s\n- Dead letter queue for permanently failed webhooks\n\n## Why 5 retries?\nStripe's own retry policy uses 5 attempts. @mike's analysis of our logs shows 99.7% of transient failures (network timeouts, 503s) resolve within 4 retries.", "author": "mike", "day": 35, "type": "pr_opened", "labels": ["payments", "incident-response", "critical"]},
    {"pr": 67, "title": "Add idempotent webhook processing with retry logic", "body": "Solid incident response. The dead letter queue is a great addition. Should we add alerting when messages hit the DLQ?", "author": "sarah", "day": 36, "type": "review_comment", "review_state": "approved"},

    # PR #89: Rate Limiting
    {"pr": 89, "title": "Implement sliding window rate limiting", "body": "## Why\nBots are hammering our public endpoints. Need rate limiting before we launch the public API.\n\n## Design\n- Sliding window (not fixed window) to prevent burst at window boundaries\n- Redis-backed for multi-instance consistency\n- Configurable per-route limits\n- Default: 100/min authenticated, 20/min anonymous\n\n## Alternatives\n- Token bucket: More complex, similar result for our use case\n- Leaky bucket: Doesn't handle burst well\n- Third-party (Cloudflare): Added latency, less control", "author": "jordan", "day": 45, "type": "pr_opened", "labels": ["api", "security"]},
]

DOCS = [
    {"path": "README.md", "title": "ACME WebApp", "type": "readme", "content": "# ACME WebApp\n\nA modern web application built with TypeScript, Node.js, and React.\n\n## Architecture\n\nThe application follows a microservices-inspired monolith pattern:\n- **Auth Service**: JWT-based authentication with Redis session storage\n- **Payment Service**: Stripe integration with idempotent webhook processing\n- **Notification Service**: Email (SendGrid) + real-time (WebSocket)\n- **API Layer**: GraphQL for client-facing, REST for internal services\n\n## Getting Started\n\n```bash\nnpm install\ndocker-compose up -d  # Redis, Postgres, pgbouncer\nnpm run dev\n```\n\n## Key Design Decisions\n\nSee the `/docs/adr/` directory for Architecture Decision Records."},
    {"path": "docs/adr/ADR-009-jwt-auth.md", "title": "ADR-009: JWT Authentication", "type": "adr", "content": "# ADR-009: Use JWT for Authentication\n\n## Status\nAccepted (2024-01-15)\n\n## Context\nMoving to a microservices-inspired architecture requires stateless authentication. Cookie-based sessions require sticky routing or shared session stores across services.\n\n## Decision\nUse JWT tokens for authentication with:\n- Short-lived access tokens (15 min)\n- Long-lived refresh tokens (7 days) with rotation\n- Token blacklist in Redis for revocation\n\n## Consequences\n- Positive: Stateless, scales horizontally, works for mobile\n- Negative: Token size larger than session cookies, revocation requires Redis lookup\n\n## Alternatives Considered\n- Session cookies with Redis: Works but requires shared Redis for all services\n- OAuth2 tokens via external provider: Too complex for our scale right now"},
    {"path": "docs/adr/ADR-012-redis-sessions.md", "title": "ADR-012: Redis for Session Storage", "type": "adr", "content": "# ADR-012: Migrate Session Storage to Redis\n\n## Status\nAccepted (2024-01-30)\n\n## Context\nPostgres session lookups have p99 latency of 45ms. The auth middleware runs on every request, making this a significant bottleneck.\n\n## Decision\nMigrate session data to Redis.\n\n## Benchmarks\n- Postgres: p50=12ms, p99=45ms\n- Redis: p50=1ms, p99=3ms\n\n## Consequences\n- Positive: 15x latency improvement at p99\n- Negative: Additional infrastructure dependency\n- Mitigation: Redis Sentinel for HA, graceful degradation to Postgres on Redis failure"},
    {"path": "docs/adr/ADR-015-graphql.md", "title": "ADR-015: GraphQL for Client API", "type": "adr", "content": "# ADR-015: Adopt GraphQL for Client-Facing API\n\n## Status\nAccepted (2024-03-10)\n\n## Context\nMobile app over-fetches data significantly. User profile endpoint returns 47 fields, mobile needs 8. This wastes bandwidth on slow connections.\n\n## Decision\nAdopt GraphQL (Apollo Server) for client-facing endpoints. Keep REST for internal service-to-service communication.\n\n## Scope\n- Queries and mutations only (no subscriptions — see ADR-018)\n- 6-month deprecation period for REST endpoints\n- TypeScript code-first schema generation\n\n## Consequences\n- Positive: 76% payload reduction for mobile, flexible data fetching\n- Negative: Learning curve, caching is more complex than REST\n- Risk: N+1 queries — mitigated with DataLoader"},
    {"path": "docs/CONTRIBUTING.md", "title": "Contributing Guide", "type": "readme", "content": "# Contributing to ACME WebApp\n\n## Code Review Process\n\n1. All PRs require at least one approval\n2. Changes to `src/auth/` or `src/payments/` require review from a domain expert\n3. Breaking changes need an ADR in `docs/adr/`\n\n## Architecture Decisions\n\nFor significant changes, create an ADR:\n- Copy `docs/adr/TEMPLATE.md`\n- Follow the format: Context, Decision, Consequences, Alternatives\n- Get team consensus in the PR discussion before merging"},
]

SLACK_THREADS = [
    {"channel": "backend", "summary": "Discussion about Redis vs Memcached for session storage. Sarah presented benchmarks showing Redis p99 at 3ms vs Postgres 45ms. Team agreed Redis was the right choice due to persistence needs.", "day": 14, "linked_prs": [28], "linked_files": ["src/auth/session.ts", "src/config/redis.ts"]},
    {"channel": "incidents", "summary": "Post-mortem for duplicate charge incident on 2024-02-20. Stripe webhook handler wasn't idempotent. 3 customers affected, $847 total. Mike took point on the fix. Action items: add idempotency keys, webhook retry with backoff, DLQ.", "day": 34, "linked_prs": [67], "linked_commits": ["e5f6a7b8c9d0"], "linked_files": ["src/payments/webhook.ts"]},
    {"channel": "frontend", "summary": "Alex raised concerns about GraphQL subscriptions memory leaks. Team decided to handle real-time features through dedicated WebSocket layer instead of GraphQL subscriptions.", "day": 56, "linked_prs": [42], "linked_files": ["src/api/graphql/schema.ts", "src/notifications/ws.ts"]},
    {"channel": "backend", "summary": "Jordan presented rate limiting design options. Sliding window chosen over token bucket for simplicity. Limits set at 100/min authenticated, 20/min anonymous based on current traffic analysis.", "day": 44, "linked_prs": [89], "linked_files": ["src/api/middleware/rateLimit.ts"]},
    {"channel": "backend", "summary": "Priya proposed GraphQL migration for user API. Key benefit: 76% payload reduction for mobile. Team approved queries/mutations only, no subscriptions. 6-month REST deprecation window.", "day": 54, "linked_prs": [42], "linked_files": ["src/api/graphql/schema.ts"]},
]

DECISIONS = [
    {"id": "D-001", "title": "Use JWT for stateless authentication", "summary": "Adopted JWT tokens for authentication to support microservices architecture without shared session state.", "rationale": "Cookie-based sessions require sticky routing or shared stores across services. JWT is stateless and works for mobile.", "alternatives": "Session cookies with shared Redis; OAuth2 via external provider", "by": "sarah", "day": 0, "files": ["src/auth/jwt.ts", "src/auth/middleware.ts"], "modules": ["auth"], "commits": ["a1b2c3d4e5f6", "b2c3d4e5f6a7"], "prs": [12], "tags": ["auth", "architecture"], "importance": 4.5},
    {"id": "D-002", "title": "Migrate session storage from Postgres to Redis", "summary": "Moved session lookups to Redis for 15x latency improvement at p99 (45ms -> 3ms).", "rationale": "Auth middleware runs on every request. Postgres p99 of 45ms was a significant bottleneck. Redis provides sub-5ms lookups.", "alternatives": "Memcached (no persistence); In-memory cache (not viable for multi-instance)", "by": "sarah", "day": 15, "files": ["src/auth/session.ts", "src/config/redis.ts"], "modules": ["auth", "infrastructure"], "commits": ["c3d4e5f6a7b8"], "prs": [28], "tags": ["performance", "auth", "redis"], "importance": 4.0},
    {"id": "D-003", "title": "Choose Stripe for payment processing", "summary": "Selected Stripe over Braintree and Adyen for payment integration.", "rationale": "Best international currency support, excellent developer experience, and comprehensive webhook system.", "alternatives": "Braintree (limited currency support); Adyen (complex integration)", "by": "mike", "day": 20, "files": ["src/payments/stripe.ts", "src/payments/webhook.ts"], "modules": ["payments"], "commits": ["d4e5f6a7b8c9"], "prs": [], "tags": ["payments", "vendor"], "importance": 4.0},
    {"id": "D-004", "title": "Implement idempotent webhook processing with 5 retries", "summary": "After duplicate charge incident, added idempotency keys and exponential backoff retry (5 attempts).", "rationale": "Production incident caused 3 duplicate charges ($847). Stripe uses 5 retries; analysis shows 99.7% of transient failures resolve within 4 retries.", "alternatives": "Fire-and-forget (unsafe); Infinite retry (resource waste)", "by": "mike", "day": 35, "files": ["src/payments/webhook.ts", "src/payments/idempotency.ts"], "modules": ["payments"], "commits": ["e5f6a7b8c9d0", "f6a7b8c9d0e1"], "prs": [67], "tags": ["payments", "reliability", "incident-response"], "importance": 4.8},
    {"id": "D-005", "title": "Adopt GraphQL for client-facing API", "summary": "Migrated from REST to GraphQL for client-facing endpoints to reduce mobile over-fetching (76% payload reduction).", "rationale": "Mobile app fetched 47 fields when only 8 needed. GraphQL allows precise data fetching. REST kept for internal services.", "alternatives": "REST with field selection params; BFF (Backend for Frontend) pattern", "by": "priya", "day": 55, "files": ["src/api/graphql/schema.ts", "src/api/graphql/resolvers/user.ts"], "modules": ["api"], "commits": ["c9d0e1f2a3b4"], "prs": [42], "tags": ["api", "mobile", "graphql"], "importance": 4.2},
    {"id": "D-006", "title": "Use sliding window for rate limiting", "summary": "Implemented sliding window rate limiting over token bucket or leaky bucket algorithms.", "rationale": "Sliding window prevents burst at window boundaries (fixed window problem). Simpler than token bucket with similar results for our traffic patterns.", "alternatives": "Token bucket (more complex); Leaky bucket (poor burst handling); Cloudflare (added latency, less control)", "by": "jordan", "day": 45, "files": ["src/api/middleware/rateLimit.ts"], "modules": ["api", "security"], "commits": ["b8c9d0e1f2a3"], "prs": [89], "tags": ["api", "security", "rate-limiting"], "importance": 3.5},
    {"id": "D-007", "title": "WebSocket over GraphQL Subscriptions for real-time", "summary": "Chose direct WebSocket for real-time features instead of GraphQL subscriptions.", "rationale": "GraphQL subscriptions had memory leaks under load with Apollo Server. Direct WebSocket is more predictable and supports bidirectional communication for typing indicators.", "alternatives": "GraphQL subscriptions (memory leaks); Server-Sent Events (unidirectional only)", "by": "alex", "day": 95, "files": ["src/notifications/ws.ts", "src/notifications/channels.ts"], "modules": ["notifications", "api"], "commits": ["b4c5d6e7f8a9", "c5d6e7f8a901"], "prs": [42], "tags": ["real-time", "websocket", "architecture"], "importance": 3.8},
    {"id": "D-008", "title": "Build subscription billing in-house over Stripe Billing", "summary": "Built custom subscription billing instead of using Stripe Billing due to custom proration requirements.", "rationale": "Stripe Billing doesn't support our mid-cycle plan change proration model. In-house gives full control over proration calculations.", "alternatives": "Stripe Billing (limited proration); Chargebee (additional vendor dependency)", "by": "mike", "day": 90, "files": ["src/payments/subscription.ts", "src/payments/proration.ts"], "modules": ["payments"], "commits": ["a3b4c5d6e7f8"], "prs": [], "tags": ["payments", "billing", "build-vs-buy"], "importance": 4.0},
]


def seed_all():
    es = get_es_client()
    actions = []

    # Seed commits
    for c in COMMITS:
        embed_input = f"{c['msg']}\n{'; '.join(c['files'][:5])}"
        actions.append({
            "_index": "codelore-commits",
            "_id": c["sha"][:12],
            "sha": c["sha"],
            "message": c["msg"],
            "author": c["author"],
            "author_email": f"{c['author']}@acme.com",
            "date": ts(c["day"]),
            "files_changed": c["files"],
            "additions": c["adds"],
            "deletions": c["dels"],
            "diff_summary": f"Changed {len(c['files'])} files: +{c['adds']}-{c['dels']}",
            "why_summary": c["msg"].split("\n")[0],
            "repo": REPO,
            "impact_score": min(len(c["files"]) * 0.3 + (c["adds"] + c["dels"]) * 0.002, 5.0),
            "embedding": embed_text(embed_input),
        })

    # Seed PR events
    for pr in PR_EVENTS:
        text = pr.get("body", "")
        doc_id = f"pr-{pr['pr']}-{pr['type']}-{pr['day']}"
        doc = {
            "_index": "codelore-pr-events",
            "_id": doc_id,
            "pr_number": pr["pr"],
            "title": pr["title"],
            "author": pr["author"],
            "created_at": ts(pr["day"]),
            "event_type": pr["type"],
            "repo": REPO,
            "embedding": embed_text(text[:500]),
        }
        if pr["type"] == "pr_opened":
            doc["body"] = text
            doc["labels"] = pr.get("labels", [])
        else:
            doc["comment_body"] = text
            doc["comment_author"] = pr["author"]
            doc["comment_date"] = ts(pr["day"])
            if "review_state" in pr:
                doc["review_state"] = pr["review_state"]
        actions.append(doc)

    # Seed docs
    for i, d in enumerate(DOCS):
        doc_id = f"doc-{i:03d}"
        actions.append({
            "_index": "codelore-docs",
            "_id": doc_id,
            "doc_id": doc_id,
            "path": d["path"],
            "filename": d["path"].split("/")[-1],
            "doc_type": d["type"],
            "title": d["title"],
            "content": d["content"],
            "section": d["content"][:500],
            "last_author": "sarah",
            "last_updated": ts(90),
            "repo": REPO,
            "embedding": embed_text(f"{d['title']}\n{d['content'][:400]}"),
        })

    # Seed Slack threads
    for i, s in enumerate(SLACK_THREADS):
        thread_id = f"slack-{i:03d}"
        actions.append({
            "_index": "codelore-slack",
            "_id": thread_id,
            "thread_id": thread_id,
            "channel": s["channel"],
            "user": AUTHORS[i % len(AUTHORS)],
            "text": s["summary"],
            "timestamp": ts(s["day"]),
            "thread_summary": s["summary"],
            "linked_prs": s.get("linked_prs", []),
            "linked_commits": s.get("linked_commits", []),
            "linked_files": s.get("linked_files", []),
            "repo": REPO,
            "embedding": embed_text(s["summary"]),
        })

    # Seed decisions
    for d in DECISIONS:
        actions.append({
            "_index": "codelore-decisions",
            "_id": d["id"],
            "decision_id": d["id"],
            "title": d["title"],
            "summary": d["summary"],
            "rationale": d["rationale"],
            "alternatives_considered": d["alternatives"],
            "decided_by": d["by"],
            "decided_at": ts(d["day"]),
            "status": "accepted",
            "tags": d["tags"],
            "affected_files": d["files"],
            "affected_modules": d["modules"],
            "related_commits": d["commits"],
            "related_prs": d["prs"],
            "source_type": "pr",
            "source_ids": [f"pr-{p}" for p in d["prs"]],
            "repo": REPO,
            "importance": d["importance"],
            "embedding": embed_text(f"{d['title']}\n{d['summary']}\n{d['rationale']}"),
        })

    success, errors = bulk(es, actions)
    print(f"Seeded {success} documents across all indices")
    if errors:
        print(f"  Errors: {errors}")

    # Print summary
    for idx in ["codelore-commits", "codelore-pr-events", "codelore-docs", "codelore-slack", "codelore-decisions"]:
        es.indices.refresh(index=idx)
        count = es.count(index=idx)["count"]
        print(f"  {idx}: {count} docs")


if __name__ == "__main__":
    seed_all()
