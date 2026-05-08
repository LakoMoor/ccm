"""CLI: ccm "task"  or  ccm  (interactive)  or  ccm init --monitor-key ba_..."""

from __future__ import annotations

import argparse
import sys

from .agent import Agent
from .config import get, write


def main() -> None:
    # ccm init  — отдельная ветка
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        p = argparse.ArgumentParser(prog="ccm init")
        p.add_argument("--monitor-key", required=True)
        args = p.parse_args(sys.argv[2:])
        write(args.monitor_key)
        return

    parser = argparse.ArgumentParser(prog="ccm", description="Claude Code + claude_monitor tracing")
    parser.add_argument("task",        nargs="?",    help="Task (omit for interactive mode)")
    parser.add_argument("--project",   default="default")
    parser.add_argument("--session",   default=None, help="Resume a previous session")
    parser.add_argument("--model",     default="claude-sonnet-4-6")
    parser.add_argument("--cwd",       default=".",  help="Working directory")
    parser.add_argument("--quiet",     action="store_true")

    args, extra_flags = parser.parse_known_args()

    monitor_key = get("CLAUDE_MONITOR_API_KEY")
    if not monitor_key:
        print("Error: run `ccm init --monitor-key ba_...` first", file=sys.stderr)
        sys.exit(1)

    agent = Agent(
        monitor_api_key=monitor_key,
        project=args.project,
        session_id=args.session,
        model=args.model,
        verbose=not args.quiet,
        extra_flags=extra_flags,
    )

    if args.task:
        agent.run(args.task, cwd=args.cwd)
        return

    print("ccm  (Ctrl+D to exit)\n")
    try:
        while True:
            try:
                task = input(">>> ").strip()
            except EOFError:
                break
            if task:
                agent.run(task, cwd=args.cwd)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
