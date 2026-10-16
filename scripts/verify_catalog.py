#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "models.json"
REV_RE = re.compile(r"^[0-9a-f]{40}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
REF_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9_.-]*$")


def fail(message: str) -> None:
    raise ValueError(message)


def _canonical_bytes(data: object) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def verify(path: Path = CATALOG) -> dict:
    raw = path.read_bytes()
    data = json.loads(raw)
    if raw != _canonical_bytes(data):
        fail(f"{path}: JSON must be canonical (indent=2, sort_keys=True, trailing newline)")
    if data.get("schema") != 1 or data.get("kind") != "speechscope-model-catalog":
        fail("unsupported catalog identity")
    models = data.get("models")
    if not isinstance(models, dict) or not models:
        fail("models must be a non-empty object")
    if data.get("source", {}).get("model_count") != len(models):
        fail("source.model_count must equal models size")

    aliases: dict[tuple[str, str], str] = {}
    for ref, item in models.items():
        if not REF_RE.fullmatch(ref) or item.get("ref") != ref:
            fail(f"{ref}: invalid or mismatched ref")
        backend, ident = ref.split(":", 1)
        if item.get("backend") != backend or item.get("id") != ident:
            fail(f"{ref}: backend/id must match ref")
        source = item.get("source", {})
        rev = source.get("revision")
        if not isinstance(rev, str) or not REV_RE.fullmatch(rev):
            fail(f"{ref}: source.revision must be a 40-hex commit")
        if source.get("provider") != "huggingface":
            fail(f"{ref}: only huggingface sources are supported in catalog v1")
        mode = item.get("acquisition", {}).get("mode")
        if mode not in {"managed", "runtime-managed"}:
            fail(f"{ref}: invalid acquisition mode")
        artifacts = item.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            fail(f"{ref}: artifacts must be non-empty")
        primary = [a for a in artifacts if a.get("primary") is True]
        if len(primary) != 1:
            fail(f"{ref}: exactly one primary artifact is required")
        for a in artifacts:
            rel = a.get("path")
            if not isinstance(rel, str) or rel.startswith("/") or ".." in Path(rel).parts:
                fail(f"{ref}: unsafe artifact path {rel!r}")
            url = a.get("url")
            if not isinstance(url, str):
                fail(f"{ref}: artifact url missing")
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.netloc != "huggingface.co":
                fail(f"{ref}: artifact must use HTTPS huggingface.co URL")
            if f"/resolve/{rev}/" not in parsed.path:
                fail(f"{ref}: artifact URL must pin source.revision")
            size, digest = a.get("size"), a.get("sha256")
            if mode == "managed":
                if not isinstance(size, int) or size <= 0:
                    fail(f"{ref}: managed artifact requires positive size")
                if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                    fail(f"{ref}: managed artifact requires SHA-256")
            elif digest is not None and (not isinstance(digest, str) or not SHA_RE.fullmatch(digest)):
                fail(f"{ref}: invalid optional SHA-256")
        for alias in item.get("aliases", []):
            key = (backend, alias)
            previous = aliases.get(key)
            if previous is not None and previous != ref:
                fail(f"duplicate alias {alias!r} in backend {backend!r}")
            aliases[key] = ref

    return data


def main() -> int:
    try:
        data = verify()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"catalog verification failed: {exc}", file=sys.stderr)
        return 1
    digest = hashlib.sha256(_canonical_bytes(data)).hexdigest()
    print(f"ok: {len(data['models'])} models; catalog sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
