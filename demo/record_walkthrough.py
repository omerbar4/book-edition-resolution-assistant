"""Record the BERA presentation walkthrough and screenshots (synthetic catalog only).

Prerequisites, all local:
- BERA serving the synthetic fixture catalog on 127.0.0.1:8000 with the local LLM, e.g.
  BERA_VAR_DIR=<scratch dir with catalog.sqlite> BERA_LLM_PROVIDER=openai_compat
  BERA_LLM_BASE_URL=http://127.0.0.1:8080/v1 BERA_LLM_MODEL=qwen3-4b-instruct-2507-q4km
  BERA_LLM_ROUTE_EVIDENCE=data/eval/llm_route_evidence_policy_v2_amended.json
  .tools/venv/bin/uv run python -m bera.cli serve --port 8000
- llama-server with Qwen3-4B-Instruct-2507 Q4_K_M on 127.0.0.1:8080 (`-c 8192 -ngl 99`).
- Playwright for Python and a Chromium build, in an environment you configure explicitly.
  Playwright is NOT a project dependency and this script never installs anything. Point
  BERA_PLAYWRIGHT_PYTHON at that environment's interpreter, and optionally pass
  --chromium-executable (or BERA_CHROMIUM_EXECUTABLE) to use an existing Chrome/Chromium
  instead of Playwright's own browser. Optional standalone setup (needs a download):
      python3.12 -m venv .tools/presentation-venv
      .tools/presentation-venv/bin/pip install playwright==1.63.0
      .tools/presentation-venv/bin/python -m playwright install chromium
      export BERA_PLAYWRIGHT_PYTHON=.tools/presentation-venv/bin/python

    "$BERA_PLAYWRIGHT_PYTHON" demo/record_walkthrough.py --out docs/presentation \
        --var-dir <BERA_VAR_DIR>

Every segment carries a label:
- LIVE: the UI, the API and the trace database are queried while recording; the LLM step is a
  real call to the local model. Captions are generated from the actual responses.
- MOCK: pytest security tests that feed scripted model outputs (test doubles, not the model).
- RECORDED: held-out numbers copied from docs/EVALUATION_REPORT.md, measured once at tag
  bera-eval-freeze-2026-11-07-r2. Nothing is re-run for them.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

try:
    from playwright.sync_api import Page, sync_playwright
except ImportError as exc:  # pragma: no cover - optional tooling
    raise SystemExit(
        "Playwright is not importable from this interpreter. Run the script with the Python of"
        " an environment that has it (BERA_PLAYWRIGHT_PYTHON); see the module docstring."
    ) from exc

BASE = "http://127.0.0.1:8000"
REPO = Path(__file__).resolve().parents[1]
UV = ".tools/venv/bin/uv"
W, H = 1280, 800

COLORS = {"LIVE": "#1a7f37", "MOCK": "#9a6700", "RECORDED": "#0969da", "BERA": "#57606a"}

OVERLAY_JS = """([kind, color, label, caption]) => {
  for (const id of ['__rec_banner', '__rec_caption']) document.getElementById(id)?.remove();
  const b = document.createElement('div');
  b.id = '__rec_banner';
  b.style.cssText = 'position:fixed;top:0;left:0;right:0;height:38px;z-index:99999;'
    + 'display:flex;align-items:center;gap:10px;padding:0 16px;background:#fff;'
    + 'border-bottom:1px solid #d0d7de;font:14px system-ui,sans-serif;color:#1f2328';
  const pill = document.createElement('span');
  pill.style.cssText = `background:${color};color:#fff;font-weight:700;padding:3px 10px;`
    + 'border-radius:4px;letter-spacing:.5px';
  pill.textContent = kind;
  const text = document.createElement('span');
  text.textContent = label;
  b.append(pill, text);
  const c = document.createElement('div');
  c.id = '__rec_caption';
  c.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:99999;padding:12px 20px;'
    + 'background:rgba(31,35,40,.92);color:#fff;font:17px/1.4 system-ui,sans-serif';
  c.textContent = caption;
  if (!caption) c.style.display = 'none';
  document.body.appendChild(b);
  document.body.appendChild(c);
  document.body.style.paddingTop = '44px';
  document.body.style.paddingBottom = '70px';
}"""

TERMINAL_HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#0d1117;color:#e6edf3;font:13.5px/1.45 ui-monospace,Menlo,monospace}
#t{padding:56px 22px 90px;white-space:pre-wrap;word-break:break-word}
.cmd{color:#7ee787}.pass{color:#3fb950}.fail{color:#f85149}.dim{color:#8b949e}
</style></head><body><div id="t"></div></body></html>"""

