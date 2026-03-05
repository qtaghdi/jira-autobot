from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CommitInfo:
    hash: str
    author: str
    date: str  # YYYY-MM-DD
    message: str


@dataclass
class TaskEntry:
    date: str  # YYYY-MM-DD
    summary: str
    status: str = "pending"  # pending | created | done | error
    issue_key: str = ""
    error_msg: str = ""
