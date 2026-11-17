#!/usr/bin/env python3
"""Check the forecast ledger: every entry's hash, the chain between entries, and date order.

Exit 0 when the ledger is intact, 1 otherwise. It does not check the OpenTimestamps proofs; use
``ots verify entries/<date>.json.ots`` for that.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def verify(entries: Path, ledger: Path) -> list[str]:
    problems: list[str] = []
    if not ledger.exists():
        return (
            problems if not any(entries.glob("*.json")) else ["entries exist but no ledger.jsonl"]
        )
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    listed: set[str] = set()
    previous_sha: str | None = None
    previous_date = ""
    for number, raw in enumerate(lines, start=1):
        line = json.loads(raw)
        name, date, sha = line["file"], line["as_of_date"], line["sha256"]
        listed.add(name)
        path = entries / name
        if not path.exists():
            problems.append(f"line {number}: {name} is missing")
            previous_sha, previous_date = sha, date
            continue
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != sha:
            problems.append(f"line {number}: {name} does not match its recorded sha256")
        entry = json.loads(body)
        if entry.get("as_of_date") != date or name != f"{date}.json":
            problems.append(f"line {number}: {name} date fields disagree")
        if entry.get("previous_entry_sha256") != previous_sha:
            problems.append(f"line {number}: {name} breaks the chain to the previous entry")
        if date <= previous_date:
            problems.append(f"line {number}: {name} is not later than the previous entry")
        previous_sha, previous_date = sha, date
    for path in sorted(entries.glob("*.json")):
        if path.name not in listed:
            problems.append(f"{path.name} is not listed in ledger.jsonl")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entries", type=Path, default=HERE / "entries")
    parser.add_argument("--ledger", type=Path, default=HERE / "ledger.jsonl")
    args = parser.parse_args(argv)
    problems = verify(args.entries, args.ledger)
    for problem in problems:
        print(f"FAIL: {problem}")
    if problems:
        return 1
    count = len(list(args.entries.glob("*.json")))
    print(f"ledger OK: {count} entries, hashes and chain intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
