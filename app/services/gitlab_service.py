"""
GitLab Service — Handles commit fetching from GitLab REST API v4.

Features:
- Full pagination support (follows Link headers for >100 commits)
- Noise filtering (bot authors, merge commits, trivial bumps)
- Metadata normalization into NormalizedCommit
- Conventional Commits pre-parsing
"""
import requests
from typing import List

from app.core.state import NormalizedCommit
from app.services.commit_parser import (
    filter_noise_commits,
    parse_conventional_commit,
)
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.logger import logger


class GitLabService:

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_commits_raw(self, url: str, token: str, project_id: str, start_date: str, end_date: str) -> List[dict]:
        """
        Fetch ALL commits from GitLab with full pagination and retry logic.
        Returns raw dicts from the API.
        """
        api_url = f"{url}/api/v4/projects/{project_id}/repository/commits"
        headers = {"PRIVATE-TOKEN": token}
        params = {
            "since": f"{start_date}T00:00:00Z",
            "until": f"{end_date}T23:59:59Z",
            "with_stats": "true",
            "per_page": 100,
        }

        all_commits = []
        page = 1
        max_pages = 50  # Safety limit (5000 commits max)

        while page <= max_pages:
            params["page"] = page
            response = requests.get(api_url, headers=headers, params=params)

            if response.status_code != 200:
                raise Exception(f"GitLab API Error: {response.status_code} - {response.text}")

            commits = response.json()
            if not commits:
                break  # No more results

            all_commits.extend(commits)

            # Check for next page via headers
            next_page = response.headers.get("x-next-page", "")
            if not next_page:
                break
            page = int(next_page)

        return all_commits

    def get_commits(self, url: str, token: str, project_id: str, start_date: str, end_date: str) -> List[dict]:
        """
        Backward-compatible method: fetches raw commits.
        Used by existing /api/test-gitlab endpoint.
        """
        return self.get_commits_raw(url, token, project_id, start_date, end_date)

    def get_normalized_commits(
        self,
        url: str,
        token: str,
        project_id: str,
        start_date: str,
        end_date: str,
        filter_noise: bool = True,
    ) -> List[NormalizedCommit]:
        """
        Full pipeline method: fetches, filters, normalizes, and pre-parses commits.
        
        Returns NormalizedCommit objects ready for the LangGraph pipeline.
        """
        raw_commits = self.get_commits_raw(url, token, project_id, start_date, end_date)

        # 1. Filter noise commits
        if filter_noise:
            raw_commits = filter_noise_commits(raw_commits)

        # 2. Normalize and pre-parse each commit
        normalized = []
        for c in raw_commits:
            title = c.get("title", "")
            message = c.get("message", "")
            stats = c.get("stats") or {}

            # Parse Conventional Commits format
            parsed = parse_conventional_commit(title)

            normalized.append(NormalizedCommit(
                short_id=c.get("short_id", ""),
                title=title,
                message=message,
                author_name=c.get("author_name", ""),
                committed_date=c.get("committed_date", "") or c.get("created_at", ""),
                stats_additions=stats.get("additions", 0),
                stats_deletions=stats.get("deletions", 0),
                cc_type=parsed.commit_type,
                cc_scope=parsed.scope,
                cc_subject=parsed.subject,
                cc_is_conventional=parsed.is_conventional,
            ))

        return normalized