#!/usr/bin/env python3
"""Refresh curated Hugging Face metadata using the API's LFS blob metadata."""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "models.json"


def api_model(repo: str, revision: str) -> dict:
    quoted = urllib.parse.quote(repo, safe="/")
    rev = urllib.parse.quote(revision, safe="")
    url = f"https://huggingface.co/api/models/{quoted}/revision/{rev}?blobs=true"
    req = urllib.request.Request(url, headers={"User-Agent": "speechscope-model-catalog/0.1"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def main() -> int:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    api_cache: dict[tuple[str, str], dict] = {}
    for ref, model in data["models"].items():
        repo = model["source"]["repository"]
        rev = model["source"]["revision"]
        key = (repo, rev)
        api_cache.setdefault(key, api_model(repo, rev))
        siblings = {item["rfilename"]: item for item in api_cache[key].get("siblings", [])}
        for artifact in model["artifacts"]:
            blob = siblings.get(artifact["path"])
            if blob is None:
                raise RuntimeError(f"{ref}: upstream file not found: {artifact['path']}")
            lfs = blob.get("lfs")
            if isinstance(lfs, dict):
                artifact["size"] = int(lfs["size"])
                artifact["sha256"] = str(lfs["sha256"])
            elif model["acquisition"]["mode"] == "managed":
                raise RuntimeError(f"{ref}: managed artifact lacks LFS SHA metadata")
    CATALOG.write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"updated {len(data['models'])} model entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
