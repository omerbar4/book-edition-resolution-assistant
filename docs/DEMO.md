# Demo (3–5 minutes, local, synthetic catalog only)

The demo uses only the 30-edition synthetic fixture catalog (`data/fixtures/`). It never uses
a dev or held-out evaluation case, and its outcomes are what the fixtures are built to show,
not evaluation results. No network, no models and no LLM are needed.

## Setup

```bash
.tools/venv/bin/uv run python -m bera.cli build-catalog          # var/catalog.sqlite, 30 editions
npm --prefix frontend ci && npm --prefix frontend run build      # UI, once
.tools/venv/bin/uv run python -m bera.cli serve --port 8000      # terminal 1
.tools/venv/bin/uv run python demo/run_demo.py                   # terminal 2: scripted pass
```

`run_demo.py` refuses unless the server is local and its catalog is all synthetic. It exits
non-zero if any outcome differs from the expected one. Verified on 2026-11-08 against a clean
clone: 6/6 as expected.

## Script

| # | Type in the UI (http://127.0.0.1:8000) | Outcome | Point to make |
|---|---|---|---|
| 1 | ISBN `978-0-00-001002-5` | suggest SYN-E0002 (`unique_isbn_no_conflict`) | hyphens are normalized; one checksum-valid mapping and no conflicting field |
| 2 | title `Practical Data Structurs`, author `Priya Natarajan`, format paperback | suggest SYN-E0011 (`unique_consistent_match`) | the typo is tolerated by trigram retrieval; exactly one edition fits every supplied field |
| 3 | title `The Lantern Keepers Daughter`, author `Mara Ellison` | review (`multiple_consistent_candidates`) | four editions fit what was typed; an unknown field never breaks the tie |
| 4 | ISBN `9780000010124` | review (`duplicate_isbn_mapping`) | one ISBN maps to three records, including a different book; never auto-resolved |
| 5 | ISBN `9780000010019` | review (`isbn_bad_checksum`, `isbn_repair_hypothesis_only`) | a repaired ISBN is a hypothesis, not evidence |
| 6 | title `A Book That Is Not In The Catalog`, author `Nobody Known` | review (`likely_not_in_corpus`) | out-of-corpus queries go to a human |

For any case, point out the reason codes and each candidate's check table (field, check,
query, record), with agree/conflict/unknown per field. Then use **Confirm this edition** or
**Reject**. The UI answers "Recorded locally … Stored as feedback, not as an evaluation label".
The UI path for case 2 and its confirmation was checked in the browser against a clean clone
on 2026-11-08.

## What to say about results

Quote the held-out numbers only from [EVALUATION_REPORT.md](EVALUATION_REPORT.md), with their
denominators:

- 0/40 wrong suggestions observed (95% upper bound 8.8%; not zero risk);
- 6/15 answerable queries suggested correctly;
- all seven configurations made identical decisions;
- the LLM is advisory, with its gates closed;
- confidence is uncalibrated.

## Optional: the advisory LLM panel

This needs the locally built `llama-server` and the Qwen3-4B weights, which require
owner-approved downloads. Start the server on 127.0.0.1:8080 and serve BERA with
`BERA_LLM_PROVIDER=openai_compat BERA_LLM_BASE_URL=http://127.0.0.1:8080/v1
BERA_LLM_MODEL=qwen3-4b-instruct-2507-q4km` (the `--alias` given to llama-server). Case 3 then
shows the "Adjudication (advisory)" panel next to the final decision, which stays **review**
because the suggestion gates are closed.
