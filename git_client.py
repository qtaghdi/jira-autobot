from __future__ import annotations

import subprocess
from datetime import datetime, timedelta

from models import CommitInfo


def validate_repo(repo_path: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "rev-parse", "--git-dir"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return True, "Valid git repository"
        return False, result.stderr.strip()
    except FileNotFoundError:
        return False, "git is not installed or not on PATH"
    except Exception as e:
        return False, str(e)


def get_commits(repo_path: str, date_from: str, date_to: str) -> list[CommitInfo]:
    # --before is exclusive, so add 1 day
    to_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
    before_str = to_date.strftime("%Y-%m-%d")

    result = subprocess.run(
        [
            "git", "-C", repo_path, "log",
            f"--after={date_from}",
            f"--before={before_str}",
            "--pretty=format:%h|||%an|||%ad|||%s",
            "--date=short",
        ],
        capture_output=True, text=True, timeout=30,
    )

    if result.returncode != 0:
        raise ValueError(f"git log failed: {result.stderr.strip()}")

    commits: list[CommitInfo] = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("|||", 3)
        if len(parts) == 4:
            commits.append(CommitInfo(
                hash=parts[0],
                author=parts[1],
                date=parts[2],
                message=parts[3],
            ))

    return commits
