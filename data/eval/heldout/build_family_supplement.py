"""Build the held-out family supplement (owner decision 2026-11-08, option 1).

    uv run python data/eval/heldout/build_family_supplement.py [--check]

Inputs: ONLY the pinned corpus mapping (data/corpus/v3_proposed/families.json) and the frozen
held-out queue (data/eval/heldout/heldout_queue.jsonl, verified against its manifest). Never
labels or model outputs. Output: families.json with an identity entry added for each probe
family (bera.evalkit.heldout.probe_family) that is absent from the corpus mapping. Every
existing entry is preserved exactly. Used only via `bera.evalkit.run --families`, which sets
evaluation grouping/validation; the resolver never sees a family.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from bera.evalkit.families import load_frozen_queue
from bera.evalkit.heldout import PROBE_STRATUM

ROOT = Path(__file__).resolve().parents[3]
CORPUS_MAP = ROOT / "data/corpus/v3_proposed/families.json"
QUEUE = ROOT / "data/eval/heldout/heldout_queue.jsonl"
OUT = ROOT / "data/eval/heldout/heldout_families_supplement.json"


def build() -> tuple[dict[str, str], list[str]]:
    base: dict[str, str] = json.loads(CORPUS_MAP.read_text())
    drafts, _ = load_frozen_queue(QUEUE)
    known = set(base.values())
    probes = [d for d in drafts if d.stratum == PROBE_STRATUM]
    assert all(not d.source_edition_id for d in probes)
    additions = sorted({d.family for d in probes} - known)
    assert not set(additions) & set(base), "an addition would overwrite an existing key"
    out = dict(base)
    for f in additions:
        out[f] = f
    return out, additions


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--check", action="store_true", help="verify the committed file")
    args = a.parse_args()
    out, additions = build()
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if args.check:
        assert OUT.read_text() == text, "supplement differs from a fresh build"
    else:
        OUT.write_text(text)
    base = json.loads(CORPUS_MAP.read_text())
    drafts, _ = load_frozen_queue(QUEUE)
    probes = Counter(d.family for d in drafts if d.stratum == PROBE_STRATUM)
    print(f"base entries {len(base)}; additions {len(additions)}; total {len(out)}")
    print(f"existing entries preserved exactly: {all(out[k] == v for k, v in base.items())}")
    print(
        f"probe queries {sum(probes.values())} in {len(probes)} probe families; "
        f"queries per probe family {sorted(probes.values())}"
    )
    print("sha256", hashlib.sha256(OUT.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
