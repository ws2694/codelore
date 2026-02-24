"""GitHub data ingester — fetches commits, PRs, docs and indexes into Elasticsearch."""

import hashlib
from datetime import datetime

import httpx
from elasticsearch.helpers import bulk

from backend.config import get_settings
from backend.services.elasticsearch_client import get_es_client
from backend.services.embedding_service import embed_text, embed_batch


class GitHubIngester:
    def __init__(self, token: str | None = None, repo: str | None = None):
        settings = get_settings()
        self.token = token or settings.github_token
        self.repo = repo or settings.github_repo
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base_url = "https://api.github.com"
        self.es = get_es_client()
        self.stats = {"commits": 0, "prs": 0, "pr_events": 0, "docs": 0}

    async def ingest_all(self) -> dict:
        """Run full ingestion pipeline."""
        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            self.client = client
            await self.ingest_commits()
            await self.ingest_prs()
            await self.ingest_docs()
        return self.stats

    async def ingest_commits(self, max_pages: int = 5):
        """Fetch and index git commits."""
        print(f"Ingesting commits from {self.repo}...")
        actions = []
        page = 1

        while page <= max_pages:
            resp = await self.client.get(
                f"{self.base_url}/repos/{self.repo}/commits",
                params={"per_page": 100, "page": page},
            )
            if resp.status_code != 200:
                print(f"  Error fetching commits page {page}: {resp.status_code}")
                break

            commits = resp.json()
            if not commits:
                break

            for commit in commits:
                commit_data = commit.get("commit", {})
                sha = commit.get("sha", "")

                # Fetch detailed commit info for file stats
                detail_resp = await self.client.get(
                    f"{self.base_url}/repos/{self.repo}/commits/{sha}"
                )
                files_changed = []
                additions = 0
                deletions = 0
                diff_parts = []

                if detail_resp.status_code == 200:
                    detail = detail_resp.json()
                    stats = detail.get("stats", {})
                    additions = stats.get("additions", 0)
                    deletions = stats.get("deletions", 0)
                    for f in detail.get("files", []):
                        files_changed.append(f["filename"])
                        if f.get("patch"):
                            diff_parts.append(
                                f"{f['filename']}: +{f.get('additions', 0)}-{f.get('deletions', 0)}"
                            )

                message = commit_data.get("message", "")
                diff_summary = "; ".join(diff_parts[:20])
                embed_input = f"{message}\n{diff_summary}" if diff_summary else message

                impact = self._compute_impact(
                    len(files_changed), additions + deletions
                )

                doc = {
                    "_index": "codelore-commits",
                    "_id": sha[:12],
                    "sha": sha,
                    "message": message,
                    "author": (commit.get("author") or {}).get("login", "unknown"),
                    "author_email": commit_data.get("author", {}).get("email", ""),
                    "date": commit_data.get("author", {}).get("date"),
                    "files_changed": files_changed,
                    "additions": additions,
                    "deletions": deletions,
                    "diff_summary": diff_summary,
                    "why_summary": message.split("\n")[0],
                    "repo": self.repo,
                    "impact_score": impact,
                    "embedding": embed_text(embed_input),
                }
                actions.append(doc)

            page += 1

        if actions:
            success, _ = bulk(self.es, actions)
            self.stats["commits"] = success
            print(f"  Indexed {success} commits")

    async def ingest_prs(self, max_pages: int = 3):
        """Fetch and index pull requests with reviews and comments."""
        print(f"Ingesting PRs from {self.repo}...")
        actions = []
        page = 1

        while page <= max_pages:
            resp = await self.client.get(
                f"{self.base_url}/repos/{self.repo}/pulls",
                params={"state": "all", "per_page": 50, "page": page},
            )
            if resp.status_code != 200:
                print(f"  Error fetching PRs page {page}: {resp.status_code}")
                break

            prs = resp.json()
            if not prs:
                break

            for pr in prs:
                pr_num = pr["number"]

                # Index PR description
                pr_text = f"{pr.get('title', '')}\n{pr.get('body', '') or ''}"
                actions.append({
                    "_index": "codelore-pr-events",
                    "_id": f"pr-{pr_num}-opened",
                    "pr_number": pr_num,
                    "title": pr.get("title", ""),
                    "body": pr.get("body", "") or "",
                    "author": (pr.get("user") or {}).get("login", "unknown"),
                    "state": pr.get("state", ""),
                    "created_at": pr.get("created_at"),
                    "merged_at": pr.get("merged_at"),
                    "closed_at": pr.get("closed_at"),
                    "event_type": "pr_opened",
                    "labels": [l["name"] for l in pr.get("labels", [])],
                    "repo": self.repo,
                    "embedding": embed_text(pr_text),
                })
                self.stats["prs"] += 1

                # Fetch review comments
                rev_resp = await self.client.get(
                    f"{self.base_url}/repos/{self.repo}/pulls/{pr_num}/reviews"
                )
                if rev_resp.status_code == 200:
                    for review in rev_resp.json():
                        body = review.get("body", "") or ""
                        if not body.strip():
                            continue
                        actions.append({
                            "_index": "codelore-pr-events",
                            "_id": f"pr-{pr_num}-review-{review['id']}",
                            "pr_number": pr_num,
                            "title": pr.get("title", ""),
                            "author": (pr.get("user") or {}).get("login", "unknown"),
                            "event_type": "review",
                            "review_state": review.get("state", ""),
                            "comment_body": body,
                            "comment_author": (review.get("user") or {}).get("login", ""),
                            "comment_date": review.get("submitted_at"),
                            "created_at": pr.get("created_at"),
                            "repo": self.repo,
                            "embedding": embed_text(body),
                        })
                        self.stats["pr_events"] += 1

                # Fetch PR comments
                comments_resp = await self.client.get(
                    f"{self.base_url}/repos/{self.repo}/pulls/{pr_num}/comments"
                )
                if comments_resp.status_code == 200:
                    for comment in comments_resp.json():
                        body = comment.get("body", "") or ""
                        if not body.strip():
                            continue
                        actions.append({
                            "_index": "codelore-pr-events",
                            "_id": f"pr-{pr_num}-comment-{comment['id']}",
                            "pr_number": pr_num,
                            "title": pr.get("title", ""),
                            "author": (pr.get("user") or {}).get("login", "unknown"),
                            "event_type": "review_comment",
                            "comment_body": body,
                            "comment_author": (comment.get("user") or {}).get("login", ""),
                            "comment_date": comment.get("created_at"),
                            "files_changed": [comment.get("path", "")] if comment.get("path") else [],
                            "created_at": pr.get("created_at"),
                            "repo": self.repo,
                            "embedding": embed_text(body),
                        })
                        self.stats["pr_events"] += 1

            page += 1

        if actions:
            success, _ = bulk(self.es, actions)
            print(f"  Indexed {success} PR events")

    async def ingest_docs(self, paths: list[str] | None = None):
        """Fetch and index markdown documentation files."""
        print(f"Ingesting docs from {self.repo}...")
        if paths is None:
            paths = [""]  # Start from repo root

        actions = []

        for path in paths:
            await self._crawl_docs(path, actions)

        if actions:
            success, _ = bulk(self.es, actions)
            self.stats["docs"] = success
            print(f"  Indexed {success} doc sections")

    async def _crawl_docs(self, path: str, actions: list, depth: int = 0):
        """Recursively crawl a directory for markdown files."""
        if depth > 3:
            return

        resp = await self.client.get(
            f"{self.base_url}/repos/{self.repo}/contents/{path}"
        )
        if resp.status_code != 200:
            return

        contents = resp.json()
        if not isinstance(contents, list):
            contents = [contents]

        for item in contents:
            if item["type"] == "dir" and item["name"].lower() in (
                "docs", "doc", "adr", "adrs", "architecture", "design",
            ):
                await self._crawl_docs(item["path"], actions, depth + 1)
            elif item["type"] == "file" and item["name"].lower().endswith((".md", ".txt", ".rst")):
                await self._index_doc_file(item, actions)

    async def _index_doc_file(self, item: dict, actions: list):
        """Fetch and index a single documentation file."""
        resp = await self.client.get(item.get("download_url", ""))
        if resp.status_code != 200:
            return

        content = resp.text
        filename = item["name"]
        path = item["path"]

        # Determine doc type
        doc_type = "readme"
        lower_path = path.lower()
        if "adr" in lower_path:
            doc_type = "adr"
        elif "design" in lower_path:
            doc_type = "design_doc"
        elif "changelog" in lower_path:
            doc_type = "changelog"
        elif "runbook" in lower_path:
            doc_type = "runbook"

        # Extract title from first heading
        title = filename
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Chunk by sections (split on ## headings) for better retrieval
        sections = self._split_into_sections(content)

        for i, section in enumerate(sections):
            if len(section.strip()) < 20:
                continue
            doc_id = hashlib.md5(f"{path}:{i}".encode()).hexdigest()[:12]
            actions.append({
                "_index": "codelore-docs",
                "_id": doc_id,
                "doc_id": doc_id,
                "path": path,
                "filename": filename,
                "doc_type": doc_type,
                "title": title,
                "content": content if i == 0 else "",
                "section": section,
                "last_author": "",
                "repo": self.repo,
                "embedding": embed_text(f"{title}\n{section}"),
            })
            self.stats["docs"] += 1

    def _split_into_sections(self, content: str) -> list[str]:
        """Split markdown content into sections by ## headings."""
        sections = []
        current = []

        for line in content.split("\n"):
            if line.startswith("## ") and current:
                sections.append("\n".join(current))
                current = [line]
            else:
                current.append(line)

        if current:
            sections.append("\n".join(current))

        return sections if sections else [content]

    def _compute_impact(self, files_count: int, lines_changed: int) -> float:
        """Compute an impact score for a commit."""
        score = 0.0
        score += min(files_count * 0.1, 1.0)
        score += min(lines_changed * 0.001, 1.0)
        return min(score, 5.0)
