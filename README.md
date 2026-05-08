# ccm

Claude Code CLI with full [claude_monitor](https://github.com/AlexWortega/claudemonitorpython) tracing.

Runs `claude` under the hood, streams every event (thinking, tool calls, results) and writes them as spans to claude_monitor in real time.

## Install

```bash
pip install git+https://github.com/LakoMoor/ccm.git
```

Requires [Claude Code](https://claude.ai/code) to be installed and authenticated.

## Setup

```bash
ccm init --monitor-key ba_...
```

Saves your key to `~/.config/ccm/config.toml`. That's it — no Anthropic API key needed, Claude Code already has it.

## Usage

```bash
# one-shot
ccm "fix the failing tests"

# interactive
ccm

# with options
ccm "refactor auth module" --project my-app --session run-42 --cwd ~/repos/myapp
```

## What gets traced

Every event from the Claude stream maps to a claude_monitor span:

| Claude event | Span kind |
|---|---|
| user prompt | `user_msg` |
| `thinking` block | `thinking` |
| `tool_use` block | `tool_use` |
| `tool_result` | `tool_result` (linked to parent `tool_use`) |
| `text` block | `assistant_msg` |
| final result | trace outcome `good` / `bad` + cost + duration |

## Python API

```python
from claude_monitor import Agent

agent = Agent(
    monitor_api_key="ba_...",
    project="my-app",
    model="claude-opus-4-7",
)

agent.run("add docstrings to all functions in utils.py", cwd="/path/to/repo")
```

## Options

```
ccm [task] [options]

  --project    Project name in claude_monitor   (default: default)
  --session    Session ID — resumes existing trace
  --model      Claude model                     (default: claude-sonnet-4-6)
  --cwd        Working directory for the agent  (default: .)
  --quiet      Suppress local output
```
