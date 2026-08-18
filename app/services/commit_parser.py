"""
Commit Parser — Conventional Commits regex pre-parser and noise filtering.

Handles:
1. Parsing Conventional Commits format: type(scope): subject
2. Filtering out noise commits (bot authors, merge messages, trivial bumps)
"""
import re
from typing import List, Optional
from pydantic import BaseModel, Field


# --- Conventional Commits Regex ---
# Matches: type(scope): subject  OR  type: subject  OR  type(scope)!: subject
CONVENTIONAL_COMMIT_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)"           # type (feat, fix, chore, etc.)
    r"(?:\((?P<scope>[^)]+)\))?"       # optional (scope)
    r"(?P<breaking>!)?"                # optional ! for breaking changes
    r":\s*"                            # colon + space separator
    r"(?P<subject>.+)$"               # subject (rest of line)
)

# --- Noise Patterns ---
BOT_AUTHORS = [
    "gitlab-ci[bot]",
    "dependabot",
    "dependabot[bot]",
    "renovate[bot]",
    "renovate",
    "github-actions[bot]",
    "semantic-release-bot",
]

NOISE_TITLE_PATTERNS = [
    re.compile(r"^Merge branch\s+", re.IGNORECASE),
    re.compile(r"^Merge remote-tracking branch\s+", re.IGNORECASE),
    re.compile(r"^Merge pull request\s+", re.IGNORECASE),
    re.compile(r"^Merge request\s+", re.IGNORECASE),
    re.compile(r"^Merged in\s+", re.IGNORECASE),
    re.compile(r"^Bump\s+\S+\s+(from|to)\s+", re.IGNORECASE),
    re.compile(r"^Update dependency\s+", re.IGNORECASE),
    re.compile(r"^chore\(deps\):", re.IGNORECASE),
    re.compile(r"^Initial commit$", re.IGNORECASE),
]


class ParsedConventionalCommit(BaseModel):
    """Result of parsing a commit message against Conventional Commits format."""
    commit_type: Optional[str] = Field(None, description="Conventional Commits type (feat, fix, chore, etc.)")
    scope: Optional[str] = Field(None, description="Scope in parentheses, e.g., auth, ui, api")
    subject: Optional[str] = Field(None, description="Commit subject line (after type:)")
    is_breaking: bool = Field(False, description="Whether the commit is a breaking change (!)")
    is_conventional: bool = Field(False, description="Whether the commit follows Conventional Commits format")


def parse_conventional_commit(message: str) -> ParsedConventionalCommit:
    """
    Parse a commit message against the Conventional Commits specification.
    
    Examples:
        "feat(auth): add login button" -> type=feat, scope=auth, subject=add login button
        "fix: resolve crash on startup" -> type=fix, scope=None, subject=resolve crash on startup
        "random commit message" -> is_conventional=False
    """
    # Use only the first line (title) for parsing
    first_line = message.strip().split("\n")[0].strip()
    match = CONVENTIONAL_COMMIT_RE.match(first_line)
    
    if not match:
        return ParsedConventionalCommit(is_conventional=False)
    
    return ParsedConventionalCommit(
        commit_type=match.group("type").lower(),
        scope=match.group("scope"),
        subject=match.group("subject").strip(),
        is_breaking=match.group("breaking") is not None,
        is_conventional=True,
    )


def is_noise_commit(title: str, author_name: str) -> bool:
    """
    Determine if a commit should be filtered out as noise.
    
    Filters:
    - Bot/automated authors (CI bots, dependabot, etc.)
    - Merge commit messages
    - Dependency bump auto-commits
    - Initial commit
    """
    # Check bot authors (case-insensitive)
    author_lower = author_name.lower().strip()
    for bot in BOT_AUTHORS:
        if bot.lower() in author_lower:
            return True
    
    # Check noise title patterns
    title_stripped = title.strip()
    for pattern in NOISE_TITLE_PATTERNS:
        if pattern.search(title_stripped):
            return True
    
    return False


def filter_noise_commits(commits: List[dict]) -> List[dict]:
    """
    Filter a list of raw GitLab commit dicts, removing noise commits.
    Returns only meaningful commits for report generation.
    """
    filtered = []
    for commit in commits:
        title = commit.get("title", "")
        author = commit.get("author_name", "")
        if not is_noise_commit(title, author):
            filtered.append(commit)
    return filtered
