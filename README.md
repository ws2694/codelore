# CodeLore — Codebase Memory Agent

CodeLore is an AI agent that serves as the **institutional memory** of a codebase. It indexes the *why* behind code — not just what changed, but why it was written that way, what alternatives were considered, and what discussions led to each decision.

Built with **Elastic Agent Builder** and **Elasticsearch**, CodeLore ingests git commits, pull request discussions, architecture docs, and team conversations, then makes them searchable through an intelligent agent that reasons across all sources.

## The Problem

Every codebase accumulates institutional knowledge that is scattered and lost:
- **Git logs** have commit messages but not the full rationale
- **PR discussions** contain design debates that disappear after merge
- **Architecture docs** go stale and lose their connection to actual code
- **Slack threads** hold critical context that nobody can find later

New developers spend weeks piecing together *why* code is structured the way it is. Senior engineers repeatedly answer the same questions. CodeLore solves this by making all of that context instantly searchable.

## Architecture

```
┌──────────────┐         ┌─────────────────────────────────────┐
│   Frontend   │         │          Elastic Cloud               │
│  React + TS  │         │                                      │
│              │         │  ┌─────────────────────────────────┐ │
│  ┌────────┐  │  HTTP   │  │     Kibana Agent Builder        │ │
│  │Ask Mode│  │────┐    │  │                                 │ │
│  ├────────┤  │    │    │  │  ┌───────────────────────────┐  │ │
│  │Onboard │  │    │    │  │  │  codelore-agent (LLM)     │  │ │
│  ├────────┤  │    │    │  │  │  ASK / ONBOARD / EXPLORE  │  │ │
│  │Explore │  │    │    │  │  └──────────┬────────────────┘  │ │
│  └────────┘  │    │    │  │             │ uses 6 tools      │ │
│              │    │    │  │  ┌──────────▼────────────────┐  │ │
│              │    │    │  │  │ Custom ES|QL Tools        │  │ │
├──────────────┤    │    │  │  │ + Platform Tools          │  │ │
│ FastAPI API  │◄───┘    │  │  └──────────┬────────────────┘  │ │
│              │────────►│  └─────────────┼───────────────────┘ │
│ /chat/ask    │         │               │ queries              │
│ /onboard/*   │         │  ┌────────────▼────────────────────┐ │
│ /explore/*   │         │  │       Elasticsearch              │ │
│ /ingest/*    │         │  │                                  │ │
└──────┬───────┘         │  │  codelore-commits   (text+vec)  │ │
       │ ingest          │  │  codelore-pr-events (text+vec)  │ │
┌──────▼───────┐         │  │  codelore-docs      (text+vec)  │ │
│  GitHub API  │────────►│  │  codelore-slack     (text+vec)  │ │
│  commits     │         │  │  codelore-decisions (text+vec)  │ │
│  PRs+reviews │         │  └─────────────────────────────────┘ │
│  docs        │         └─────────────────────────────────────┘
└──────────────┘
  Sentence Transformers (all-MiniLM-L6-v2) embeds during ingestion
```

## Features

### Ask Mode — Codebase Q&A
Ask natural language questions about design decisions, architecture rationale, and code history. The agent searches across all indices, cross-references sources, and returns a cited answer with confidence ratings.

> *"Why does the auth service use Redis instead of Postgres for sessions?"*

### Onboard Mode — Guided Learning Paths
Select a topic (architecture, auth, payments, recent changes) and the agent generates a multi-step walkthrough of the most important decisions, key files, and domain experts.

### Explore Mode — Code Archaeology
- **File Timeline**: Enter a file path and see every commit, PR discussion, and decision that affected it, sorted chronologically.
- **Decision Browser**: Browse synthesized architectural decisions with rationale, alternatives considered, importance scores, and affected files.
- **Semantic Search**: kNN vector search across all indices — find conceptual matches like "why did we choose this pattern" even when no exact keywords match.
- **Expert Finder**: Identifies domain experts by aggregating commit history per module, with on-call recommendations (60% recency + 40% volume scoring) and bus factor analysis.
- **Impact Analysis**: Risk dashboard for any file — bus factor, change frequency, co-change coupling ratios, and a computed risk level (low/medium/high).

