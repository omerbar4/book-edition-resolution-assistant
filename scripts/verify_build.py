"""Compare two full corpus builds with each other and with the approved selection preview.

    python3 -I scripts/verify_build.py PREVIEW_DIR BUILD_A BUILD_B --out RESULT.json

Checks: identical corpus sha256; identical selected work ids, family assignments, split
balance, strata and sampled-edition analysis in A, B and the preview; every written edition
belongs to a selected work; editions written + dropped == editions sampled in the preview.
Exit 1 on any mismatch. Nothing is "explained away" here: differences are listed for a human.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def load(p: Path) -> Any:
    return json.loads(p.read_text())


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        while b := fh.read(1 << 20):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    args = sys.argv[1:]
    out = Path(args[args.index("--out") + 1])
    prev_dir, a_dir, b_dir = (Path(x) for x in args[:3])
    prev = load(prev_dir / "selection_preview.json")
    pm = load(prev_dir / "manifest.json")
    ma, mb = load(a_dir / "manifest.json"), load(b_dir / "manifest.json")
    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"check": name, "ok": bool(ok), **({"detail": detail} if detail else {})})

    ha, hb = sha256(a_dir / "corpus.jsonl"), sha256(b_dir / "corpus.jsonl")
    check("corpus_sha256_A_equals_B", ha == hb, {"A": ha, "B": hb})
    check("manifest_sha256_matches_file_A", ma["output"]["sha256"] == ha)
    check("manifest_sha256_matches_file_B", mb["output"]["sha256"] == hb)
    for f in ("probe_audit.json", "families.json"):
        check(f"{f}_A_equals_B", sha256(a_dir / f) == sha256(b_dir / f))
    for m, tag in ((ma, "A"), (mb, "B")):
        check(f"inputs_identical_preview_{tag}", m["inputs"] == pm["inputs"])
        check(
            f"pass1_rescanned_{tag}",
            "reused_scratch" not in m["read_stats"].get("editions_pass1", {}),
        )

    pa = {k: v for k, v in pm["analysis"].items()}
    fam_prev = pa["families"]["family_of"]
    sel_prev = sorted(r["work"] for r in prev["selected"])
    sampled_prev = sum(r["editions_sampled"] for r in prev["selected"])
    for m, tag in ((ma, "A"), (mb, "B")):
        an = m["analysis"]
        fam = an["families"]["family_of"]
        check(f"selected_ids_equal_preview_{tag}", sorted(fam) == sel_prev)
        diff = sorted(k for k in set(fam) | set(fam_prev) if fam.get(k) != fam_prev.get(k))
        check(f"family_assignments_equal_preview_{tag}", not diff, diff[:20] or None)
        check(f"split_balance_equal_preview_{tag}", an["split_balance"] == pa["split_balance"])
        check(f"strata_equal_preview_{tag}", m["strata"] == pm["strata"])
        check(
            f"edition_sampling_equal_preview_{tag}",
            an["edition_sampling"] == pa["edition_sampling"],
        )
        check(
            f"exclusion_counts_equal_preview_{tag}",
            all(
                m["exclusion_check"][k] == pm["exclusion_check"][k]
                for k in ("excluded_works", "excluded_by_rule")
            ),
        )
        check(
            f"no_strict_exclusion_violations_{tag}",
            not m["exclusion_check"]["violations"],
            m["exclusion_check"]["violations"][:20] or None,
        )
        dropped = sum(m["dropped"].get(k, 0) for k in m["dropped"] if k != "not_sampled")
        check(
            f"written_plus_dropped_equals_sampled_{tag}",
            m["editions_written"] + dropped == sampled_prev,
            {"written": m["editions_written"], "dropped": m["dropped"], "sampled": sampled_prev},
        )

    works = set(sel_prev)
    stray = []
    with (a_dir / "corpus.jsonl").open() as fh:
        for line in fh:
            e = json.loads(line)
            if e.get("work_id") not in works:
                stray.append(e["edition_id"])
    check("every_edition_in_a_selected_work", not stray, stray[:20] or None)

    result = {
        "corpus_sha256": ha,
        "editions_written": ma["editions_written"],
        "selected_works": len(sel_prev),
        "all_ok": all(c["ok"] for c in checks),
        "checks": checks,
        "provenance": ma.get("provenance"),
    }
    out.write_text(json.dumps(result, indent=2))
    for c in checks:
        print(("PASS " if c["ok"] else "FAIL ") + c["check"])
    print("ALL OK" if result["all_ok"] else "MISMATCH")
    sys.exit(0 if result["all_ok"] else 1)


if __name__ == "__main__":
    main()
