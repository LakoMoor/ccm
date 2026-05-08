"""Read CLAUDE_MONITOR_API_KEY from ~/.config/ccm/config.toml or env."""

from __future__ import annotations

import os
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "ccm" / "config.toml"


def _load() -> dict[str, str]:
    if not CONFIG_PATH.exists():
        return {}
    if sys.version_info >= (3, 11):
        import tomllib
        with open(CONFIG_PATH, "rb") as f:
            return tomllib.load(f)
    result: dict[str, str] = {}
    for line in CONFIG_PATH.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#") and not line.startswith("["):
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def get(key: str) -> str:
    return _load().get(key) or os.environ.get(key, "")


def write(monitor_key: str) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(f'CLAUDE_MONITOR_API_KEY = "{monitor_key}"\n')
    CONFIG_PATH.chmod(0o600)
    print(f"Saved → {CONFIG_PATH}")
