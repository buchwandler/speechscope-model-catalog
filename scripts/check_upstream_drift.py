#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "catalog" / "source.json"


def head_sha(repo: str) -> str:
    url = f"https://huggingface.co/api/models/{repo}"
    req = urllib.request.Request(url, headers={"User-Agent": "speechscope-model-catalog/0.1"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    sha = data.get("sha")
    if not isinstance(sha, str) or len(sha) != 40:
        raise ValueError(f"{repo}: API did not return a 40-char sha")
    return sha


def main() -> int:
    try:
        source = json.loads(SOURCE.read_text(encoding="utf-8"))
        rows = []
        changed = False
        for item in sorted(source["sources"], key=lambda x: x["repository"]):
            repo, pinned = item["repository"], item["revision"]
            current = head_sha(repo)
            status = "ok" if current == pinned else "DRIFT"
            changed |= status != "ok"
            rows.append((status, repo, pinned, current))
        for status, repo, pinned, current in rows:
            print(f"{status:5} {repo} pinned={pinned} current={current}")
        return 2 if changed else 0
    except Exception as exc:  # noqa: BLE001
        print(f"drift check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
