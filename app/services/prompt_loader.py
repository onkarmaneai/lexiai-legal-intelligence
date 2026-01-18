"""Prompt loading utilities."""
from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings


def load_prompt(name: str) -> str:
    return Path(settings.prompt_dir, name).read_text(encoding="utf-8")


def load_prompt_vars(name: str) -> dict:
    return json.loads(Path(settings.prompt_vars_dir, name).read_text(encoding="utf-8"))
