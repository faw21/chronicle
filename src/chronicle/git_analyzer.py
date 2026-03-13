"""Git history analysis for chronicle-ai."""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import git
from git import InvalidGitRepositoryError, NoSuchPathError

from .models import CommitInfo, FileHistory, RepoSummary


def _parse_since(since: Optional[str]) -> Optional[datetime]:
    """Parse a human-readable 'since' string into a datetime."""
    if since is None:
        return None

    since = since.strip().lower()

    # Handle "N days/weeks/months/years ago"
    pattern = r"(\d+)\s+(day|week|month|year)s?\s+ago"
    match = re.match(pattern, since)
    if match:
        n = int(match.group(1))
        unit = match.group(2)
        now = datetime.now()
        if unit == "day":
            return now - timedelta(days=n)
        elif unit == "week":
            return now - timedelta(weeks=n)
        elif unit == "month":
            return now - timedelta(days=n * 30)
        elif unit == "year":
            return now - timedelta(days=n * 365)

    # Try ISO date format
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(since, fmt)
        except ValueError:
            continue

    return None


def _build_commit_info(commit: git.Commit) -> CommitInfo:
    """Convert a gitpython Commit to CommitInfo."""
    files_changed: List[str] = []
    insertions = 0
    deletions = 0

    try:
        if commit.parents:
            diff = commit.parents[0].diff(commit)
        else:
            diff = commit.diff(git.NULL_TREE)

        for d in diff:
            if d.a_path:
                files_changed.append(d.a_path)
            elif d.b_path:
                files_changed.append(d.b_path)

        stats = commit.stats
        insertions = stats.total.get("insertions", 0)
        deletions = stats.total.get("deletions", 0)
    except Exception:
        pass

    # Handle both offset-aware and offset-naive datetimes
    committed_date = commit.committed_datetime
    if hasattr(committed_date, "replace"):
        try:
            committed_date = committed_date.replace(tzinfo=None)
        except Exception:
            pass

    return CommitInfo(
        sha=commit.hexsha,
        short_sha=commit.hexsha[:7],
        message=commit.message.strip(),
        author=str(commit.author.name),
        author_email=str(commit.author.email),
        date=committed_date,
        files_changed=files_changed,
        insertions=insertions,
        deletions=deletions,
    )


def get_repo(path: str = ".") -> git.Repo:
    """Get the git repository at the given path."""
    try:
        return git.Repo(path, search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        raise ValueError(f"Not a git repository: {path}") from e


def get_commits(
    repo: git.Repo,
    since: Optional[datetime] = None,
    until: Optional[str] = None,
    author: Optional[str] = None,
    paths: Optional[List[str]] = None,
    max_commits: int = 200,
) -> List[CommitInfo]:
    """Fetch commits from the repo with optional filters."""
    try:
        kwargs = {}
        if until:
            kwargs["rev"] = until
        if paths:
            kwargs["paths"] = paths

        commits_iter = repo.iter_commits(max_count=max_commits * 2, **kwargs)
        commits = []

        for commit in commits_iter:
            if len(commits) >= max_commits:
                break

            # Filter by since date
            commit_date = commit.committed_datetime
            if hasattr(commit_date, "replace"):
                try:
                    commit_date = commit_date.replace(tzinfo=None)
                except Exception:
                    pass

            if since and commit_date < since:
                continue

            # Filter by author
            if author:
                author_lower = author.lower()
                if (
                    author_lower not in str(commit.author.name).lower()
                    and author_lower not in str(commit.author.email).lower()
                ):
                    continue

            commits.append(_build_commit_info(commit))

        return commits

    except (git.GitCommandError, ValueError):
        return []


def analyze_file(
    repo: git.Repo,
    file_path: str,
    since: Optional[datetime] = None,
    max_commits: int = 100,
) -> FileHistory:
    """Analyze the git history of a specific file."""
    commits = get_commits(
        repo,
        since=since,
        paths=[file_path],
        max_commits=max_commits,
    )

    total_insertions = sum(c.insertions for c in commits)
    total_deletions = sum(c.deletions for c in commits)

    unique_authors = list(
        dict.fromkeys(c.author for c in commits)  # preserves order, deduplicates
    )

    first_commit = commits[-1] if commits else None
    last_commit = commits[0] if commits else None

    return FileHistory(
        path=file_path,
        commits=commits,
        total_insertions=total_insertions,
        total_deletions=total_deletions,
        first_commit=first_commit,
        last_commit=last_commit,
        unique_authors=unique_authors,
    )


def analyze_repo(
    repo: git.Repo,
    since: Optional[datetime] = None,
    until: Optional[str] = None,
    max_commits: int = 200,
) -> RepoSummary:
    """Analyze the overall repository history."""
    commits = get_commits(
        repo,
        since=since,
        until=until,
        max_commits=max_commits,
    )

    if not commits:
        return RepoSummary(
            path=str(repo.working_dir),
            total_commits=0,
            total_authors=[],
            first_commit=None,
            last_commit=None,
            most_changed_files=[],
            commits=[],
        )

    # Count file changes
    file_change_count: dict = {}
    for commit in commits:
        for f in commit.files_changed:
            file_change_count[f] = file_change_count.get(f, 0) + 1

    most_changed = sorted(file_change_count, key=lambda k: file_change_count[k], reverse=True)[:10]

    unique_authors = list(dict.fromkeys(c.author for c in commits))
    first_commit = commits[-1] if commits else None
    last_commit = commits[0] if commits else None

    return RepoSummary(
        path=str(repo.working_dir),
        total_commits=len(commits),
        total_authors=unique_authors,
        first_commit=first_commit,
        last_commit=last_commit,
        most_changed_files=most_changed,
        commits=commits,
    )


def analyze_author(
    repo: git.Repo,
    author: str,
    since: Optional[datetime] = None,
    max_commits: int = 200,
) -> Tuple[List[CommitInfo], List[str]]:
    """Analyze commits by a specific author.

    Returns (commits, most_changed_files).
    """
    commits = get_commits(
        repo,
        since=since,
        author=author,
        max_commits=max_commits,
    )

    file_change_count: dict = {}
    for commit in commits:
        for f in commit.files_changed:
            file_change_count[f] = file_change_count.get(f, 0) + 1

    most_changed = sorted(file_change_count, key=lambda k: file_change_count[k], reverse=True)[:10]

    return commits, most_changed


def parse_since_string(since: Optional[str]) -> Optional[datetime]:
    """Public interface to parse since strings."""
    return _parse_since(since)
