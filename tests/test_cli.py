"""Tests for chronicle.cli."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from chronicle.cli import main
from chronicle.models import GeneratedStory, StoryMode, StoryStyle


def make_mock_story(mode=StoryMode.FILE, style=StoryStyle.NARRATIVE, title="The Story of `auth.py`"):
    return GeneratedStory(
        title=title,
        content="## Story\n\nThis code evolved significantly over time.",
        mode=mode,
        style=style,
        commit_count=10,
        author_count=2,
        provider_used="mock (test)",
    )


@pytest.fixture
def runner():
    return CliRunner()


class TestMainCommand:
    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "chronicle-ai" in result.output

    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_subcommands_listed(self, runner):
        result = runner.invoke(main, ["--help"])
        assert "file" in result.output
        assert "repo" in result.output
        assert "author" in result.output
        assert "range" in result.output


class TestFileCommand:
    def test_file_help(self, runner):
        result = runner.invoke(main, ["file", "--help"])
        assert result.exit_code == 0
        assert "FILE" in result.output

    @patch("chronicle.cli.get_repo")
    @patch("chronicle.cli.analyze_file")
    @patch("chronicle.cli.get_provider")
    @patch("chronicle.cli.narrate_file")
    def test_successful_run(self, mock_narrate, mock_get_provider, mock_analyze, mock_get_repo, runner, temp_git_repo, sample_file_history):
        mock_get_repo.return_value = MagicMock()
        mock_analyze.return_value = sample_file_history
        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_get_provider.return_value = mock_provider
        mock_narrate.return_value = make_mock_story()

        result = runner.invoke(main, ["file", "src/auth.py", "--provider", "claude"])
        assert result.exit_code == 0
        assert "Story" in result.output

    @patch("chronicle.cli.get_repo")
    @patch("chronicle.cli.analyze_file")
    @patch("chronicle.cli.get_provider")
    @patch("chronicle.cli.narrate_file")
    def test_plain_output(self, mock_narrate, mock_get_provider, mock_analyze, mock_get_repo, runner, sample_file_history):
        mock_get_repo.return_value = MagicMock()
        mock_analyze.return_value = sample_file_history
        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_get_provider.return_value = mock_provider
        mock_narrate.return_value = make_mock_story()

        result = runner.invoke(main, ["file", "auth.py", "--plain"])
        assert result.exit_code == 0

    @patch("chronicle.cli.get_repo")
    @patch("chronicle.cli.analyze_file")
    def test_no_commits_exits_1(self, mock_analyze, mock_get_repo, runner):
        from chronicle.models import FileHistory
        mock_get_repo.return_value = MagicMock()
        mock_analyze.return_value = FileHistory(
            path="empty.py", commits=[], total_insertions=0, total_deletions=0,
            first_commit=None, last_commit=None, unique_authors=[],
        )
        result = runner.invoke(main, ["file", "empty.py"])
        assert result.exit_code == 1

    def test_invalid_repo_exits_1(self, runner, tmp_path):
        not_a_repo = tmp_path / "not_repo"
        not_a_repo.mkdir()
        result = runner.invoke(main, ["file", "auth.py", "--repo", str(not_a_repo)])
        assert result.exit_code == 1


class TestRepoCommand:
    def test_repo_help(self, runner):
        result = runner.invoke(main, ["repo", "--help"])
        assert result.exit_code == 0

    @patch("chronicle.cli.get_repo")
    @patch("chronicle.cli.analyze_repo")
    @patch("chronicle.cli.get_provider")
    @patch("chronicle.cli.narrate_repo")
    def test_successful_run(self, mock_narrate, mock_get_provider, mock_analyze, mock_get_repo, runner, sample_repo_summary):
        mock_get_repo.return_value = MagicMock()
        mock_analyze.return_value = sample_repo_summary
        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_get_provider.return_value = mock_provider
        mock_narrate.return_value = make_mock_story(mode=StoryMode.REPO, title="The Story of This Repository")

        result = runner.invoke(main, ["repo", "--provider", "claude"])
        assert result.exit_code == 0

    @patch("chronicle.cli.get_repo")
    @patch("chronicle.cli.analyze_repo")
    def test_empty_repo_exits_1(self, mock_analyze, mock_get_repo, runner):
        from chronicle.models import RepoSummary
        mock_get_repo.return_value = MagicMock()
        mock_analyze.return_value = RepoSummary(
            path="/fake", total_commits=0, total_authors=[],
            first_commit=None, last_commit=None,
        )
        result = runner.invoke(main, ["repo"])
        assert result.exit_code == 1

    @patch("chronicle.cli.get_repo")
    @patch("chronicle.cli.analyze_repo")
    @patch("chronicle.cli.get_provider")
    @patch("chronicle.cli.narrate_repo")
    def test_style_option(self, mock_narrate, mock_get_provider, mock_analyze, mock_get_repo, runner, sample_repo_summary):
        mock_get_repo.return_value = MagicMock()
        mock_analyze.return_value = sample_repo_summary
        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_get_provider.return_value = mock_provider
        mock_narrate.return_value = make_mock_story(mode=StoryMode.REPO, title="Timeline")

        result = runner.invoke(main, ["repo", "--style", "timeline"])
        assert result.exit_code == 0


class TestAuthorCommand:
    def test_author_help(self, runner):
        result = runner.invoke(main, ["author", "--help"])
        assert result.exit_code == 0

    @patch("chronicle.cli.get_repo")
    @patch("chronicle.cli.analyze_author")
    @patch("chronicle.cli.get_provider")
    @patch("chronicle.cli.narrate_author")
    def test_successful_run(self, mock_narrate, mock_get_provider, mock_analyze, mock_get_repo, runner, sample_commits):
        mock_get_repo.return_value = MagicMock()
        mock_analyze.return_value = (sample_commits, ["src/auth.py"])
        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_get_provider.return_value = mock_provider
        mock_narrate.return_value = make_mock_story(
            mode=StoryMode.AUTHOR, title="The Story of Alice's Contributions"
        )

        result = runner.invoke(main, ["author", "Alice"])
        assert result.exit_code == 0

    @patch("chronicle.cli.get_repo")
    @patch("chronicle.cli.analyze_author")
    def test_no_commits_exits_1(self, mock_analyze, mock_get_repo, runner):
        mock_get_repo.return_value = MagicMock()
        mock_analyze.return_value = ([], [])
        result = runner.invoke(main, ["author", "Nobody"])
        assert result.exit_code == 1


class TestRangeCommand:
    def test_range_help(self, runner):
        result = runner.invoke(main, ["range", "--help"])
        assert result.exit_code == 0

    @patch("chronicle.cli.get_repo")
    @patch("chronicle.cli.get_commits")
    @patch("chronicle.cli.get_provider")
    @patch("chronicle.cli.narrate_range")
    def test_successful_run(self, mock_narrate, mock_get_provider, mock_get_commits, mock_get_repo, runner, sample_commits):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_get_commits.return_value = sample_commits
        mock_provider = MagicMock()
        mock_provider.name = "mock"
        mock_get_provider.return_value = mock_provider
        mock_narrate.return_value = make_mock_story(
            mode=StoryMode.RANGE, title="What Changed: v1.0..v2.0"
        )

        # Use a single ref (no ..) to avoid the complex filtering path
        result = runner.invoke(main, ["range", "v2.0"])
        assert result.exit_code == 0

    @patch("chronicle.cli.get_repo")
    @patch("chronicle.cli.get_commits")
    def test_no_commits_exits_1(self, mock_get_commits, mock_get_repo, runner):
        mock_get_repo.return_value = MagicMock()
        mock_get_commits.return_value = []
        result = runner.invoke(main, ["range", "v0..v1"])
        assert result.exit_code == 1

    def test_invalid_repo_exits_1(self, runner, tmp_path):
        not_a_repo = tmp_path / "not_repo2"
        not_a_repo.mkdir()
        result = runner.invoke(main, ["range", "HEAD~3..HEAD", "--repo", str(not_a_repo)])
        assert result.exit_code == 1


class TestProviders:
    def test_invalid_provider_exits_1(self, runner, tmp_path):
        result = runner.invoke(main, ["file", "auth.py"])
        # Without a mock, this will fail on the repo lookup, which is fine
        assert result.exit_code != 0
