"""GitHub data ingester — fetches commits, PRs, docs and indexes into Elasticsearch."""

import hashlib
from datetime import datetime

import httpx
from elasticsearch.helpers import bulk

from backend.config import get_settings
from backend.services.elasticsearch_client import get_es_client
from backend.services.embedding_service import embed_text, embed_batch


ALL_INDICES = [
    "codelore-commits",
    "codelore-pr-events",
    "codelore-docs",
    "codelore-decisions",
    "codelore-slack",
]


def delete_repo_data(repo: str) -> dict[str, int]:
    """Delete all documents for a given repo across all indices."""
    es = get_es_client()
    deleted = {}
    for index in ALL_INDICES:
        if not es.indices.exists(index=index):
            continue
        resp = es.delete_by_query(
            index=index,
            body={"query": {"term": {"repo": repo}}},
            refresh=True,
        )
        deleted[index] = resp.get("deleted", 0)
    return deleted


class GitHubIngester:
    def __init__(self, token: str | None = None, repo: str | None = None):
        settings = get_settings()
        self.token = token or settings.github_token
        self.repo = repo or settings.github_repo
        # Short repo prefix for document IDs to avoid cross-repo collisions
        self._repo_prefix = hashlib.md5(self.repo.encode()).hexdigest()[:6]
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base_url = "https://api.github.com"
        self.es = get_es_client()
        self.stats = {"commits": 0, "prs": 0, "pr_events": 0, "docs": 0, "decisions": 0}

    def _doc_id(self, *parts: str) -> str:
        """Build a repo-scoped document ID."""
        return f"{self._repo_prefix}-{'-'.join(parts)}"

    async def ingest_all(self) -> dict:
        """Run full ingestion pipeline. Cleans old data for this repo first."""
        # Delete existing data for this repo to avoid stale/duplicate documents
        deleted = delete_repo_data(self.repo)
        total_deleted = sum(deleted.values())
        if total_deleted:
            print(f"Cleaned {total_deleted} old documents for {self.repo}")

        async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
            self.client = client
            await self.ingest_commits()
            await self.ingest_prs()
            await self.ingest_docs()
            await self.synthesize_decisions()
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
                    "_id": self._doc_id("c", sha[:12]),
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
                    "_id": self._doc_id("pr", str(pr_num), "opened"),
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
                            "_id": self._doc_id("pr", str(pr_num), "review", str(review['id'])),
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
                            "_id": self._doc_id("pr", str(pr_num), "comment", str(comment['id'])),
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
            content_hash = hashlib.md5(f"{path}:{i}".encode()).hexdigest()[:12]
            doc_id = self._doc_id("doc", content_hash)
            actions.append({
                "_index": "codelore-docs",
                "_id": doc_id,
                "doc_id": content_hash,
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

    async def synthesize_decisions(self):
        """Synthesize architectural decisions from merged PRs and high-impact commits."""
        print(f"Synthesizing decisions from {self.repo}...")
        actions = []

        # --- From merged PRs ---
        page = 1
        while page <= 3:
            resp = await self.client.get(
                f"{self.base_url}/repos/{self.repo}/pulls",
                params={"state": "closed", "per_page": 50, "page": page},
            )
            if resp.status_code != 200:
                break

            prs = resp.json()
            if not prs:
                break

            for pr in prs:
                if not pr.get("merged_at"):
                    continue

                body = pr.get("body", "") or ""
                title = pr.get("title", "")

                if len(body) < 30 and len(title) < 15:
                    continue

                pr_num = pr["number"]
                author = (pr.get("user") or {}).get("login", "unknown")
                labels = [l["name"] for l in pr.get("labels", [])]

                rationale_parts = []
                rev_resp = await self.client.get(
                    f"{self.base_url}/repos/{self.repo}/pulls/{pr_num}/reviews"
                )
                if rev_resp.status_code == 200:
                    for review in rev_resp.json():
                        r_body = review.get("body", "") or ""
                        if r_body.strip():
                            reviewer = (review.get("user") or {}).get("login", "")
                            rationale_parts.append(f"@{reviewer}: {r_body}")

                files_resp = await self.client.get(
                    f"{self.base_url}/repos/{self.repo}/pulls/{pr_num}/files"
                )
                affected_files = []
                if files_resp.status_code == 200:
                    affected_files = [f["filename"] for f in files_resp.json()[:20]]

                modules = self._extract_modules(affected_files)
                rationale = "\n\n".join(rationale_parts) if rationale_parts else body
                summary = body[:500] if body else title

                importance = min(
                    (len(affected_files) * 0.2) + (len(rationale_parts) * 0.5) + 1.0,
                    5.0,
                )

                embed_input = f"{title}\n{summary}\n{rationale[:300]}"

                actions.append({
                    "_index": "codelore-decisions",
                    "_id": self._doc_id("dec-pr", str(pr_num)),
                    "decision_id": f"pr-{pr_num}",
                    "title": title,
                    "summary": summary,
                    "rationale": rationale,
                    "alternatives_considered": "",
                    "decided_by": author,
                    "decided_at": pr.get("merged_at"),
                    "status": "accepted",
                    "tags": labels,
                    "affected_files": affected_files,
                    "affected_modules": list(modules),
                    "related_commits": [],
                    "related_prs": [pr_num],
                    "source_type": "pull_request",
                    "source_ids": [f"pr-{pr_num}"],
                    "repo": self.repo,
                    "importance": importance,
                    "embedding": embed_text(embed_input),
                })

            page += 1

        pr_count = len(actions)

        # --- From high-impact commits ---
        # Commits that touch 3+ files or have multi-line messages represent decisions
        pr_shas = set()  # track PR-linked commits to avoid duplicates
        page = 1
        while page <= 5:
            resp = await self.client.get(
                f"{self.base_url}/repos/{self.repo}/commits",
                params={"per_page": 100, "page": page},
            )
            if resp.status_code != 200:
                break

            commits = resp.json()
            if not commits:
                break

            for commit in commits:
                sha = commit.get("sha", "")
                commit_data = commit.get("commit", {})
                message = commit_data.get("message", "")

                # Skip merge commits and trivial one-liners
                lines = [l for l in message.split("\n") if l.strip()]
                title_line = lines[0] if lines else message[:80]

                if title_line.lower().startswith("merge"):
                    continue

                # Fetch detail for file count
                detail_resp = await self.client.get(
                    f"{self.base_url}/repos/{self.repo}/commits/{sha}"
                )
                if detail_resp.status_code != 200:
                    continue

                detail = detail_resp.json()
                files = detail.get("files", [])
                stats = detail.get("stats", {})
                total_changes = stats.get("total", 0)
                affected_files = [f["filename"] for f in files[:20]]

                # Decision criteria: 3+ files changed, OR 50+ lines changed,
                # OR multi-line commit message (rationale in body)
                has_body = len(lines) > 1
                is_significant = len(files) >= 3 or total_changes >= 50 or has_body

                if not is_significant:
                    continue

                author = (commit.get("author") or {}).get("login", "unknown")
                date = commit_data.get("author", {}).get("date")
                body_text = "\n".join(lines[1:]).strip() if has_body else ""

                modules = self._extract_modules(affected_files)

                # Build summary from commit message body or diff stats
                if body_text:
                    summary = body_text[:500]
                    rationale = body_text
                else:
                    file_summary = ", ".join(affected_files[:5])
                    if len(affected_files) > 5:
                        file_summary += f" (+{len(affected_files) - 5} more)"
                    summary = f"Changed {len(files)} files ({stats.get('additions', 0)}+ {stats.get('deletions', 0)}-): {file_summary}"
                    rationale = summary

                importance = min(
                    (len(files) * 0.15) + (total_changes * 0.002) + (1.0 if has_body else 0.5),
                    5.0,
                )

                embed_input = f"{title_line}\n{summary}"

                actions.append({
                    "_index": "codelore-decisions",
                    "_id": self._doc_id("dec-c", sha[:12]),
                    "decision_id": f"commit-{sha[:12]}",
                    "title": title_line,
                    "summary": summary,
                    "rationale": rationale,
                    "alternatives_considered": "",
                    "decided_by": author,
                    "decided_at": date,
                    "status": "accepted",
                    "tags": [],
                    "affected_files": affected_files,
                    "affected_modules": list(modules),
                    "related_commits": [sha[:12]],
                    "related_prs": [],
                    "source_type": "commit",
                    "source_ids": [sha[:12]],
                    "repo": self.repo,
                    "importance": importance,
                    "embedding": embed_text(embed_input),
                })

            page += 1

        commit_count = len(actions) - pr_count

        if actions:
            success, _ = bulk(self.es, actions)
            self.stats["decisions"] = success
            print(f"  Synthesized {success} decisions ({pr_count} from PRs, {commit_count} from commits)")
        else:
            print("  No PRs or commits with enough content to synthesize decisions")

    def _extract_modules(self, files: list[str]) -> set[str]:
        """Extract top-level module paths from file paths."""
        modules = set()
        for f in files:
            parts = f.split("/")
            if len(parts) >= 2:
                modules.add(parts[0] + "/" + parts[1])
            else:
                modules.add(parts[0])
        return modules

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