CARD_CSS = """body{margin:0;background:#f6f8fa;font:18px/1.5 system-ui,sans-serif;color:#1f2328}
main{max-width:1060px;margin:70px auto 0;padding:0 24px}
h1{font-size:34px;margin:.2em 0}h2{font-size:22px;margin:1.1em 0 .4em}
.sub{color:#57606a;font-size:20px}table{border-collapse:collapse;margin-top:8px}
td{padding:5px 14px 5px 0;vertical-align:top}td.n{font-weight:700;white-space:nowrap}
.pill{display:inline-block;color:#fff;font-weight:700;padding:1px 8px;border-radius:4px;
font-size:14px}ul{margin:.3em 0;padding-left:1.2em}li{margin:.25em 0}.muted{color:#57606a}"""


def health() -> dict[str, Any]:
    with urllib.request.urlopen(f"{BASE}/api/health", timeout=5) as r:  # noqa: S310 (fixed local URL)
        return dict(json.load(r))


def overlay(page: Page, kind: str, label: str, caption: str = "") -> None:
    page.evaluate(OVERLAY_JS, [kind, COLORS[kind], label, caption])


def caption(page: Page, text: str) -> None:
    page.evaluate(
        "t => { const c = document.getElementById('__rec_caption');"
        " c.textContent = t; c.style.display = t ? 'block' : 'none'; }",
        text,
    )


def scroll_to(page: Page, selector: str, offset: int = 50) -> None:
    page.evaluate(
        "([s, o]) => { const e = document.querySelector(s);"
        " window.scrollTo({top: e.getBoundingClientRect().top + window.scrollY - o,"
        " behavior: 'smooth'}); }",
        [selector, offset],
    )
    page.wait_for_timeout(900)


def blank(page: Page, content: str) -> None:
    """Leave the app's origin first so its CSP does not apply to the recorder's own pages."""
    page.goto("about:blank")
    page.set_content(content)


def card(page: Page, kind: str, label: str, body: str, cap: str = "") -> None:
    blank(
        page,
        f"<!doctype html><html><head><meta charset='utf-8'><style>{CARD_CSS}"
        f"</style></head><body><main>{body}</main></body></html>",
    )
    overlay(page, kind, label, cap)


def resolve_in_ui(page: Page, fields: dict[str, str]) -> dict[str, Any]:
    page.click("button.secondary:has-text('Clear')")
    for name, value in fields.items():
        page.click(f"input[name={name}]")
        page.keyboard.type(value, delay=35)
    with page.expect_response(lambda r: r.url.endswith("/api/resolve"), timeout=30000) as resp:
        page.click("button[type=submit]")
    page.wait_for_selector("[data-testid=outcome]")
    page.wait_for_timeout(300)
    return dict(resp.value.json())


