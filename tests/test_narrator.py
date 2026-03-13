"""Tests for chronicle.narrator."""

from unittest.mock import MagicMock

import pytest

from chronicle.models import (
    StoryConfig,
    StoryMode,
    StoryStyle,
)
from chronicle.narrator import (
    _format_commits_for_prompt,
    narrate_author,
    narrate_file,
    narrate_range,
    narrate_repo,
)


class TestFormatCommitsForPrompt:
    def test_formats_commits(self, sample_commits):
        result = _format_commits_for_prompt(sample_commits)
        assert "Alice" in result
        assert "Bob" in result
        assert "2024-01-01" in result

    def test_respects_limit(self, sample_commits):
        result = _format_commits_for_prompt(sample_commits, limit=1)
        # Only first commit should be included
        lines = [l for l in result.strip().split("\n") if l.strip()]
        assert len(lines) == 1

    def test_truncates_many_files(self, sample_commits):
        from chronicle.models import CommitInfo
        from datetime import datetime
        commit = CommitInfo(
            sha="abc", short_sha="abc1234", message="feat: big change",
            author="Alice", author_email="a@b.com",
            date=datetime(2024, 1, 1),
            files_changed=[f"file{i}.py" for i in range(10)],
        )
        result = _format_commits_for_prompt([commit])
        assert "+5 more" in result

    def test_empty_list_returns_empty(self):
        result = _format_commits_for_prompt([])
        assert result == ""


class TestNarrateFile:
    def test_returns_story(self, sample_file_history, mock_provider):
        config = StoryConfig(mode=StoryMode.FILE, style=StoryStyle.NARRATIVE)
        story = narrate_file(sample_file_history, config, mock_provider)
        assert story.mode == StoryMode.FILE
        assert story.style == StoryStyle.NARRATIVE
        assert story.title.startswith("The Story of")
        assert story.content
        assert mock_provider.complete.called

    def test_commit_count_in_story(self, sample_file_history, mock_provider):
        config = StoryConfig(mode=StoryMode.FILE, style=StoryStyle.NARRATIVE)
        story = narrate_file(sample_file_history, config, mock_provider)
        assert story.commit_count == len(sample_file_history.commits)

    def test_author_count_in_story(self, sample_file_history, mock_provider):
        config = StoryConfig(mode=StoryMode.FILE, style=StoryStyle.NARRATIVE)
        story = narrate_file(sample_file_history, config, mock_provider)
        assert story.author_count == len(sample_file_history.unique_authors)

    def test_provider_name_in_story(self, sample_file_history, mock_provider):
        config = StoryConfig(mode=StoryMode.FILE, style=StoryStyle.NARRATIVE)
        story = narrate_file(sample_file_history, config, mock_provider)
        assert story.provider_used == mock_provider.name

    def test_timeline_style(self, sample_file_history, mock_provider):
        config = StoryConfig(mode=StoryMode.FILE, style=StoryStyle.TIMELINE)
        story = narrate_file(sample_file_history, config, mock_provider)
        prompt_call = mock_provider.complete.call_args
        assert "timeline" in prompt_call[0][0].lower() or "timeline" in prompt_call[1].get("system", "").lower()

    def test_detective_style(self, sample_file_history, mock_provider):
        config = StoryConfig(mode=StoryMode.FILE, style=StoryStyle.DETECTIVE)
        story = narrate_file(sample_file_history, config, mock_provider)
        assert story.style == StoryStyle.DETECTIVE

    def test_file_path_in_title(self, sample_file_history, mock_provider):
        config = StoryConfig(mode=StoryMode.FILE, style=StoryStyle.NARRATIVE)
        story = narrate_file(sample_file_history, config, mock_provider)
        assert sample_file_history.path in story.title


class TestNarrateRepo:
    def test_returns_story(self, sample_repo_summary, mock_provider):
        config = StoryConfig(mode=StoryMode.REPO, style=StoryStyle.NARRATIVE)
        story = narrate_repo(sample_repo_summary, config, mock_provider)
        assert story.mode == StoryMode.REPO
        assert story.content

    def test_commit_count_in_story(self, sample_repo_summary, mock_provider):
        config = StoryConfig(mode=StoryMode.REPO, style=StoryStyle.NARRATIVE)
        story = narrate_repo(sample_repo_summary, config, mock_provider)
        assert story.commit_count == sample_repo_summary.total_commits

    def test_author_count_in_story(self, sample_repo_summary, mock_provider):
        config = StoryConfig(mode=StoryMode.REPO, style=StoryStyle.NARRATIVE)
        story = narrate_repo(sample_repo_summary, config, mock_provider)
        assert story.author_count == len(sample_repo_summary.total_authors)

    def test_timeline_style(self, sample_repo_summary, mock_provider):
        config = StoryConfig(mode=StoryMode.REPO, style=StoryStyle.TIMELINE)
        story = narrate_repo(sample_repo_summary, config, mock_provider)
        assert story.style == StoryStyle.TIMELINE


class TestNarrateAuthor:
    def test_returns_story(self, sample_commits, mock_provider):
        config = StoryConfig(mode=StoryMode.AUTHOR, style=StoryStyle.NARRATIVE)
        story = narrate_author("Alice", sample_commits, ["src/auth.py"], config, mock_provider)
        assert story.mode == StoryMode.AUTHOR
        assert "Alice" in story.title
        assert story.content

    def test_commit_count(self, sample_commits, mock_provider):
        config = StoryConfig(mode=StoryMode.AUTHOR, style=StoryStyle.NARRATIVE)
        story = narrate_author("Alice", sample_commits, [], config, mock_provider)
        assert story.commit_count == len(sample_commits)

    def test_empty_commits(self, mock_provider):
        config = StoryConfig(mode=StoryMode.AUTHOR, style=StoryStyle.NARRATIVE)
        story = narrate_author("Ghost", [], [], config, mock_provider)
        assert story.commit_count == 0
        assert mock_provider.complete.called


class TestNarrateRange:
    def test_returns_story(self, sample_commits, mock_provider):
        config = StoryConfig(mode=StoryMode.RANGE, style=StoryStyle.NARRATIVE)
        story = narrate_range(sample_commits, "v1.0..v2.0", config, mock_provider)
        assert story.mode == StoryMode.RANGE
        assert "v1.0..v2.0" in story.title
        assert story.content

    def test_commit_count(self, sample_commits, mock_provider):
        config = StoryConfig(mode=StoryMode.RANGE, style=StoryStyle.NARRATIVE)
        story = narrate_range(sample_commits, "v1.0..v2.0", config, mock_provider)
        assert story.commit_count == len(sample_commits)

    def test_unique_authors_calculated(self, sample_commits, mock_provider):
        config = StoryConfig(mode=StoryMode.RANGE, style=StoryStyle.NARRATIVE)
        story = narrate_range(sample_commits, "HEAD~3..HEAD", config, mock_provider)
        # sample_commits has Alice and Bob
        assert story.author_count == 2

    def test_empty_range(self, mock_provider):
        config = StoryConfig(mode=StoryMode.RANGE, style=StoryStyle.NARRATIVE)
        story = narrate_range([], "v1.0..v2.0", config, mock_provider)
        assert story.commit_count == 0
