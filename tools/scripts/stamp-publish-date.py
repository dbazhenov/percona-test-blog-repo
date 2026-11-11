#!/usr/bin/env python3
"""Write the publication date into posts this push publishes for the first time.

A post that was already published keeps its date. Drafts are left alone.
The workflow runs this before building the feed, then commits the result
only after that build succeeds.
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
EMPTY = "0" * 40


def front_matter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[:end] if end >= 0 else ""


def is_draft(text: str) -> bool:
    return re.search(r'(?m)^draft:\s*["\']?true["\']?\s*$', front_matter(text)) is not None


def set_date(text: str, stamp: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    head, rest = text[:end], text[end:]
    replacement = f'date: "{stamp}"'
    new_head, count = re.subn(r'(?m)^date:\s*.*$', replacement, head, count=1)
    if count == 0:
        new_head = "---\n" + replacement + head[3:]
    return new_head + rest


def git_show(rev: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def changed_posts(base: str, head: str) -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "diff", "--name-status", "--find-renames", base, head, "--", "posts"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    rows = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[-1]
        if path.endswith(".md"):
            rows.append((status, path))
    return rows


def stamp_now() -> str:
    moment = datetime.now(ZoneInfo("America/Los_Angeles"))
    return moment.strftime("%Y-%m-%dT%H:%M:%S%z")[:-2] + ":" + moment.strftime("%z")[-2:]


def main() -> None:
    base = os.environ.get("BEFORE", "")
    head = os.environ.get("HEAD", "HEAD")
    if base == "" or set(base) == {"0"}:
        print("No previous commit to compare. Dates were not changed.")
        return
    stamp = stamp_now()
    changed = 0
    for status, path in changed_posts(base, head):
        if status.startswith("R") or status.startswith("C"):
            continue
        current = (ROOT / path).read_text() if (ROOT / path).is_file() else ""
        if current == "" or is_draft(current):
            continue
        previous = git_show(base, path) if status.startswith("M") else None
        if previous is not None and not is_draft(previous):
            continue
        updated = set_date(current, stamp)
        if updated is None or updated == current:
            print(f"skipped {path}: no date field", file=sys.stderr)
            continue
        (ROOT / path).write_text(updated)
        print(f"dated {path} {stamp}")
        changed += 1
    print(f"stamped {changed} posts")


if __name__ == "__main__":
    main()
