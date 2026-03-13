"""Data models for chronicle-ai."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class StoryMode(str, Enum):
    """Story generation modes."""
    FILE = "file"        # Story about a specific file
    REPO = "repo"        # Overall repo story
    AUTHOR = "author"    # Story of an author's contributions
    RANGE = "range"      # Story between two refs (tags, commits, branches)


class StoryStyle(str, Enum):
    """Story output style."""
    NARRATIVE = "narrative"    # Flowing prose story
    TIMELINE = "timeline"      # Chronological timeline
    DETECTIVE = "detective"    # Why-focused investigation ("why was this changed?")


@dataclass(frozen=True)
class CommitInfo:
    """Information about a single commit."""
    sha: str
    short_sha: str
    message: str
    author: str
    author_email: str
    date: datetime
    files_changed: List[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0

    @property
    def summary(self) -> str:
        """First line of the commit message."""
        return self.message.split("\n")[0].strip()

    @property
    def is_merge(self) -> bool:
        """Whether this is a merge commit."""
        return self.message.startswith("Merge ")


@dataclass(frozen=True)
class FileHistory:
    """Git history for a specific file."""
    path: str
    commits: List[CommitInfo] = field(default_factory=list)
    total_insertions: int = 0
    total_deletions: int = 0
    first_commit: Optional[CommitInfo] = None
    last_commit: Optional[CommitInfo] = None
    unique_authors: List[str] = field(default_factory=list)

    @property
    def churn(self) -> int:
        """Total lines changed (insertions + deletions)."""
        return self.total_insertions + self.total_deletions

    @property
    def age_days(self) -> Optional[int]:
        """Age of the file in days."""
        if self.first_commit is None:
            return None
        delta = datetime.now() - self.first_commit.date.replace(tzinfo=None)
        return delta.days


@dataclass(frozen=True)
class RepoSummary:
    """High-level summary of a git repository."""
    path: str
    total_commits: int
    total_authors: List[str]
    first_commit: Optional[CommitInfo]
    last_commit: Optional[CommitInfo]
    most_changed_files: List[str] = field(default_factory=list)
    commits: List[CommitInfo] = field(default_factory=list)

    @property
    def age_days(self) -> Optional[int]:
        """Age of the repo in days."""
        if self.first_commit is None:
            return None
        delta = datetime.now() - self.first_commit.date.replace(tzinfo=None)
        return delta.days


@dataclass(frozen=True)
class StoryConfig:
    """Configuration for story generation."""
    mode: StoryMode = StoryMode.REPO
    style: StoryStyle = StoryStyle.NARRATIVE
    target: Optional[str] = None           # file path, author name, or ref range
    since: Optional[str] = None            # e.g., "6 months ago", "2024-01-01"
    until: Optional[str] = None            # e.g., "HEAD", "v2.0"
    max_commits: int = 100
    provider: str = "claude"
    model: Optional[str] = None
    plain: bool = False                    # Plain text output (no Rich formatting)


@dataclass(frozen=True)
class GeneratedStory:
    """The generated story output."""
    title: str
    content: str
    mode: StoryMode
    style: StoryStyle
    commit_count: int
    author_count: int
    provider_used: str
