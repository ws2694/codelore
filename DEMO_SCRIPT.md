# CodeLore Demo Script (~3 minutes)

> **Recording tips:** Screen record at 1920x1080. Zoom browser to 110%. Have CodeLore already running with `ws2694/codelore` ingested. Speak clearly and concisely. The twist: we're dogfooding — using CodeLore to explore *itself*.

---

## 0:00–0:20 — The Problem (Hook)

**[Show a GitHub PR page with 47 comments, or a git log scrolling fast]**

> "Your codebase has a memory problem. Right now, there are design decisions buried in old PRs and git logs that no one will ever read again. 
>
> CodeLore is an AI agent that turns your git history into searchable institutional memory — powered by Elasticsearch Agent Builder. To show it works, we're going to point it at *its own source code*."

---

## 0:20–0:45 — Setup & Ingestion (Real Data, Real Repo)

**[CodeLore app — Setup page]**

> "Sign in with GitHub, pick a repo — I'm selecting `codelore` itself."

**[Click `ws2694/codelore` from the repo grid → ingestion starts]**

> "The pipeline fetches every commit, PR discussion, and review comment through the GitHub API. Each document gets embedded into a vector with Sentence Transformers, then indexed into 4 Elasticsearch indices — commits, PR events, docs, and decisions."

**[Show stats ticking: ~9 commits, PRs, decisions synthesized]**

> "Decisions are synthesized *automatically* — any merged PR with review comments or any commit touching 3+ files gets extracted as an architectural decision. No manual tagging."

**[Ingestion completes → transitions to Ask mode]**

---

## 0:45–1:25 — Ask Mode (Agent Builder Reasoning)

**[In Ask mode — type the question]**

> "Let's ask it something real: **'Why did we switch from hardcoded tokens to GitHub OAuth for authentication?'**"

**[Submit. Show "Searching codebase memory..." thinking indicator, then SSE streaming response]**

> "Watch the Agent Builder reason. It has six custom ES|QL tools — right now it's searching `codelore-search-decisions` first because this is a 'why' question, then cross-referencing with `codelore-search-commits` to find the actual commit that introduced OAuth. The answer cites the specific commit and the files that changed."

**[Point to Sources section showing tool calls]**

> "Every answer is grounded in real data. No hallucination — just cited commits and PR numbers."

**[Type follow-up: **'What files were affected by that change?'**]**


---

## 1:25–1:55 — Explore: Semantic Search + Timeline

**[Switch to Explore → Semantic tab]**

> "Semantic search uses kNN vector similarity across all indices. I'll search: **'how does the agent decide which tool to use?'**"

**[Submit — show color-coded results: green commits, purple decisions]**

> "kNN finds commits and the decision about the agent's reasoning framework, ranked by cosine similarity. Commits in green, decisions in purple, docs in cyan."

**[Switch to Timeline tab → click `frontend/src/lib/api.ts` from popular files list]**

> "Timeline is code archaeology. you see our most-changed file and the evolution: Every commit, every PR, every decision that shaped this one file."

---

## 1:55–2:25 — Experts + Impact Analysis

**[Switch to Experts tab → type `backend/api/explore.py`]**

> "Experts tab answers 'who should I contact?' the on-call recommendation tells you exactly who to ping."

**[Switch to Impact tab → type `frontend/src/components/explore/ExploreMode.tsx`]**

> "Impact Analysis is the risk dashboard. `ExploreMode.tsx` was modified and co-changes with these files. The coupling ratio shows these files are tightly coupled. The change frequency chart shows all the activity concentrated in one day"

**[Point to the risk banner and co-change bars]**

> "This is pure Elasticsearch — terms aggregations for co-change detection, date histograms for frequency, cardinality aggregations for bus factor — all in a single query."

---

## 2:25–2:50 — Onboard Mode (Guided Learning)

**[Switch to Onboard mode → pick "Architecture Overview"]**

> "Last mode: onboarding. A new developer joins the team and needs to understand CodeLore itself. Pick 'Architecture Overview' and the agent generates a multi-step learning path from the actual codebase — starting with the five Elasticsearch indices, walking through the ingestion pipeline, then the Agent Builder integration."

**[Show step 1 streaming in, then click Next → step 2]**

> "Each step builds on the last with markdown formatting, code references, and cited sources. It's a personalized guided tour generated from real commit history — not a static wiki page."