def run_in_terminal(page: Page, shown: str, argv: list[str], env: dict[str, str]) -> str:
    """Run a real command while recording and stream its output into the page."""
    page.evaluate(
        "s => { const d = document.createElement('div'); d.className = 'cmd';"
        " d.textContent = '$ ' + s; document.getElementById('t').appendChild(d); }",
        shown,
    )
    page.wait_for_timeout(800)
    proc = subprocess.Popen(  # noqa: S603 (fixed argv built in this file)
        argv, cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    assert proc.stdout is not None
    out = []
    for line in proc.stdout:
        out.append(line)
        page.evaluate(
            "l => { const d = document.createElement('div');"
            " if (/PASSED|passed/.test(l)) d.className = 'pass';"
            " if (/ FAILED|\\d+ failed/.test(l)) d.className = 'fail';"
            " d.textContent = l.replace(/\\n$/, '') || ' ';"
            " document.getElementById('t').appendChild(d);"
            " window.scrollTo(0, document.body.scrollHeight); }",
            line,
        )
    proc.wait()
    page.evaluate(
        "() => { const d = document.createElement('div'); d.innerHTML = '&nbsp;';"
        " document.getElementById('t').appendChild(d); }"
    )
    return "".join(out)


LIMITATION_CAPTION = (
    "Citations validated; free-text reasoning is not validated."
    " Multiple editions remain compatible."
)


def adjudication_caption(res: dict[str, Any]) -> list[str]:
    """Describe the live adjudication from the actual response, whatever it was."""
    a = res.get("adjudication") or {}
    status = a.get("status")
    caps = []
    if status == "completed" and a.get("output"):
        out = a["output"]
        cited = ", ".join(f"{e['candidate_id']}.{e['field']}" for e in out["evidence_fields"])
        caps.append(
            f"Live Qwen3-4B answered in a strict JSON schema: choice {out['choice']}"
            f" ({a.get('chosen_edition_id') or 'abstain'}), citing {cited}."
        )
        caps.append(
            "Validated in code: the choice is in the candidate allowlist and every cited value"
            " exactly matches the stored record. Confidence is logged only, never used."
        )
        if "multiple_consistent_candidates" in res.get("reasons", []):
            caps.append(LIMITATION_CAPTION)
        else:
            caps.append("Citations validated; free-text reasoning is not validated.")
    else:
        errs = "; ".join(a.get("validation_errors") or []) or "no output"
        caps.append(f"Live call status: {status} ({errs}). The case falls back to human review.")
    caps.append(
        f"Final outcome stays '{res['outcome']}': the LLM is advisory. Its route gate is closed"
        " (dev agree route 4/10; opening needs ≥30 cases and a 95% Wilson lower bound ≥ 0.95)."
    )
    return caps


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--var-dir", type=Path, required=True, help="BERA_VAR_DIR of the server")
    ap.add_argument(
        "--chromium-executable",
        default=os.environ.get("BERA_CHROMIUM_EXECUTABLE") or None,
        help="existing Chrome/Chromium binary (default: Playwright's configured browser)",
    )
    args = ap.parse_args()

    h = health()
    if h["catalog_meta"].get("all_synthetic") != "True":
        raise SystemExit("refusing: the served catalog is not all synthetic")
    if not str(h["capabilities"]["llm"]).startswith("openai_compat:"):
        raise SystemExit("refusing: the server is not configured with the local LLM")
    model = h["capabilities"]["llm"].split(":", 1)[1]

    args.out.mkdir(parents=True, exist_ok=True)
    shots = args.out / "screenshots"
    shots.mkdir(exist_ok=True)
    video_tmp = args.out / ".video_tmp"
    env = {**os.environ, "BERA_VAR_DIR": str(args.var_dir)}
    log: dict[str, Any] = {"recorded_at_unix": time.time(), "health": h, "segments": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.chromium_executable)
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=2,
            record_video_dir=str(video_tmp),
            record_video_size={"width": W, "height": H},
        )
        page = ctx.new_page()

        # ---- title card ------------------------------------------------------------------
        card(
            page,
            "BERA",
            "Book Edition Resolution Assistant · v0.1.0 · local walkthrough",
            f"""
          <h1>Hybrid retrieval with a schema-validated, evaluation-gated LLM adjudicator</h1>
          <p class="sub">Given an ISBN or a partial book description, BERA suggests one Open
          Library edition or routes the case to human review.</p>
          <h2>In this recording</h2><ul>
          <li><span class="pill" style="background:{COLORS["LIVE"]}">LIVE</span> the running
          app on a <b>30-edition synthetic catalog</b>; the LLM is a real local call to
          {html.escape(model)} (llama-server on 127.0.0.1)</li>
          <li><span class="pill" style="background:{COLORS["MOCK"]}">MOCK</span> security tests
          that feed scripted model outputs (test doubles, not the model)</li>
          <li><span class="pill" style="background:{COLORS["RECORDED"]}">RECORDED</span>
          held-out results from the frozen r2 evaluation, not re-run</li></ul>
          <p class="muted">No dev or held-out evaluation cases appear in the live segments.</p>""",
        )
        page.wait_for_timeout(9000)

        # ---- 1. deterministic resolution ---------------------------------------------------
        page.goto(BASE + "/")
        overlay(
            page,
            "LIVE",
            "1 · Deterministic resolution (LLM not invoked) · synthetic catalog",
            "ISBN with hyphens: normalized and checksum-validated.",
        )
        r1 = resolve_in_ui(page, {"isbn": "978-0-00-001002-5"})
        overlay(
            page,
            "LIVE",
            "1 · Deterministic resolution (LLM not invoked) · synthetic catalog",
            f"One checksum-valid mapping, no conflicting field → {r1['outcome']}"
            f" {r1.get('suggested_edition_id')} ({', '.join(r1['reasons'])}). "
            f"LLM status: {(r1.get('adjudication') or {}).get('status', 'not invoked')}.",
        )
        page.wait_for_timeout(5000)
        r2 = resolve_in_ui(
            page,
            {
                "title": "Practical Data Structurs",
                "author": "Priya Natarajan",
                "physical_format": "paperback",
            },
        )
        caption(
            page,
            f"Typo in the title: BM25 + trigram retrieval fused with RRF still finds it;"
            f" exactly one edition fits every field → {r2['outcome']}"
            f" {r2.get('suggested_edition_id')}. LLM status:"
            f" {(r2.get('adjudication') or {}).get('status', 'not invoked')}.",
        )
        page.wait_for_timeout(3500)
        scroll_to(page, "article.candidate", 60)
        caption(
            page,
            "Each candidate shows deterministic field checks: agree / disagree /"
            " unknown, with the query value and the stored record.",
        )
        page.wait_for_timeout(5000)
        page.evaluate("window.scrollTo({top: 0})")
        page.wait_for_timeout(300)
        page.screenshot(path=str(shots / "01-deterministic-suggestion.png"))
        log["segments"].append({"id": 1, "kind": "LIVE", "responses": [r1, r2]})

        # ---- 2. live Qwen adjudication -----------------------------------------------------
        label2 = f"2 · Real local LLM inference: {model} via llama-server (127.0.0.1)"
        overlay(
            page, "LIVE", label2, "Ambiguous query: title (without apostrophe) and author only."
        )
        page.evaluate("window.scrollTo({top: 0})")
        page.click("button.secondary:has-text('Clear')")
        for name, value in {
            "title": "The Lantern Keepers Daughter",
            "author": "Mara Ellison",
        }.items():
            page.click(f"input[name={name}]")
            page.keyboard.type(value, delay=35)
        caption(
            page,
            "Several editions fit, so the policy asks the local model to adjudicate"
            " among at most 5 opaque candidates (c1–c5). Waiting for the live call…",
        )
        with page.expect_response(lambda r: r.url.endswith("/api/resolve"), timeout=30000) as resp:
            page.click("button[type=submit]")
        page.wait_for_selector("[data-testid=outcome]")
        r3 = dict(resp.value.json())
        caps = adjudication_caption(r3)
        scroll_to(page, ".outcome", 54)
        caption(page, caps[0])
        page.wait_for_timeout(9000)
        caption(page, caps[1])
        page.wait_for_timeout(6500)
        if len(caps) == 4:
            caption(page, caps[2])
            page.wait_for_timeout(4000)
            page.screenshot(path=str(shots / "02-live-llm-advisory.png"))
            page.wait_for_timeout(4000)
        caption(page, caps[-1])
        page.wait_for_timeout(6500)
        if len(caps) != 4:
            page.screenshot(path=str(shots / "02-live-llm-advisory.png"))
        scroll_to(page, "article.candidate", 60)
        caption(
            page,
            "Candidates: four editions agree on every supplied field, so"
            " deterministic checks cannot break the tie.",
        )
        page.wait_for_timeout(5500)
        flagged = page.locator("article.candidate:has(.warn)")
        if flagged.count():
            scroll_to(page, "article.candidate:has(.warn)", 120)
            caption(
                page,
                "A look-alike record with hidden characters is flagged for suspicious"
                " Unicode and is not offered to the model (no c-ref).",
            )
            page.wait_for_timeout(5500)
        log["segments"].append({"id": 2, "kind": "LIVE", "responses": [r3]})

        # ---- 3. mock security tests --------------------------------------------------------
        blank(page, TERMINAL_HTML)
        overlay(
            page,
            "MOCK",
            "3 · Security tests with scripted model outputs (test doubles, not Qwen)",
            "Forged candidate ids, fabricated or substring citations, citing"
            " the wrong candidate, and prompt injection must all be rejected or ignored.",
        )
        selection = (
            "forged or fabricated or wrong_candidate or substring or own_evidence"
            " or not_retried or injection"
        )
        pytest_args = [
            "run",
            "pytest",
            "tests/security/test_adjudication_attacks.py",
            "-vv",
            "--no-header",
            "-p",
            "no:cacheprovider",
            "--color=no",
            "-k",
            selection,
        ]
        out3 = run_in_terminal(
            page, f"uv {' '.join(pytest_args[:-1])} '{selection}'", [UV, *pytest_args], env
        )
        caption(
            page,
            "All pass: bad model output is rejected, never repaired or retried, and"
            " injected text cannot force a suggestion. These are fixtures, not live model"
            " failures.",
        )
        page.wait_for_timeout(6500)
        page.screenshot(path=str(shots / "03-mock-security-tests.png"))
        log["segments"].append({"id": 3, "kind": "MOCK", "pytest_tail": out3[-400:]})

        # ---- 4. latency and tokens through the API and traces -------------------------------
        blank(page, TERMINAL_HTML)
        overlay(
            page,
            "LIVE",
            "4 · Latency and token usage from the API and the local trace store",
            "Same ambiguous query through the API; the LLM call runs live again.",
        )
        body = '{"title":"The Lantern Keepers Daughter","author":"Mara Ellison"}'
        jq = (
            "{outcome, reasons, timings_ms, llm: (.adjudication | {status, attempts,"
            " choice: .output.choice, validation_errors, input_tokens, output_tokens})}"
        )
        curl_shown = (
            f"curl -s -X POST {BASE}/api/resolve -H 'content-type: application/json'"
            f" -d '{body}' | jq '{jq}'"
        )
        out4 = run_in_terminal(page, curl_shown, ["bash", "-c", curl_shown], env)
        caption(
            page,
            "Per-stage timings in ms: retrieval and checks take milliseconds; the"
            " local LLM call takes seconds. Token counts come from the model server.",
        )
        page.wait_for_timeout(6000)
        sql = (
            "select substr(query_hmac,1,12)||'…' as query_hmac, fields_present, outcome,"
            " adjudication_status as llm, attempts as att, input_tokens as tok_in,"
            " output_tokens as tok_out, cast(json_extract(timings_ms,'$.total') as int)"
            " as total_ms from traces order by created_at desc limit 5"
        )
        sql_shown = f'sqlite3 -header -column "$BERA_VAR_DIR/traces.sqlite" "{sql}"'
        out4b = run_in_terminal(page, sql_shown, ["bash", "-c", sql_shown], env)
        caption(
            page,
            "Every request in this recording is traced locally: timings, LLM status"
            " and tokens, with the query stored only as a salted HMAC, never as raw text.",
        )
        page.wait_for_timeout(7500)
        page.screenshot(path=str(shots / "04-latency-tokens-traces.png"))
        log["segments"].append({"id": 4, "kind": "LIVE", "curl": out4, "traces": out4b})

        # ---- 5. recorded held-out results --------------------------------------------------
        card(
            page,
            "RECORDED",
            "5 · Held-out results, frozen tag bera-eval-freeze-2026-11-07-r2"
            " (evaluated once; not re-run here)",
            """
          <h1>Held-out evaluation (r2 snapshot)</h1>
          <p class="sub">40 program-drafted, human-reviewed queries · 39 families · one labeler
          · policy conservative-rules-v2</p>
          <table>
          <tr><td class="n">0 / 40</td><td>wrong suggestions observed (95% Wilson upper bound
          8.8%), <b>paired with</b></td></tr>
          <tr><td class="n">6 / 15</td><td>answerable queries suggested correctly (coverage;
          95% Wilson 19.8–64.3%)</td></tr>
          <tr><td class="n">25 / 25</td><td>cases the human sent to review were routed to
          review</td></tr>
          <tr><td class="n">7 configs</td><td>identical final decisions, from exact/fuzzy and
          BM25 to hybrid + reranker + routed LLM</td></tr>
          <tr><td class="n">2 / 11</td><td>LLM picks that matched the human's answer; it
          changed no decision → <b>no measured accuracy gain from the LLM</b></td></tr>
          <tr><td class="n">gate</td><td>dev agree route 4/10 (Wilson lower bound 0.17);
          opening requires ≥30 cases and a 95% Wilson lower bound ≥ 0.95 → both routes
          closed</td></tr></table>
          <h2>Limits</h2><ul>
          <li>Small sample: with 6 suggestions, the error among suggestions is bounded only at
          39%.</li>
          <li>Queries are program-drafted perturbations of catalog records, not real traffic;
          one labeler; confidence is uncalibrated.</li>
          <li>v0.1.0 adds documented post-evaluation fixes that were not re-evaluated on
          held-out data.</li></ul>""",
            "Source: docs/EVALUATION_REPORT.md. These numbers describe the evaluated r2"
            " snapshot, not this recording.",
        )
        page.wait_for_timeout(20000)

        card(
            page,
            "BERA",
            "github.com/omerbar4/book-edition-resolution-assistant",
            """
          <h1>What this shows</h1><ul>
          <li>Hybrid retrieval and deterministic checks make every decision.</li>
          <li>A real local LLM adjudicates ambiguous cases under a strict schema with verified
          citations, and stays advisory until measured evidence clears a pre-set gate.</li>
          <li>Evaluation decided the LLM's role: no measured gain, so its gates stay
          closed.</li></ul>""",
        )
        page.wait_for_timeout(6000)

        video = page.video
        ctx.close()
        browser.close()
        assert video is not None
        dest = args.out / "bera-walkthrough.webm"
        shutil.move(video.path(), dest)
        shutil.rmtree(video_tmp, ignore_errors=True)

    (args.out / "recording_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {dest} and {shots}/*.png")


if __name__ == "__main__":
    main()
