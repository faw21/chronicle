"""Shared fixtures for chronicle-ai tests."""

import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from chronicle.models import CommitInfo, FileHistory, RepoSummary, StoryMode, StoryStyle


def make_commit_info(
    sha="abc1234def5678",
    short_sha="abc1234",
    message="feat: add awesome feature",
    author="Alice",
    author_email="alice@example.com",
    date=None,
    files_changed=None,
    insertions=10,
    deletions=5,
):
    return CommitInfo(
        sha=sha,
        short_sha=short_sha,
        message=message,
        author=author,
        author_email=author_email,
        date=date or datetime(2024, 6, 15, 12, 0, 0),
        files_changed=files_changed or ["src/auth.py"],
        insertions=insertions,
        deletions=deletions,
    )


@pytest.fixture
def sample_commit():
    return make_commit_info()


@pytest.fixture
def sample_commits():
    return [
        make_commit_info(
            sha="aaa0000111",
            short_sha="aaa0000",
            message="feat: initial commit",
            author="Alice",
            date=datetime(2024, 1, 1, 10, 0, 0),
            files_changed=["src/main.py", "README.md"],
            insertions=100,
            deletions=0,
        ),
        make_commit_info(
            sha="bbb1111222",
            short_sha="bbb1111",
            message="fix: resolve auth bug\n\nLong description here.",
            author="Bob",
            date=datetime(2024, 3, 15, 14, 30, 0),
            files_changed=["src/auth.py"],
            insertions=20,
            deletions=5,
        ),
        make_commit_info(
            sha="ccc2222333",
            short_sha="ccc2222",
            message="refactor: extract auth module",
            author="Alice",
            date=datetime(2024, 6, 1, 9, 0, 0),
            files_changed=["src/auth.py", "src/utils.py"],
            insertions=50,
            deletions=30,
        ),
    ]


@pytest.fixture
def sample_file_history(sample_commits):
    return FileHistory(
        path="src/auth.py",
        commits=sample_commits,
        total_insertions=170,
        total_deletions=35,
        first_commit=sample_commits[-1],
        last_commit=sample_commits[0],
        unique_authors=["Alice", "Bob"],
    )


@pytest.fixture
def sample_repo_summary(sample_commits):
    return RepoSummary(
        path="/fake/repo",
        total_commits=3,
        total_authors=["Alice", "Bob"],
        first_commit=sample_commits[-1],
        last_commit=sample_commits[0],
        most_changed_files=["src/auth.py", "src/main.py"],
        commits=sample_commits,
    )


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.name = "mock (test-model)"
    provider.complete.return_value = (
        "## The Story\n\nThis is a generated story about the code evolution."
    )
    return provider


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repo with some commits."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    env = {**os.environ, "GIT_AUTHOR_NAME": "Test User", "GIT_AUTHOR_EMAIL": "test@example.com",
           "GIT_COMMITTER_NAME": "Test User", "GIT_COMMITTER_EMAIL": "test@example.com"}

    subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, capture_output=True, env=env)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, capture_output=True)

    # First commit
    (repo_dir / "main.py").write_text("print('hello')\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: initial commit"], cwd=repo_dir,
                   capture_output=True, env=env)

    # Second commit
    (repo_dir / "auth.py").write_text("def authenticate(): pass\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: add authentication"], cwd=repo_dir,
                   capture_output=True, env=env)

    # Third commit
    (repo_dir / "auth.py").write_text("def authenticate():\n    return True\n")
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "fix: implement authentication"], cwd=repo_dir,
                   capture_output=True, env=env)

    return repo_dir
