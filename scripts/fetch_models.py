"""Download the models pinned in models.lock.json into ./models/ (git-ignored), verifying
each file: LFS files by SHA-256, small files by git blob SHA-1 (as published by Hugging Face).

Requires explicit owner approval; never run by tests or CI.

    uv run python scripts/fetch_models.py --approved-by-owner [role ...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "models.lock.json"
USER_AGENT = "book-edition-resolution-assistant/0.1 (portfolio project)"


def git_blob_sha1(data: bytes) -> str:
    h = hashlib.sha1(f"blob {len(data)}\0".encode(), usedforsecurity=False)
    h.update(data)
    return h.hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while block := fh.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def verify(path: Path, entry: dict[str, object]) -> bool:
    if not path.exists() or path.stat().st_size != entry["size"]:
        return False
    if "sha256" in entry:
        return sha256_file(path) == entry["sha256"]
    return git_blob_sha1(path.read_bytes()) == entry["git_blob_sha1"]


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    have = tmp.stat().st_size if tmp.exists() else 0
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if have:
        req.add_header("Range", f"bytes={have}-")
    with urllib.request.urlopen(req, timeout=60) as resp, tmp.open("ab") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
    tmp.rename(dest)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("roles", nargs="*")
    p.add_argument("--approved-by-owner", action="store_true")
    a = p.parse_args()
    if not a.approved_by_owner:
        sys.exit("refusing: model downloads require explicit owner approval (--approved-by-owner)")
    lock = json.loads(LOCK.read_text())
    for m in lock["models"]:
        if a.roles and m["role"] not in a.roles:
            continue
        base = ROOT / "models" / m["repo"].replace("/", "__") / m["revision"]
        for e in m["files"]:
            dest = base / e["path"]
            if not verify(dest, e):
                if dest.exists():
                    dest.unlink()
                fetch(e["url"], dest)
                if not verify(dest, e):
                    sys.exit(f"verification failed: {m['repo']}/{e['path']}")
            print(f"verified {m['repo']}@{m['revision'][:12]} {e['path']}")


if __name__ == "__main__":
    main()
