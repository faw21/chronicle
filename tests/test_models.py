"""Tests for chronicle.models."""

from datetime import datetime

import pytest

from chronicle.models import (
    CommitInfo,
    FileHistory,
    GeneratedStory,
    RepoSummary,
    StoryConfig,
    StoryMode,
    StoryStyle,
)


class TestCommitInfo:
    def test_summary_returns_first_line(self):
        commit = CommitInfo(
            sha="abc123", short_sha="abc", message="feat: short\n\nLong body here.",
            author="Alice", author_email="a@b.com", date=datetime.now(),
        )
        assert commit.summary == "feat: short"

    def test_summary_single_line(self):
        commit = CommitInfo(
            sha="abc123", short_sha="abc", message="fix: bug",
            author="Bob", author_email="b@b.com", date=datetime.now(),
        )
        assert commit.summary == "fix: bug"

    def test_is_merge_true(self):
        commit = CommitInfo(
            sha="abc", short_sha="abc", message="Merge branch 'main'",
            author="Alice", author_email="a@b.com", date=datetime.now(),
        )
        assert commit.is_merge is True

    def test_is_merge_false(self):
        commit = CommitInfo(
            sha="abc", short_sha="abc", message="feat: add feature",
            author="Alice", author_email="a@b.com", date=datetime.now(),
        )
        assert commit.is_merge is False

    def test_immutable(self):
        commit = CommitInfo(
            sha="abc", short_sha="abc", message="msg",
            author="A", author_email="a@b.com", date=datetime.now(),
        )
        with pytest.raises((AttributeError, TypeError)):
            commit.sha = "xyz"


class TestFileHistory:
    def test_churn_calculation(self, sample_file_history):
        assert sample_file_history.churn == sample_file_history.total_insertions + sample_file_history.total_deletions

    def test_age_days_with_first_commit(self, sample_file_history):
        age = sample_file_history.age_days
        assert age is not None
        assert age > 0

    def test_age_days_none_when_no_first_commit(self):
        history = FileHistory(
            path="empty.py",
            commits=[],
            total_insertions=0,
            total_deletions=0,
            first_commit=None,
            last_commit=None,
            unique_authors=[],
        )
        assert history.age_days is None

    def test_immutable(self, sample_file_history):
        with pytest.raises((AttributeError, TypeError)):
            sample_file_history.path = "other.py"


class TestRepoSummary:
    def test_age_days_with_first_commit(self, sample_repo_summary):
        age = sample_repo_summary.age_days
        assert age is not None
        assert age > 0

    def test_age_days_none_without_commit(self):
        summary = RepoSummary(
            path="/fake",
            total_commits=0,
            total_authors=[],
            first_commit=None,
            last_commit=None,
        )
        assert summary.age_days is None


class TestStoryConfig:
    def test_defaults(self):
        config = StoryConfig()
        assert config.mode == StoryMode.REPO
        assert config.style == StoryStyle.NARRATIVE
        assert config.max_commits == 100
        assert config.provider == "claude"
        assert config.plain is False

    def test_immutable(self):
        config = StoryConfig()
        with pytest.raises((AttributeError, TypeError)):
            config.provider = "openai"


class TestGeneratedStory:
    def test_creation(self):
        story = GeneratedStory(
            title="Test Story",
            content="Once upon a time...",
            mode=StoryMode.FILE,
            style=StoryStyle.NARRATIVE,
            commit_count=10,
            author_count=2,
            provider_used="claude (haiku)",
        )
        assert story.title == "Test Story"
        assert story.commit_count == 10


class TestStoryEnums:
    def test_story_mode_values(self):
        assert StoryMode.FILE == "file"
        assert StoryMode.REPO == "repo"
        assert StoryMode.AUTHOR == "author"
        assert StoryMode.RANGE == "range"

    def test_story_style_values(self):
        assert StoryStyle.NARRATIVE == "narrative"
        assert StoryStyle.TIMELINE == "timeline"
        assert StoryStyle.DETECTIVE == "detective"
