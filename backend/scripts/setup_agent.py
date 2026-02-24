"""Register CodeLore tools and agent with Elastic Agent Builder via Kibana API."""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import httpx
from backend.config import get_settings

TOOLS = [
    {
        "id": "codelore-search-commits",
        "type": "esql",
        "description": "Search git commits by message content, author, date range, or files changed. Use this to find when and why specific code changes were made.",
        "tags": ["commits", "git-history"],
        "configuration": {
            "query": "FROM codelore-commits | WHERE match(message, ?query) OR match(why_summary, ?query) | SORT date DESC | LIMIT 20",
            "params": {
                "query": {
                    "type": "string",
                    "description": "Search term to find in commit messages and summaries",
                }
            },
        },
    },
    {
        "id": "codelore-search-prs",
        "type": "esql",
        "description": "Search pull request events including descriptions, reviews, and comments. Use this to find discussions about code changes, design decisions, and review feedback.",
        "tags": ["pull-requests", "reviews"],
        "configuration": {
            "query": "FROM codelore-pr-events | WHERE match(title, ?query) OR match(body, ?query) OR match(comment_body, ?query) | SORT created_at DESC | LIMIT 20",
            "params": {
                "query": {
                    "type": "string",
                    "description": "Search term to find in PR titles, descriptions, and comments",
                }
            },
        },
    },
    {
        "id": "codelore-search-docs",
        "type": "esql",
        "description": "Search architecture documents, ADRs, READMEs, and design docs. Use this to find existing documentation about design decisions and system architecture.",
        "tags": ["docs", "architecture", "adr"],
        "configuration": {
            "query": "FROM codelore-docs | WHERE match(content, ?query) OR match(title, ?query) OR match(section, ?query) | SORT last_updated DESC | LIMIT 15",
            "params": {
                "query": {
                    "type": "string",
                    "description": "Search term to find in documentation content and titles",
                }
            },
        },
    },
    {
        "id": "codelore-search-decisions",
        "type": "esql",
        "description": "Search synthesized architectural decisions including their rationale, alternatives considered, and importance. Use this to understand WHY specific technical choices were made.",
        "tags": ["decisions", "architecture", "rationale"],
        "configuration": {
            "query": "FROM codelore-decisions | WHERE match(summary, ?query) OR match(rationale, ?query) OR match(title, ?query) | SORT decided_at DESC | LIMIT 15",
            "params": {
                "query": {
                    "type": "string",
                    "description": "Search term to find in decision records, rationale, and summaries",
                }
            },
        },
    },
    {
        "id": "codelore-file-history",
        "type": "esql",
        "description": "Get the complete change history for a specific file path, including all commits that modified it. Use this for code archaeology and understanding how a file evolved.",
        "tags": ["file-history", "archaeology", "timeline"],
        "configuration": {
            "query": "FROM codelore-commits | WHERE files_changed == ?filepath | SORT date DESC | LIMIT 50",
            "params": {
                "filepath": {
                    "type": "string",
                    "description": "File path or partial path to search for in change history",
                }
            },
        },
    },
    {
        "id": "codelore-author-activity",
        "type": "esql",
        "description": "Find all contributions by a specific author across commits. Use this to identify domain experts and understand who has expertise in which areas of the codebase.",
        "tags": ["team", "expertise", "contributors"],
        "configuration": {
            "query": 'FROM codelore-commits | WHERE author == ?author | SORT date DESC | LIMIT 30',
            "params": {
                "author": {
                    "type": "string",
                    "description": "GitHub username of the author to search for",
                }
            },
        },
    },
]

