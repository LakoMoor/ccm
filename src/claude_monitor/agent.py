"""Stream claude CLI output → claude_monitor spans."""

from __future__ import annotations

import json
import subprocess
import sys
import uuid
from typing import Iterator

from .client import Run


def _stream_claude(task: str, cwd: str, model: str, extra_flags: list[str]) -> Iterator[dict]:
    cmd = [
        "claude", "-p",
        "--output-format", "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
    ]
    if model:
        cmd += ["--model", model]
    cmd += extra_flags
    cmd.append(task)

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, cwd=cwd,
    )
    for line in proc.stdout:
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                pass
    proc.wait()


class Agent:
    def __init__(
        self,
        *,
        monitor_api_key: str,
        project: str = "default",
        session_id: str | None = None,
        model: str = "claude-sonnet-4-6",
        verbose: bool = True,
        extra_flags: list[str] | None = None,
    ):
        self.monitor_key  = monitor_api_key
        self.project      = project
        self.session_id   = session_id or f"ccm-{uuid.uuid4().hex[:8]}"
        self.model        = model
        self.verbose      = verbose
        self.extra_flags  = extra_flags or []

    def _log(self, *args):
        if self.verbose:
            print(*args, flush=True)

    def run(self, task: str, cwd: str = ".") -> str:
        self._log(f"\n> {task}\n{'─' * 60}")

        with Run(
            api_key=self.monitor_key,
            project=self.project,
            session_id=self.session_id,
            task_name=task[:120],
            model=self.model,
        ) as run:
            run.log_user(task)

            # tool_use_id → span.id  для связи parent_span_id у tool_result
            pending_tools: dict[str, str] = {}
            final_text = ""

            for event in _stream_claude(task, cwd, self.model, self.extra_flags):
                etype = event.get("type")

                # ── assistant events ─────────────────────────────────────────
                if etype == "assistant":
                    for block in event.get("message", {}).get("content", []):
                        btype = block.get("type")

                        if btype == "thinking":
                            run.log_thinking(block["thinking"])
                            self._log(f"  [thinking] {block['thinking'][:80]}…")

                        elif btype == "tool_use":
                            span = run.log_tool_use(block["name"], block.get("input", {}))
                            pending_tools[block["id"]] = span.id
                            self._log(f"\n  [{block['name']}] {json.dumps(block.get('input',{}))[:80]}")

                        elif btype == "text" and block.get("text"):
                            final_text = block["text"]
                            run.log_assistant(final_text)
                            self._log(f"\n[claude] {final_text}")

                # ── tool results ─────────────────────────────────────────────
                elif etype == "user":
                    for block in event.get("message", {}).get("content", []):
                        if block.get("type") == "tool_result":
                            tool_use_id   = block.get("tool_use_id", "")
                            parent_span_id = pending_tools.pop(tool_use_id, None)
                            content = block.get("content", "")
                            if isinstance(content, list):
                                content = "\n".join(c.get("text","") for c in content)
                            run.log_tool_result(
                                str(content)[:3000],
                                parent_span_id=parent_span_id,
                            )
                            self._log(f"  → {str(content)[:100]}")

                # ── final result ─────────────────────────────────────────────
                elif etype == "result":
                    outcome = "bad" if event.get("is_error") else "good"
                    run.finish(
                        outcome=outcome,
                        metadata={
                            "cost_usd":  event.get("total_cost_usd"),
                            "turns":     event.get("num_turns"),
                            "duration_ms": event.get("duration_ms"),
                        },
                    )
                    self._log(f"\n{'─'*60}\n{outcome.upper()}  {event.get('duration_ms',0)/1000:.1f}s")

            return final_text
