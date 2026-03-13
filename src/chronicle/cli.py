"""CLI entry point for chronicle-ai."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .git_analyzer import (
    analyze_author,
    analyze_file,
    analyze_repo,
    get_commits,
    get_repo,
    parse_since_string,
)
from .models import StoryConfig, StoryMode, StoryStyle
from .narrator import narrate_author, narrate_file, narrate_range, narrate_repo
from .providers import get_provider
from .providers.base import ProviderError

console = Console()
err_console = Console(stderr=True, style="bold red")


def _print_story(story, plain: bool) -> None:
    """Print the generated story to stdout."""
    if plain:
        print(f"# {story.title}\n")
        print(story.content)
        return

    console.print()
    console.print(
        Panel(
            f"[bold cyan]{story.title}[/bold cyan]\n"
            f"[dim]{story.commit_count} commits · "
            f"{story.author_count} contributor(s) · "
            f"via {story.provider_used}[/dim]",
            border_style="blue",
        )
    )
    console.print()
    console.print(Markdown(story.content))
    console.print()


@click.group()
@click.version_option(__version__, "--version", "-V")
def main():
    """chronicle-ai — AI-powered git history narrator.

    Turn your git log into engaging stories.

    \b
    Examples:
      chronicle file src/auth.py          # Story about a file
      chronicle repo                      # Story about the whole repo
      chronicle author "Alice"            # Story about a contributor
      chronicle range v1.0..v2.0         # Story between two versions
    """


@main.command()
@click.argument("file_path")
@click.option("--repo", "-r", default=".", help="Path to the git repository.")
@click.option(
    "--style",
    "-s",
    type=click.Choice(["narrative", "timeline", "detective"]),
    default="narrative",
    help="Story style. [default: narrative]",
)
@click.option("--since", help="Only include commits after this date (e.g. '6 months ago', '2024-01-01').")
@click.option("--max-commits", default=100, show_default=True, help="Maximum commits to analyze.")
@click.option("--provider", "-p", default="claude", show_default=True, help="LLM provider: claude, openai, ollama.")
@click.option("--model", "-m", default=None, help="Override the default model for the provider.")
@click.option("--plain", is_flag=True, help="Plain text output (no Rich formatting).")
def file(file_path, repo, style, since, max_commits, provider, model, plain):
    """Tell the story of a FILE's evolution through git history."""
    try:
        git_repo = get_repo(repo)
    except ValueError as e:
        err_console.print(f"Error: {e}")
        sys.exit(1)

    since_dt = parse_since_string(since)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(f"Analyzing git history of {file_path}...", total=None)
        history = analyze_file(git_repo, file_path, since=since_dt, max_commits=max_commits)

    if not history.commits:
        err_console.print(
            f"No commits found for '{file_path}'. "
            "Check the path and try --since to adjust the date range."
        )
        sys.exit(1)

    config = StoryConfig(
        mode=StoryMode.FILE,
        style=StoryStyle(style),
        target=file_path,
        since=since,
        max_commits=max_commits,
        provider=provider,
        model=model,
        plain=plain,
    )

    try:
        llm = get_provider(provider, model)
    except ValueError as e:
        err_console.print(f"Error: {e}")
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Generating story...", total=None)
        try:
            story = narrate_file(history, config, llm)
        except ProviderError as e:
            err_console.print(f"LLM error: {e}")
            sys.exit(1)

    _print_story(story, plain)


@main.command()
@click.option("--repo", "-r", default=".", help="Path to the git repository.")
@click.option(
    "--style",
    "-s",
    type=click.Choice(["narrative", "timeline", "detective"]),
    default="narrative",
    help="Story style. [default: narrative]",
)
@click.option("--since", help="Only include commits after this date.")
@click.option("--until", help="Only include commits up to this ref (tag, branch, commit SHA).")
@click.option("--max-commits", default=200, show_default=True, help="Maximum commits to analyze.")
@click.option("--provider", "-p", default="claude", show_default=True, help="LLM provider.")
@click.option("--model", "-m", default=None, help="Override the default model.")
@click.option("--plain", is_flag=True, help="Plain text output.")
def repo(repo, style, since, until, max_commits, provider, model, plain):
    """Tell the story of the entire repository's evolution."""
    try:
        git_repo = get_repo(repo)
    except ValueError as e:
        err_console.print(f"Error: {e}")
        sys.exit(1)

    since_dt = parse_since_string(since)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Analyzing repository history...", total=None)
        summary = analyze_repo(git_repo, since=since_dt, until=until, max_commits=max_commits)

    if summary.total_commits == 0:
        err_console.print(
            "No commits found. Check your date range or ensure the repo has commits."
        )
        sys.exit(1)

    config = StoryConfig(
        mode=StoryMode.REPO,
        style=StoryStyle(style),
        since=since,
        until=until,
        max_commits=max_commits,
        provider=provider,
        model=model,
        plain=plain,
    )

    try:
        llm = get_provider(provider, model)
    except ValueError as e:
        err_console.print(f"Error: {e}")
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Generating story...", total=None)
        try:
            story = narrate_repo(summary, config, llm)
        except ProviderError as e:
            err_console.print(f"LLM error: {e}")
            sys.exit(1)

    _print_story(story, plain)


