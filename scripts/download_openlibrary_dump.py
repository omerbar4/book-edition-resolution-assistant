"""Download the pinned Open Library dump files. REQUIRES explicit owner approval.

Not run as part of tests or CI. Files go to ./downloads/ (git-ignored), are verified against
the archive.org-published size and sha1, and are deleted after the corpus is built.

    uv run python scripts/download_openlibrary_dump.py --approved-by-owner \
        editions authors redirects
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

DUMP_DATE = "2026-10-31"
BASE = f"https://archive.org/download/ol_dump_{DUMP_DATE}/"
# Sizes and sha1 from archive.org item metadata, checked 2026-11-03.
FILES = {
    "editions": (12_630_804_778, "78d5434c97782081e3f3adf37e2c53c18aed0b41"),
    "authors": (784_183_875, "93c27cf01586db495f2f0245d78a4ebfcdf298e5"),
    "redirects": (75_673_010, "d8559bfbd88934d1b9d1caf354105eb4a2adefec"),
    "works": (4_078_855_962, "07d086eb1c5b06b6a3905c1ab48469891b194d86"),
}
USER_AGENT = "book-edition-resolution-assistant/0.1 (portfolio project; one-time dump download)"


def fetch(name: str, out_dir: Path) -> Path:
    size, sha1 = FILES[name]
    path = out_dir / f"ol_dump_{name}_{DUMP_DATE}.txt.gz"
    have = path.stat().st_size if path.exists() else 0
    if have < size:
        req = urllib.request.Request(BASE + path.name, headers={"User-Agent": USER_AGENT})
        if have:
            req.add_header("Range", f"bytes={have}-")
        with urllib.request.urlopen(req, timeout=60) as resp:
            # Append only if the server honored the range (206); otherwise start over.
            mode = "ab" if have and resp.status == 206 else "wb"
            with path.open(mode) as fh:
                while chunk := resp.read(1 << 20):
                    fh.write(chunk)
    if path.stat().st_size < size:
        raise SystemExit(f"{path.name}: incomplete ({path.stat().st_size}/{size}); rerun to resume")
    h = hashlib.sha1(usedforsecurity=False)
    with path.open("rb") as fh:
        while block := fh.read(1 << 20):
            h.update(block)
    if path.stat().st_size < size:
        raise SystemExit(f"{path.name}: incomplete ({path.stat().st_size}/{size}); rerun to resume")
    if path.stat().st_size != size or h.hexdigest() != sha1:
        raise SystemExit(f"{path.name}: size/sha1 mismatch; refusing to use it")
    print(f"verified {path.name}")
    return path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+", choices=sorted(FILES))
    p.add_argument("--approved-by-owner", action="store_true")
    p.add_argument("--out", type=Path, default=Path("downloads"))
    a = p.parse_args()
    if not a.approved_by_owner:
        sys.exit("refusing: dump downloads require explicit owner approval (--approved-by-owner)")
    total = sum(FILES[f][0] for f in a.files)
    print(f"downloading {len(a.files)} file(s), {total / 1e9:.2f} GB, from {BASE}")
    a.out.mkdir(exist_ok=True)
    for f in a.files:
        fetch(f, a.out)


if __name__ == "__main__":
    main()
