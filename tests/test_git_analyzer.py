"""Tests for chronicle.git_analyzer."""

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from chronicle.git_analyzer import (
    analyze_author,
    analyze_file,
    analyze_repo,
    get_commits,
    get_repo,
    parse_since_string,
)


class TestParseSinceString:
    def test_none_returns_none(self):
        assert parse_since_string(None) is None

    def test_1_day_ago(self):
        result = parse_since_string("1 day ago")
        assert result is not None
        now = datetime.now()
        expected = datetime.now() - timedelta(days=1)
        assert abs((expected - result).total_seconds()) < 60

    def test_7_days_ago(self):
        result = parse_since_string("7 days ago")
        assert result is not None
        expected = datetime.now() - timedelta(days=7)
        assert abs((expected - result).total_seconds()) < 60

    def test_2_weeks_ago(self):
        result = parse_since_string("2 weeks ago")
        assert result is not None
        expected = datetime.now() - timedelta(weeks=2)
        assert abs((expected - result).total_seconds()) < 60

    def test_3_months_ago(self):
        result = parse_since_string("3 months ago")
        assert result is not None
        expected = datetime.now() - timedelta(days=90)
        assert abs((expected - result).total_seconds()) < 3600

    def test_1_year_ago(self):
        result = parse_since_string("1 year ago")
        assert result is not None
        expected = datetime.now() - timedelta(days=365)
        assert abs((expected - result).total_seconds()) < 3600

    def test_iso_date_format(self):
        result = parse_since_string("2024-01-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_slash_date_format(self):
        result = parse_since_string("2024/06/01")
        assert result is not None
        assert result.year == 2024

    def test_invalid_string_returns_none(self):
        result = parse_since_string("not-a-date")
        assert result is None

    def test_singular_day(self):
        result = parse_since_string("1 day ago")
        assert result is not None

    def test_plural_months(self):
        result = parse_since_string("6 months ago")
        assert result is not None


class TestGetRepo:
    def test_valid_repo(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        assert repo is not None

    def test_invalid_path_raises(self, tmp_path):
        not_a_repo = tmp_path / "not_a_repo"
        not_a_repo.mkdir()
        with pytest.raises(ValueError, match="Not a git repository"):
            get_repo(str(not_a_repo))

    def test_nonexistent_path_raises(self):
        with pytest.raises(ValueError):
            get_repo("/nonexistent/path/that/does/not/exist")


class TestGetCommits:
    def test_returns_commits(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        commits = get_commits(repo, max_commits=10)
        assert len(commits) >= 3

    def test_max_commits_respected(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        commits = get_commits(repo, max_commits=1)
        assert len(commits) == 1

    def test_commit_fields_populated(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        commits = get_commits(repo, max_commits=5)
        commit = commits[0]
        assert commit.sha
        assert commit.short_sha
        assert len(commit.short_sha) == 7
        assert commit.message
        assert commit.author
        assert commit.date

    def test_since_filter(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        # Future date should return no commits
        future = datetime.now() + timedelta(days=1)
        commits = get_commits(repo, since=future, max_commits=10)
        assert len(commits) == 0

    def test_author_filter(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        commits = get_commits(repo, author="Test User", max_commits=10)
        assert len(commits) >= 1
        for commit in commits:
            assert "Test" in commit.author or "test" in commit.author_email

    def test_empty_repo_returns_empty_list(self, tmp_path):
        empty_repo = tmp_path / "empty"
        empty_repo.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=empty_repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "x@x.com"], cwd=empty_repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "X"], cwd=empty_repo, capture_output=True)
        repo = get_repo(str(empty_repo))
        commits = get_commits(repo)
        assert commits == []


class TestAnalyzeFile:
    def test_returns_file_history(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        history = analyze_file(repo, "auth.py", max_commits=10)
        assert history.path == "auth.py"
        assert len(history.commits) >= 2

    def test_unique_authors_populated(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        history = analyze_file(repo, "auth.py", max_commits=10)
        assert len(history.unique_authors) >= 1

    def test_nonexistent_file_returns_empty(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        history = analyze_file(repo, "nonexistent_file.py", max_commits=10)
        assert history.commits == []
        assert history.first_commit is None

    def test_first_and_last_commit(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        history = analyze_file(repo, "auth.py", max_commits=10)
        if history.commits:
            assert history.first_commit is not None
            assert history.last_commit is not None


class TestAnalyzeRepo:
    def test_returns_repo_summary(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        summary = analyze_repo(repo, max_commits=10)
        assert summary.total_commits >= 3
        assert len(summary.total_authors) >= 1

    def test_most_changed_files_populated(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        summary = analyze_repo(repo, max_commits=10)
        assert isinstance(summary.most_changed_files, list)

    def test_commits_list_populated(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        summary = analyze_repo(repo, max_commits=10)
        assert len(summary.commits) >= 3

    def test_empty_repo_returns_empty_summary(self, tmp_path):
        empty_repo = tmp_path / "empty2"
        empty_repo.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=empty_repo, capture_output=True)
        subprocess.run(["git", "config", "user.email", "x@x.com"], cwd=empty_repo, capture_output=True)
        subprocess.run(["git", "config", "user.name", "X"], cwd=empty_repo, capture_output=True)
        repo = get_repo(str(empty_repo))
        summary = analyze_repo(repo, max_commits=10)
        assert summary.total_commits == 0
        assert summary.first_commit is None


class TestAnalyzeAuthor:
    def test_returns_author_commits(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        commits, most_changed = analyze_author(repo, "Test User", max_commits=10)
        assert len(commits) >= 1

    def test_unknown_author_returns_empty(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        commits, most_changed = analyze_author(repo, "Unknown Author XYZ", max_commits=10)
        assert len(commits) == 0
        assert most_changed == []

    def test_most_changed_files_populated(self, temp_git_repo):
        repo = get_repo(str(temp_git_repo))
        commits, most_changed = analyze_author(repo, "Test User", max_commits=10)
        assert isinstance(most_changed, list)