@main.command()
@click.argument("author_name")
@click.option("--repo", "-r", default=".", help="Path to the git repository.")
@click.option(
    "--style",
    "-s",
    type=click.Choice(["narrative", "timeline", "detective"]),
    default="narrative",
    help="Story style.",
)
@click.option("--since", help="Only include commits after this date.")
@click.option("--max-commits", default=200, show_default=True, help="Maximum commits to analyze.")
@click.option("--provider", "-p", default="claude", show_default=True, help="LLM provider.")
@click.option("--model", "-m", default=None, help="Override the default model.")
@click.option("--plain", is_flag=True, help="Plain text output.")
def author(author_name, repo, style, since, max_commits, provider, model, plain):
    """Tell the story of an AUTHOR's contributions to the repository."""
    try:
        git_repo = get_repo(repo)
    except ValueError as e:
        err_console.print(f"Error: {e}")
        sys.exit(1)

    since_dt = parse_since_string(since)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(f"Finding commits by '{author_name}'...", total=None)
        commits, most_changed = analyze_author(
            git_repo, author_name, since=since_dt, max_commits=max_commits
        )

    if not commits:
        err_console.print(
            f"No commits found for author '{author_name}'. "
            "Try a partial name or email address."
        )
        sys.exit(1)

    config = StoryConfig(
        mode=StoryMode.AUTHOR,
        style=StoryStyle(style),
        target=author_name,
        since=since,
        max_commits=max_commits,
        provider=provider,
        model=model,
        plain=plain,
    )

    try:
        llm = get_provider(provider, model)
    except ValueError as e:
        err_console.print(f"Error: {e}")
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Generating story...", total=None)
        try:
            story = narrate_author(author_name, commits, most_changed, config, llm)
        except ProviderError as e:
            err_console.print(f"LLM error: {e}")
            sys.exit(1)

    _print_story(story, plain)


@main.command(name="range")
@click.argument("ref_range")
@click.option("--repo", "-r", default=".", help="Path to the git repository.")
@click.option(
    "--style",
    "-s",
    type=click.Choice(["narrative", "timeline", "detective"]),
    default="narrative",
    help="Story style.",
)
@click.option("--max-commits", default=200, show_default=True, help="Maximum commits to analyze.")
@click.option("--provider", "-p", default="claude", show_default=True, help="LLM provider.")
@click.option("--model", "-m", default=None, help="Override the default model.")
@click.option("--plain", is_flag=True, help="Plain text output.")
def range_cmd(ref_range, repo, style, max_commits, provider, model, plain):
    """Tell the story of changes within a REF_RANGE (e.g., v1.0..v2.0 or main..HEAD)."""
    try:
        git_repo = get_repo(repo)
    except ValueError as e:
        err_console.print(f"Error: {e}")
        sys.exit(1)

    # Parse the range: "v1.0..v2.0" → until="v2.0", analyze commits from v1.0
    parts = ref_range.split("..")
    if len(parts) == 2:
        base_ref, head_ref = parts
        until = head_ref if head_ref else "HEAD"
    else:
        base_ref = None
        until = ref_range

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(f"Analyzing commits in range {ref_range}...", total=None)
        try:
            if base_ref:
                commits = get_commits(
                    git_repo,
                    until=until,
                    max_commits=max_commits,
                )
                # Filter to only commits reachable from until but not from base_ref
                try:
                    base_commits_shas = {
                        c.hexsha for c in git_repo.iter_commits(base_ref, max_count=1000)
                    }
                    from .git_analyzer import _build_commit_info
                    filtered = []
                    for raw_commit in git_repo.iter_commits(until, max_count=max_commits):
                        if raw_commit.hexsha in base_commits_shas:
                            break
                        filtered.append(_build_commit_info(raw_commit))
                    commits = filtered
                except Exception:
                    pass
            else:
                commits = get_commits(git_repo, until=until, max_commits=max_commits)
        except Exception as e:
            err_console.print(f"Git error: {e}")
            sys.exit(1)

    if not commits:
        err_console.print(f"No commits found in range '{ref_range}'.")
        sys.exit(1)

    config = StoryConfig(
        mode=StoryMode.RANGE,
        style=StoryStyle(style),
        target=ref_range,
        max_commits=max_commits,
        provider=provider,
        model=model,
        plain=plain,
    )

    try:
        llm = get_provider(provider, model)
    except ValueError as e:
        err_console.print(f"Error: {e}")
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Generating story...", total=None)
        try:
            story = narrate_range(commits, ref_range, config, llm)
        except ProviderError as e:
            err_console.print(f"LLM error: {e}")
            sys.exit(1)

    _print_story(story, plain)
