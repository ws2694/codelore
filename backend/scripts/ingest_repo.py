"""One-shot script to ingest a GitHub repo into CodeLore indices."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.github_ingester import GitHubIngester
from backend.config import get_settings


async def main():
    settings = get_settings()
    repo = sys.argv[1] if len(sys.argv) > 1 else settings.github_repo

    if not repo:
        print("Usage: python -m backend.scripts.ingest_repo <owner/repo>")
        print("   or set GITHUB_REPO in .env")
        sys.exit(1)

    print(f"Starting ingestion for: {repo}")
    print("=" * 50)

    ingester = GitHubIngester(repo=repo)
    stats = await ingester.ingest_all()

    print("=" * 50)
    print("Ingestion complete!")
    print(f"  Commits:   {stats['commits']}")
    print(f"  PRs:       {stats['prs']}")
    print(f"  PR Events: {stats['pr_events']}")
    print(f"  Docs:      {stats['docs']}")


if __name__ == "__main__":
    asyncio.run(main())