### GitHub Ingestion Pipeline
One-click ingestion from any GitHub repo via OAuth. Fetches commits (with diffs), PRs (with reviews and comments), and architecture docs. All text is embedded with Sentence Transformers for semantic search. Automatic cleanup of old data on re-ingestion prevents duplicates.

### Multi-Repo Support
Connect any GitHub repo via OAuth, switch between repos, and each repo's data is cleanly isolated with repo-scoped document IDs and per-query filtering.

## Agent Builder Integration

### Agent: `codelore-agent`
A custom agent with detailed system instructions covering 3 operating modes (Ask, Onboard, Explore) and a reasoning framework that:
1. Parses the question to identify topic, time range, and intent
2. Searches across all relevant indices
3. Cross-references findings (commits → PRs → decisions)
4. Synthesizes a narrative answer with citations

### 6 Custom ES|QL Tools

| Tool | Purpose |
|------|---------|
| `codelore-search-commits` | Full-text search on commit messages and summaries |
| `codelore-search-prs` | Search PR titles, descriptions, and review comments |
| `codelore-search-docs` | Search architecture docs, ADRs, and READMEs |
| `codelore-search-decisions` | Search synthesized decision records and rationale |
| `codelore-file-history` | Get complete change history for a specific file |
| `codelore-author-activity` | Find all contributions by a specific author |

### Platform Tools
The agent also uses `platform.core.search`, `platform.core.generate_esql`, and `platform.core.execute_esql` for dynamic queries the pre-built tools don't cover.

## Elasticsearch Indices

| Index | Documents | Purpose |
|-------|-----------|---------|
| `codelore-commits` | Git commits with diffs, impact scores, embeddings | Code change history |
| `codelore-pr-events` | PR descriptions, reviews, comments | Design discussions |
| `codelore-docs` | Architecture docs chunked by section | Documentation |
| `codelore-slack` | Slack threads linked to code | Team discussions |
| `codelore-decisions` | Synthesized decisions with rationale | Architectural memory |

All indices include 384-dim dense vector fields with **int8_hnsw quantization** (cosine similarity) for fast, memory-efficient semantic search.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, httpx
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Framer Motion
- **AI/Agent**: Elastic Agent Builder (Kibana API)
- **Search**: Elasticsearch 8.12+ (Cloud Serverless)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Data Source**: GitHub API (commits, PRs, docs)

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Elastic Cloud account with Agent Builder enabled
- GitHub Personal Access Token

### 1. Clone and configure

```bash
git clone https://github.com/your-org/codelore.git
cd codelore
cp .env.example .env
# Edit .env with your Elastic Cloud and GitHub credentials
```

### 2. Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Create Elasticsearch indices
python -m backend.scripts.setup_indices

# Register Agent Builder tools and agent
python -m backend.scripts.setup_agent

# Ingest from your GitHub repo (configured in .env)
python -m backend.scripts.ingest