AGENT = {
    "id": "codelore-agent",
    "name": "CodeLore - Codebase Memory Agent",
    "description": "An AI agent that serves as the institutional memory of a codebase. It searches git history, PR discussions, architecture docs, and team conversations to answer questions about code decisions, generate onboarding paths, and visualize codebase evolution.",
    "labels": ["codebase", "memory", "archaeology", "onboarding"],
    "avatar_color": "#8B5CF6",
    "avatar_symbol": "CL",
    "configuration": {
        "instructions": """You are CodeLore, a Codebase Memory Agent. Your purpose is to help developers understand the WHY behind code — not just what the code does, but why it was written that way, what alternatives were considered, and what discussions led to each decision.

Your Data Sources (Elasticsearch Indices):
- codelore-commits: Git commit history with messages, diffs, and file changes
- codelore-pr-events: Pull request descriptions, review comments, and discussion threads
- codelore-docs: Architecture docs, ADRs, READMEs, and design documents
- codelore-slack: Slack threads linked to code discussions
- codelore-decisions: Synthesized architectural decision records with rationale and alternatives

Your Operating Modes:

**ASK MODE** (default): Answer questions about design decisions, architecture rationale, and code history. Always cite specific sources.

**ONBOARD MODE**: When a user says "onboard me on [module]", generate a structured learning path. Start with the highest-impact decisions, then walk through evolution chronologically. Include links to relevant PRs and docs.

**EXPLORE MODE**: When a user asks "how has [X] evolved" or "show me the history of [Y]", produce a chronological timeline of changes with decision context at each inflection point.

Reasoning Framework:
1. Parse the user's question to identify: the topic, time range, and whether they want the "what", the "why", or the "who"
2. Search across ALL relevant indices — use codelore-search-decisions first for "why" questions
3. Cross-reference findings: if a commit references a PR, search for that PR's discussion
4. Use ES|QL queries for analytical questions (who are experts, what changed recently, churn analysis)
5. Synthesize a narrative answer that connects the dots

Response Format:
- Use Markdown for all responses
- Always include a **Sources** section with specific commit SHAs, PR numbers, doc paths, or Slack thread references
- Include a **Confidence** indicator (High/Medium/Low) based on source corroboration
- When relevant, suggest a **Domain Expert** who might know more (based on commit/review history)
- For timelines, use chronological lists with dates
- For onboarding, use numbered steps with clear headers

Rules:
- ALWAYS search before answering. Never guess at rationale.
- When multiple perspectives exist (e.g., disagreement in PR comments), present them fairly.
- If you find a gap — a decision with no documented rationale — flag it explicitly.
- Distinguish between "this is documented" and "this is my inference based on the code changes."
- Prefer recent information over old when there are conflicts.
- When showing code file paths, format them as inline code.

Semantic Search:
- You have access to `platform.core.search` which supports kNN vector queries across all codelore-* indices.
- All indices have a 384-dimensional `embedding` field indexed for cosine similarity.
- For vague or conceptual questions ("why did we choose...", "what was the reasoning behind..."), use platform.core.search with a kNN query to find semantically related content.
- kNN query format: {"knn": {"field": "embedding", "query_vector": [<384 floats>], "k": 10, "num_candidates": 100}, "_source": {"excludes": ["embedding"]}}
- Since you cannot generate embeddings directly, first try keyword search tools. If results are poor or the question is abstract, recommend the user try the Explore > Semantic Search feature for better conceptual results.

Impact & Risk Analysis:
- When users ask "what would break if I change X?" or "what files are coupled to Y?", explain that the Explore > Impact tab provides co-change analysis, bus factor, and risk assessment.
- For "who should I contact about X?", suggest checking the Explore > Experts tab which shows the on-call recommendation.""",
        "tools": [
            {
                "tool_ids": [
                    "platform.core.search",
                    "platform.core.list_indices",
                    "platform.core.get_index_mapping",
                    "platform.core.generate_esql",
                    "platform.core.execute_esql",
                    "codelore-search-commits",
                    "codelore-search-prs",
                    "codelore-search-docs",
                    "codelore-search-decisions",
                    "codelore-file-history",
                    "codelore-author-activity",
                ]
            }
        ],
    },
}


def setup_agent():
    settings = get_settings()
    kibana_url = settings.kibana_url.rstrip("/")
    headers = {
        "Authorization": f"ApiKey {settings.kibana_api_key}",
        "kbn-xsrf": "true",
        "Content-Type": "application/json",
    }

    print(f"Connecting to Kibana: {kibana_url}")

    with httpx.Client(headers=headers, timeout=30.0) as client:
        # Step 1: Create tools
        print("\nCreating tools...")
        for tool in TOOLS:
            # Try to delete existing tool first
            client.delete(f"{kibana_url}/api/agent_builder/tools/{tool['id']}")

            resp = client.post(
                f"{kibana_url}/api/agent_builder/tools",
                json=tool,
            )
            status = "OK" if resp.status_code in (200, 201) else f"FAIL ({resp.status_code})"
            print(f"  {tool['id']}: {status}")
            if resp.status_code not in (200, 201):
                print(f"    {resp.text[:200]}")

        # Step 2: Create agent
        print("\nCreating agent...")
        client.delete(f"{kibana_url}/api/agent_builder/agents/{AGENT['id']}")

        resp = client.post(
            f"{kibana_url}/api/agent_builder/agents",
            json=AGENT,
        )
        status = "OK" if resp.status_code in (200, 201) else f"FAIL ({resp.status_code})"
        print(f"  codelore-agent: {status}")
        if resp.status_code not in (200, 201):
            print(f"    {resp.text[:300]}")

        # Step 3: Verify
        print("\nVerification:")
        tools_resp = client.get(f"{kibana_url}/api/agent_builder/tools")
        if tools_resp.status_code == 200:
            tools_data = tools_resp.json()
            # Response may be a list or a dict wrapping a list
            if isinstance(tools_data, dict):
                tools_list = tools_data.get("tools", tools_data.get("data", []))
            else:
                tools_list = tools_data
            codelore_tools = [t for t in tools_list if isinstance(t, dict) and t.get("id", "").startswith("codelore-")]
            print(f"  CodeLore tools registered: {len(codelore_tools)}")

        agents_resp = client.get(f"{kibana_url}/api/agent_builder/agents")
        if agents_resp.status_code == 200:
            agents_data = agents_resp.json()
            if isinstance(agents_data, dict):
                agents_list = agents_data.get("agents", agents_data.get("data", []))
            else:
                agents_list = agents_data
            codelore_agents = [a for a in agents_list if isinstance(a, dict) and a.get("id", "").startswith("codelore-")]
            print(f"  CodeLore agents registered: {len(codelore_agents)}")

        # Step 4: Test conversation
        print("\nTest conversation...")
        test_resp = client.post(
            f"{kibana_url}/api/agent_builder/converse",
            json={
                "input": "List all available CodeLore data indices and their purpose.",
                "agent_id": "codelore-agent",
            },
            timeout=60.0,
        )
        if test_resp.status_code == 200:
            data = test_resp.json()
            print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else type(data).__name__}")
            # Try common field names for the answer
            msg = data.get("message") or data.get("output") or data.get("response") or data.get("content") or data.get("text") or ""
            if isinstance(msg, str):
                msg = msg[:200]
            print(f"  Test response: {msg}...")
            print(f"  Conversation ID: {data.get('conversation_id', 'N/A')}")
        else:
            print(f"  Test failed: {test_resp.status_code}")
            print(f"    {test_resp.text[:200]}")


if __name__ == "__main__":
    setup_agent()
