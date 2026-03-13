"""AI story narrator for chronicle-ai."""

from typing import List, Optional

from .models import (
    CommitInfo,
    FileHistory,
    GeneratedStory,
    RepoSummary,
    StoryConfig,
    StoryMode,
    StoryStyle,
)
from .providers.base import BaseProvider


_SYSTEM_NARRATIVE = """You are a technical historian and storyteller.
You analyze git commit histories and turn them into engaging, human-readable narratives.
Write in a clear, engaging style — like a well-written engineering blog post or postmortem.
Focus on the WHY, not just the WHAT. Highlight turning points, interesting decisions, and context.
Keep it concise but informative. Use Markdown formatting."""

_SYSTEM_TIMELINE = """You are a technical documentation writer.
You analyze git commit histories and create clear, structured timelines.
Use Markdown with dates, bullet points, and headings.
Focus on significant events: major features, breaking changes, bug fixes, refactors.
Be concise and factual."""

_SYSTEM_DETECTIVE = """You are a code archaeologist investigating the evolution of a codebase.
Your job is to answer: WHY does this code exist? What problems was it solving?
Write as if you're explaining the decisions to a new team member.
Look for patterns: What kept changing? What was controversial? What was refactored repeatedly?
Use Markdown formatting."""


def _get_system_prompt(style: StoryStyle) -> str:
    """Get the system prompt for a given story style."""
    if style == StoryStyle.NARRATIVE:
        return _SYSTEM_NARRATIVE
    elif style == StoryStyle.TIMELINE:
        return _SYSTEM_TIMELINE
    elif style == StoryStyle.DETECTIVE:
        return _SYSTEM_DETECTIVE
    return _SYSTEM_NARRATIVE


def _format_commits_for_prompt(commits: List[CommitInfo], limit: int = 80) -> str:
    """Format commits into a compact string for the LLM prompt."""
    lines = []
    for commit in commits[:limit]:
        date_str = commit.date.strftime("%Y-%m-%d")
        files_str = ", ".join(commit.files_changed[:5])
        if len(commit.files_changed) > 5:
            files_str += f" (+{len(commit.files_changed) - 5} more)"
        line = f"- [{date_str}] {commit.short_sha} by {commit.author}: {commit.summary}"
        if files_str:
            line += f" | files: {files_str}"
        lines.append(line)
    return "\n".join(lines)


def narrate_file(
    history: FileHistory,
    config: StoryConfig,
    provider: BaseProvider,
) -> GeneratedStory:
    """Generate a story about a single file's evolution."""
    commits_text = _format_commits_for_prompt(history.commits)

    style_instruction = {
        StoryStyle.NARRATIVE: "Write a flowing narrative about how this file evolved.",
        StoryStyle.TIMELINE: "Create a structured timeline of key changes to this file.",
        StoryStyle.DETECTIVE: "Investigate why this file changed so much. What does the history reveal?",
    }[config.style]

    prompt = f"""Analyze the git history of the file `{history.path}` and {style_instruction}

## File Statistics
- Total commits: {len(history.commits)}
- First appearance: {history.first_commit.date.strftime('%Y-%m-%d') if history.first_commit else 'unknown'}
- Last changed: {history.last_commit.date.strftime('%Y-%m-%d') if history.last_commit else 'unknown'}
- Total lines added: {history.total_insertions}
- Total lines removed: {history.total_deletions}
- Contributors: {', '.join(history.unique_authors) if history.unique_authors else 'unknown'}

## Commit History
{commits_text if commits_text else 'No commits found in the given range.'}

Write the story now. Keep it under 400 words unless the history is very complex."""

    content = provider.complete(prompt, system=_get_system_prompt(config.style))

    return GeneratedStory(
        title=f"The Story of `{history.path}`",
        content=content,
        mode=StoryMode.FILE,
        style=config.style,
        commit_count=len(history.commits),
        author_count=len(history.unique_authors),
        provider_used=provider.name,
    )