# Start API server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev    # Starts on http://localhost:3000, proxies /api to :8000
```

### 4. Verify

Visit http://localhost:3000. The sidebar should show green Elasticsearch status and document counts across all indices.

## Live Data — Real GitHub Repository

CodeLore is connected to a **real GitHub repository**, not synthetic demo data. The ingestion pipeline fetches actual commits (with diffs), pull requests (with reviews and comments), and architecture docs via the GitHub API. All ingested text is embedded with Sentence Transformers for semantic search.

This means every answer from the agent is grounded in real commit history, real PR discussions, and real design decisions — demonstrating CodeLore's value on a production codebase.

## Project Structure

```
codelore/
├── backend/
│   ├── api/                  # REST endpoints
│   │   ├── chat.py           # POST /chat/ask — Q&A via Agent Builder
│   │   ├── onboard.py        # POST /onboard/start, /onboard/next
│   │   ├── explore.py        # timeline, decisions, experts, impact, semantic-search
│   │   ├── ingest.py         # POST/DELETE /ingest/repo, GET /ingest/status
│   │   └── health.py         # GET /health
│   ├── services/
│   │   ├── agent_builder.py  # Kibana Agent Builder API client
│   │   ├── elasticsearch_client.py
│   │   ├── embedding_service.py    # Sentence Transformers
│   │   └── github_ingester.py      # GitHub data pipeline
│   ├── scripts/
│   │   ├── setup_indices.py  # Create ES indices
│   │   ├── setup_agent.py    # Register tools + agent
│   │   └── ingest.py         # GitHub ingestion pipeline
│   ├── models/schemas.py     # Pydantic request/response models
│   ├── config.py             # Settings from .env
│   └── main.py               # FastAPI app
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ask/AskMode.tsx        # Chat Q&A interface
│       │   ├── onboard/OnboardMode.tsx # Guided learning paths
│       │   ├── explore/ExploreMode.tsx     # 5-tab explore interface
│       │   ├── explore/Timeline.tsx        # Chronological event view
│       │   ├── explore/DecisionGraph.tsx   # Decision card grid
│       │   ├── explore/SemanticResults.tsx # kNN search results
│       │   ├── explore/ExpertPanel.tsx     # Expert finder + on-call
│       │   └── explore/ImpactPanel.tsx     # Risk + co-change analysis
│       ├── hooks/             # useChat, useTimeline, useExperts, useImpact, useSemanticSearch
│       └── lib/               # API client, types
├── .env.example
└── README.md
```

## Hackathon Submission

**Elasticsearch Agent Builder Hackathon** (Jan 22 - Feb 27, 2026)

### Problem Solved
New developers waste weeks understanding why code exists. Critical design context is trapped in closed PRs, old Slack threads, and stale docs. CodeLore turns a codebase's scattered history into searchable, AI-powered institutional memory.

### Elasticsearch Features Used
- **kNN vector search** with `int8_hnsw` quantization — 4x memory savings, fast semantic search across all indices
- **Multi-index kNN queries** — single query across 4 indices instead of sequential per-index queries
- **msearch API** — batch multiple queries into one round-trip for timeline construction
- **Aggregations** — `terms`, `cardinality`, `date_histogram`, `max`/`min` for expert finder, impact analysis, and bus factor
- **delete_by_query** — clean repo data isolation, no stale cross-repo results
- **Force merge** — post-ingestion optimization to 1 segment for maximum search performance
- **`_source` excludes** — embedding vectors excluded at mapping level to reduce network overhead

### Agent Builder Features Used
- 6 custom ES|QL tools with parameterized `match()` queries for full-text search
- Platform tools (`search`, `generate_esql`, `execute_esql`) for dynamic queries
- Multi-turn conversations with `conversation_id` for stateful onboarding
- Detailed system instructions defining 3 operating modes and a reasoning framework
- Repo-scoped queries via `[REPO: owner/name]` prefix in agent messages

### Challenges
- **ES|QL syntax**: Discovering that `LIKE CONCAT("%", ?param, "%")` doesn't work in serverless mode and that `match()` is the correct full-text search function for parameterized ESQL tools.
- **Response parsing**: The Agent Builder API nests the answer under `response.message` rather than at the top level, requiring careful response exploration.
- **Token limits**: Multi-turn onboarding conversations can exceed the LLM's context window by turn 3, solved with a graceful fallback to fresh conversations.
- **Cross-repo data leakage**: In-memory auth state lost on server restart caused wrong-repo results. Solved by passing `selected_repo` from frontend with every API call.
- **Query performance**: Sequential per-index kNN queries took minutes. Solved with multi-index queries, msearch batching, int8_hnsw quantization, and force merge.

### What We Liked
- The **ES|QL tool type** made it trivial to create parameterized search tools without custom code.
- **Platform tools** like `generate_esql` let the agent write dynamic queries on the fly for questions our pre-built tools don't cover.
- The **conversation API** handles multi-turn context automatically, making stateful onboarding straightforward.
- **kNN + filter** gives us both semantic understanding and strict repo isolation in a single query.
