# chronicle-ai

> **AI-powered git history narrator.** Turn your `git log` into engaging stories.

[![PyPI version](https://badge.fury.io/py/chronicle-ai.svg)](https://pypi.org/project/chronicle-ai/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

\`\`\`bash
$ chronicle file src/auth.py

╭──────────────────────────────────────────────────────────────╮
│  The Story of `src/auth.py`                                  │
│  47 commits · 3 contributors · via claude (haiku)            │
╰──────────────────────────────────────────────────────────────╯

## The Authentication Module's Journey

This file began as a simple password-checking function in January 2023,
just three lines that returned a boolean. Within weeks, it became the
most-changed file in the repository...
\`\`\`

\`git log\` shows you *what* changed. \`chronicle\` tells you *why*.

---

## Why chronicle?

Every codebase has stories hidden in its git history:
- Why was this module rewritten three times?
- What crisis triggered that 200-line commit at 2 AM?
- Which contributor shaped this file the most?

\`chronicle\` uses AI to read those signals and turn them into narratives that help you understand your codebase — and onboard new engineers — in minutes instead of hours.

---

## Installation

\`\`\`bash
pip install chronicle-ai

# With Anthropic Claude (recommended)
pip install 'chronicle-ai[anthropic]'

# With OpenAI
pip install 'chronicle-ai[openai]'
\`\`\`

No API key? Use Ollama for free local inference:
\`\`\`bash
ollama pull llama3.2
chronicle repo --provider ollama
\`\`\`

---

## Usage

### Tell the story of a file

\`\`\`bash
# Narrative style (default)
chronicle file src/auth.py

# Chronological timeline
chronicle file src/auth.py --style timeline

# Detective mode: WHY did this change so much?
chronicle file src/auth.py --style detective

# Focus on recent changes only
chronicle file src/auth.py --since "6 months ago"
\`\`\`

### Tell the story of your entire repo

\`\`\`bash
chronicle repo

# Between two versions
chronicle repo --since "2024-01-01" --until "v2.0"

# Plain text (pipe-friendly)
chronicle repo --plain > STORY.md
\`\`\`

### Tell the story of a contributor

\`\`\`bash
chronicle author "Alice"
chronicle author "alice@company.com" --style timeline
\`\`\`

### Tell the story between two versions

\`\`\`bash
chronicle range v1.0..v2.0
chronicle range main..HEAD --style detective
\`\`\`

---

## Options

| Option | Description |
|--------|-------------|
| \`--style\` | \`narrative\` (default), \`timeline\`, or \`detective\` |
| \`--since\` | Limit to commits after this date (\`"6 months ago"\`, \`"2024-01-01"\`) |
| \`--until\` | Limit to commits up to this ref (tag, branch, SHA) |
| \`--provider\` | LLM provider: \`claude\` (default), \`openai\`, \`ollama\` |
| \`--model\` | Override the default model |
| \`--max-commits\` | Max commits to analyze (default: 100) |
| \`--plain\` | Plain text output, no Rich formatting |
| \`--repo\` | Path to the git repo (default: current directory) |

---

## Story Styles

| Style | Best for |
|-------|---------|
| \`narrative\` | Understanding the arc of a file or project |
| \`timeline\` | Structured chronological view of changes |
| \`detective\` | Investigating WHY something is the way it is |

---

## LLM Providers

| Provider | Setup | Cost |
|----------|-------|------|
| \`claude\` | \`export ANTHROPIC_API_KEY=...\` | ~$0.001 per story |
| \`openai\` | \`export OPENAI_API_KEY=...\` | ~$0.001 per story |
| \`ollama\` | \`ollama serve\` + \`ollama pull llama3.2\` | Free (local) |

---

## Full Developer Workflow

\`\`\`bash
# Morning: understand what changed
standup-ai ~/work/myapp --yesterday

# Before committing: review your own code
critiq --diff origin/main

# Generate commit message + PR description
gpr --commit-run && gpr --pr

# Understanding a complex file before a PR review
chronicle file src/payments.py --style detective
gitbrief --changed-only --base main | pbcopy

# After releasing: generate changelog
changelog-ai v1.0..v2.0
\`\`\`

**Ecosystem:** [standup-ai](https://github.com/faw21/standup-ai) · [critiq](https://github.com/faw21/critiq) · [gpr](https://github.com/faw21/gpr) · [gitbrief](https://github.com/faw21/gitbrief) · [changelog-ai](https://github.com/faw21/changelog-ai) · [testfix](https://github.com/faw21/testfix) · **chronicle-ai**

---

## How It Works

1. **Analyzes git history**: Uses \`gitpython\` to extract commit messages, authors, file changes, and timestamps
2. **Builds context**: Computes statistics (churn, contributors, hotspot files)
3. **Prompts the LLM**: Sends a structured prompt with the right narrative framing
4. **Returns a story**: Formatted in Markdown, rendered with Rich

No code is sent to the LLM — only commit metadata.

---

- [difftests](https://github.com/faw21/difftests) — AI test generator from git diffs

- [critiq-action](https://github.com/faw21/critiq-action) — critiq as a GitHub Action for CI

- [mergefix](https://github.com/faw21/mergefix) — AI merge conflict resolver: fix all conflicts with one command

## License

MIT — see [LICENSE](LICENSE)