---

## 2:50–3:00 — Closing

**[Show sidebar: ES status green, document counts per index]**

> "Six custom ES|QL tools. Five platform tools. kNN vector search. Five Elasticsearch indices. One Agent Builder agent that ties it all together.
>
> CodeLore — stop losing context, start remembering why."

---

## Architecture Diagram (for submission)

```
┌─────────────────────────────────────────────────────────────────┐
│                        CodeLore Frontend                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────────┐  │
│  │ Ask Mode │  │ Onboard  │  │        Explore Mode           │  │
│  │  (Chat)  │  │  (Learn) │  │ Timeline│Decisions│Experts│   │  │
│  │   SSE    │  │  Steps   │  │ Impact │Semantic (kNN)    │   │  │
│  └────┬─────┘  └────┬─────┘  └────────────┬─────────────────┘  │
│       │              │                     │                     │
└───────┼──────────────┼─────────────────────┼─────────────────────┘
        │              │                     │
        ▼              ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │
│  │ /chat/*  │  │/onboard/*│  │/explore/*│  │  /ingest/repo │   │
│  │ ask+stream│  │start+next│  │6 endpoints│  │  GitHub API  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬───────┘   │
│       │              │             │                │            │
│       ▼              ▼             │                ▼            │
│  ┌─────────────────────────┐      │    ┌────────────────────┐   │
│  │  Elastic Agent Builder  │      │    │ Embedding Service  │   │
│  │  (Kibana API)           │      │    │ all-MiniLM-L6-v2   │   │
│  │                         │      │    │ 384-dim vectors    │   │
│  │  6 ES|QL Tools:         │      │    └────────────────────┘   │
│  │  • search-commits       │      │                             │
│  │  • search-prs           │      │                             │
│  │  • search-docs          │      │                             │
│  │  • search-decisions     │      │                             │
│  │  • file-history         │      │                             │
│  │  • author-activity      │      │                             │
│  │                         │      │                             │
│  │  5 Platform Tools:      │      │                             │
│  │  • core.search (kNN)    │      │                             │
│  │  • generate_esql        │      │                             │
│  │  • execute_esql         │      │                             │
│  │  • list_indices         │      │                             │
│  │  • get_index_mapping    │      │                             │
│  └────────┬────────────────┘      │                             │
│           │                       │                             │
└───────────┼───────────────────────┼─────────────────────────────┘
            │                       │
            ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Elasticsearch (Cloud Serverless)                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │codelore-     │  │codelore-     │  │codelore-     │          │
│  │commits       │  │pr-events     │  │docs          │          │
│  │ • message    │  │ • title/body │  │ • content    │          │
│  │ • why_summary│  │ • comments   │  │ • section    │          │
│  │ • files      │  │ • reviews    │  │ • doc_type   │          │
│  │ • embedding  │  │ • embedding  │  │ • embedding  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │codelore-     │  │codelore-     │  All indices have:          │
│  │decisions     │  │slack         │  • Full-text search         │
│  │ • rationale  │  │ • threads    │  • 384-dim dense_vector     │
│  │ • importance │  │ • linked_prs │  • Cosine similarity (kNN)  │
│  │ • embedding  │  │ • embedding  │  • Keyword aggregations     │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cheat Sheet: Demo Queries That Will Return Real Results

### Ask Mode
| Query | Why it works |
|-------|-------------|
| "Why did we switch from hardcoded tokens to GitHub OAuth?" | Commit `f0a1f5f` added OAuth flow — 15 files changed |
| "Why did we add Server-Sent Events instead of returning full responses?" | Commit `9832726` added SSE streaming — 11 files changed |
| "What are the six ES|QL tools registered with the agent and what do they do?" | `setup_agent.py` has all 6 tool definitions |
| "How does the decision synthesis work? Where do decisions come from?" | `github_ingester.py` extracts from PRs + high-impact commits |
| "What Elasticsearch indices does CodeLore use and what's in each one?" | `setup_indices.py` defines all 5 indices |
| Follow-up: "Which one stores the vector embeddings?" | Tests conversation continuity — all 5 have embeddings |

### Semantic Search (no keyword match needed)
| Query | Why it's impressive |
|-------|-------------------|
| "how does the agent decide which tool to use?" | No commit says "decide" — but kNN finds the reasoning framework in `setup_agent.py` |
| "real-time feedback and streaming architecture" | Finds SSE commits without exact phrase match |
| "risk assessment and code coupling" | Finds impact analysis commits + decisions about co-change patterns |
| "onboarding new developers to the codebase" | Finds onboard mode commits + the decision to add guided learning paths |

### Timeline (file paths that show interesting evolution)
| File | Why it's interesting |
|------|---------------------|
| `frontend/src/lib/api.ts` | 5 modifications — evolved from basic client → SSE → OAuth → semantic search |
| `frontend/src/components/explore/ExploreMode.tsx` | 4 modifications — grew from 2 tabs to 5 tabs |
| `backend/api/explore.py` | 3 modifications — started with timeline, added popular files, then semantic + impact |
| `backend/services/github_ingester.py` | 2 modifications — added decision synthesis from commits |

### Experts (modules that show interesting results)
| Module | What you'll see |
|--------|----------------|
| `backend/api` | Shows all backend contributors + bus factor |
| `frontend/src/components/explore` | High commit count, explore module experts |
| `backend/services` | Ingester + agent builder experts |

### Impact Analysis (files with co-change patterns)
| File | What's interesting |
|------|-------------------|
| `frontend/src/components/explore/ExploreMode.tsx` | Co-changes with `api.ts`, `types.ts`, `useTimeline.ts` — high coupling |
| `frontend/src/lib/api.ts` | Co-changes with almost everything — central coupling hub |
| `backend/api/explore.py` | Co-changes with frontend explore components — cross-stack coupling |

---

## Submission Description (~400 words)

### CodeLore — Codebase Memory Agent

**Problem:** Every codebase suffers from institutional knowledge loss. Design decisions are buried in merged PRs, architecture rationale lives in forgotten Slack threads, and the "why" behind code vanishes when engineers leave. New developers waste weeks rediscovering context that was already documented — just not findable.

**Solution:** CodeLore is an AI-powered Codebase Memory Agent built on Elastic Agent Builder and Elasticsearch. It connects to any GitHub repository, ingests the complete history — commits, PR discussions, review comments, and architecture docs — and makes it all searchable through natural language conversation. To prove it works, we dogfood it on its own source code.

**How it works:**

CodeLore indexes data into five Elasticsearch indices, each with 384-dimensional dense vector embeddings for semantic search. The Elastic Agent Builder orchestrates six custom ES|QL tools (commit search, PR search, doc search, decision search, file history, author activity) plus five platform tools (kNN search, dynamic ES|QL generation and execution, index discovery).

The agent operates in three modes:
- **Ask Mode** — Natural language Q&A about design decisions, with cited sources and confidence indicators. Streaming responses via SSE.
- **Onboard Mode** — Multi-step guided learning paths generated from real codebase history, with conversation continuity across steps.
- **Explore Mode** — Five interactive tabs: Timeline (code archaeology), Decisions (architectural memory), Experts (domain expert finder with on-call recommendations and bus factor), Impact (co-change analysis with risk scoring), and Semantic Search (kNN vector similarity across all indices).

Architectural decisions are *synthesized automatically* from merged PRs with review threads and high-impact commits that touch 3+ files — no manual tagging required.

**Elasticsearch & Agent Builder Features Used:**
- 6 custom ES|QL tools with parameterized queries (`match()`, `==`, `SORT`, `LIMIT`)
- `platform.core.search` for kNN vector queries (384-dim cosine similarity)
- `platform.core.generate_esql` and `execute_esql` for dynamic analytical queries
- Terms aggregations for expert ranking and co-change detection
- Date histogram aggregations for change frequency analysis
- Cardinality aggregations for bus factor calculation
- Multi-match queries with field boosting for decision relevance
- Dense vector indexing with cosine similarity across all five indices

**Features we liked:**
1. **ES|QL tools are powerful** — parameterized queries with `match()` and `==` operators make it easy to build domain-specific search without complex DSL
2. **Conversation continuity** — Agent Builder's `conversation_id` lets us build multi-step onboarding that maintains context across turns
3. **Platform tools complement custom tools** — `generate_esql` handles ad-hoc analytical queries our predefined tools don't cover

**Challenge:** ES|QL syntax differs from standard Elasticsearch DSL — `LIKE CONCAT()` doesn't work in serverless, `match()` requires the correct field type, and parameter types must be `"string"` not `"text"`. Debugging required careful reading of the ES|QL reference.