def narrate_repo(
    summary: RepoSummary,
    config: StoryConfig,
    provider: BaseProvider,
) -> GeneratedStory:
    """Generate a story about the entire repo's evolution."""
    commits_text = _format_commits_for_prompt(summary.commits)

    style_instruction = {
        StoryStyle.NARRATIVE: "Write a compelling narrative about how this project evolved.",
        StoryStyle.TIMELINE: "Create a structured timeline of the project's major milestones.",
        StoryStyle.DETECTIVE: "Investigate the project's evolution. What patterns emerge? What was the biggest challenge?",
    }[config.style]

    hotspots = ", ".join(summary.most_changed_files[:5]) if summary.most_changed_files else "none"

    prompt = f"""Analyze this git repository's history and {style_instruction}

## Repository Statistics
- Total commits analyzed: {summary.total_commits}
- Contributors: {', '.join(summary.total_authors[:10])}
- Project age: {summary.age_days} days
- First commit: {summary.first_commit.date.strftime('%Y-%m-%d') if summary.first_commit else 'unknown'}
- Latest commit: {summary.last_commit.date.strftime('%Y-%m-%d') if summary.last_commit else 'unknown'}
- Most frequently changed files: {hotspots}

## Recent Commit History (newest first)
{commits_text if commits_text else 'No commits found in the given range.'}

Write the story now. Keep it under 500 words unless the history is complex."""

    content = provider.complete(prompt, system=_get_system_prompt(config.style))

    return GeneratedStory(
        title="The Story of This Repository",
        content=content,
        mode=StoryMode.REPO,
        style=config.style,
        commit_count=summary.total_commits,
        author_count=len(summary.total_authors),
        provider_used=provider.name,
    )


def narrate_author(
    author: str,
    commits: List[CommitInfo],
    most_changed_files: List[str],
    config: StoryConfig,
    provider: BaseProvider,
) -> GeneratedStory:
    """Generate a story about an author's contributions."""
    commits_text = _format_commits_for_prompt(commits)

    style_instruction = {
        StoryStyle.NARRATIVE: "Write a narrative about this developer's journey and contributions.",
        StoryStyle.TIMELINE: "Create a timeline of this developer's major contributions.",
        StoryStyle.DETECTIVE: "Investigate this developer's impact on the codebase. What can we learn?",
    }[config.style]

    hotspots = ", ".join(most_changed_files[:5]) if most_changed_files else "none"

    date_range = ""
    if commits:
        date_range = f"{commits[-1].date.strftime('%Y-%m-%d')} to {commits[0].date.strftime('%Y-%m-%d')}"

    prompt = f"""Analyze the contributions of developer "{author}" and {style_instruction}

## Contribution Statistics
- Total commits: {len(commits)}
- Period: {date_range}
- Most impacted files: {hotspots}

## Commit History
{commits_text if commits_text else 'No commits found for this author in the given range.'}

Write the story now. Keep it under 400 words."""

    content = provider.complete(prompt, system=_get_system_prompt(config.style))

    return GeneratedStory(
        title=f"The Story of {author}'s Contributions",
        content=content,
        mode=StoryMode.AUTHOR,
        style=config.style,
        commit_count=len(commits),
        author_count=1,
        provider_used=provider.name,
    )


def narrate_range(
    commits: List[CommitInfo],
    ref_range: str,
    config: StoryConfig,
    provider: BaseProvider,
) -> GeneratedStory:
    """Generate a story about changes between two git refs."""
    commits_text = _format_commits_for_prompt(commits)
    unique_authors = list(dict.fromkeys(c.author for c in commits))

    style_instruction = {
        StoryStyle.NARRATIVE: "Write a narrative about what changed between these versions.",
        StoryStyle.TIMELINE: "Create a timeline of changes in this range.",
        StoryStyle.DETECTIVE: "Investigate what happened between these two points. What drove the changes?",
    }[config.style]

    prompt = f"""Analyze the git history for the range "{ref_range}" and {style_instruction}

## Range Statistics
- Total commits: {len(commits)}
- Contributors in this range: {', '.join(unique_authors)}

## Commits (newest first)
{commits_text if commits_text else 'No commits found in this range.'}

Write the story now. This could be a release notes narrative or a sprint retrospective. Keep it under 500 words."""

    content = provider.complete(prompt, system=_get_system_prompt(config.style))

    return GeneratedStory(
        title=f"What Changed: {ref_range}",
        content=content,
        mode=StoryMode.RANGE,
        style=config.style,
        commit_count=len(commits),
        author_count=len(unique_authors),
        provider_used=provider.name,
    )
