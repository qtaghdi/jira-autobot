from __future__ import annotations

import json
import re
from pathlib import Path

from models import TaskEntry

_HEADER_PATTERN = re.compile(r".+\s+\[오[전후]\s+\d{1,2}:\d{2}\]")


def parse_chat_message(text: str) -> list[str]:
    lines = text.strip().splitlines()
    tasks: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _HEADER_PATTERN.match(stripped):
            continue
        tasks.append(stripped)
    return tasks


def load_from_json(path: str | Path, year: int) -> list[TaskEntry]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)

    tasks: list[TaskEntry] = []
    for key in sorted(raw.keys()):
        date_str = f"{year}-{key}"
        for summary in parse_chat_message(raw[key]):
            tasks.append(TaskEntry(date=date_str, summary=summary))
    return tasks
