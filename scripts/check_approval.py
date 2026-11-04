"""Verify an owner approval record against the working tree before a full corpus build.

The record (JSON) pins the approved commit and sha256 of the selection config, seed list and
exclusions. A build is refused if those files differ, if selection code (src/bera) differs from
the approved commit, or if tracked files are modified. Writing the record is the owner's act;
this script only checks it.

    python3 -I scripts/check_approval.py APPROVED.txt CONFIG SEEDS EXCLUSIONS [--print]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def main() -> None:
    approval, cfg, seeds, excl, *rest = sys.argv[1:]
    rec = json.loads(Path(approval).read_text())
    commit = rec["approved_commit"]
    problems = []
    for name, path in (("config", cfg), ("seed_list", seeds), ("exclusions", excl)):
        want = rec["files"][name]
        if want["path"] != path or want["sha256"] != sha256(path):
            problems.append(f"{name} {path} does not match the approval record")
    if git("diff", "--name-only", commit, "HEAD", "--", "src/bera").strip():
        problems.append(f"src/bera differs from approved commit {commit}")
    if git("status", "--porcelain", "--untracked-files=no").strip():
        problems.append("tracked files are modified; commit or revert first")
    if problems:
        sys.exit("refusing build: " + "; ".join(problems))
    if "--print" in rest:
        head = git("rev-parse", "HEAD").strip()
        print(
            json.dumps(
                {
                    "approved_commit": commit,
                    "build_commit": head,
                    "src_bera_identical_to_approved": True,
                    "approval_record_sha256": sha256(approval),
                    "files": rec["files"],
                }
            )
        )


if __name__ == "__main__":
    main()
