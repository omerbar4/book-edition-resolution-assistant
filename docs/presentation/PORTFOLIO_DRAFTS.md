# Portfolio and résumé drafts (not yet used anywhere)

Drafts for the owner to adapt. The actual CV, portfolio site and GitHub About text have not
been changed. Every number here matches [EVALUATION_REPORT.md](../EVALUATION_REPORT.md).
Held-out numbers belong to tag `bera-eval-freeze-2026-11-07-r2`, not to later `main`.

## Headline

**Hybrid retrieval with a schema-validated, evaluation-gated LLM adjudicator.**

## Portfolio description (about 120 words)

BERA matches an ISBN or a partial book description to one Open Library edition, or sends the
case to human review. It validates ISBNs, retrieves candidates with BM25, trigram and
embedding search fused by reciprocal rank fusion, and runs deterministic field checks. When
several editions still fit, a local Qwen3-4B model must pick one in a strict JSON schema and
cite record fields. Code checks the choice against an allowlist and each citation against the
stored record. The model can change a decision only through a gate set before measurement: at
least 30 dev cases and a 95% Wilson lower confidence bound of at least 0.95. It reached 4/10,
so it stays advisory. On 40 held-out, program-drafted, human-reviewed queries: 0/40 wrong
suggestions observed, with 6/15 answerable coverage. All seven configurations made identical
decisions, so the LLM showed no measured accuracy gain.

## Three résumé bullets

- Built a FastAPI + React book-edition resolver that combines SQLite FTS5 BM25, trigram and
  bge-small embedding retrieval (reciprocal rank fusion), cross-encoder reranking and
  deterministic field checks, and routes ambiguous cases to human review; traced per-stage
  latency and token usage locally, storing queries only as salted HMACs.
- Integrated a local Qwen3-4B (llama.cpp) adjudicator with JSON-schema-constrained output,
  strict Pydantic validation, a candidate allowlist, exact-match citation checks, bounded
  retries and deadlines, and prompt-injection tests. Kept it advisory because dev evidence
  (4/10) missed a pre-set gate: at least 30 cases and a 95% Wilson lower bound of at least
  0.95.
- Ran a frozen held-out evaluation on 40 program-drafted, human-reviewed queries: 0/40 wrong
  suggestions observed (95% upper bound 8.8%) at 6/15 answerable coverage. All 7 retrieval and
  LLM configurations made identical decisions, so I reported no LLM accuracy gain.

## Interview answers

**60 seconds.** BERA takes an ISBN or a messy book description and either suggests the exact
Open Library edition or sends it to a person. It validates ISBNs, retrieves candidates with
keyword, typo-tolerant and embedding search fused with reciprocal rank fusion, then checks
each field. When several editions still fit, a local Qwen model has to pick one in a strict
JSON schema and cite fields, and code verifies those citations against the records. Before
measuring, I fixed the rule for letting the model change a decision: at least 30 labeled dev
cases and a 95% Wilson lower confidence bound on precision of at least 0.95. It got 4 of 10
right, so it stays advisory. On a frozen held-out set of 40 human-reviewed queries, the system
made no wrong suggestions but covered only 6 of 15 answerable ones. Every configuration made
the same decisions, including the one with the LLM.

**Why use an LLM here?** Some ambiguity, such as subtitle or format wording, could plausibly
benefit from language understanding. I treated that as a hypothesis. The model only chooses
among retrieved records and must cite them, inside a schema, token budgets and deadlines, and
it cannot act on its own.

**Did it beat the baseline?** No. All seven configurations made identical final decisions on
held-out data. The LLM picked a candidate 11 times; 2 matched the human's answer and 9 were
on cases the human sent to review. That is a negative result, and I report it as one.

**Why are its decision gates closed?** The rule was set before measurement: a route opens
only with at least 30 dev cases and a 95% Wilson lower confidence bound of at least 0.95. The
agree route had 4 correct of 10, a lower bound of 0.17; the override route had no cases. The
held-out run supports keeping it closed: 9 of the model's 11 picks were on cases the human
sent to review.

## Wording to keep

- Say "program-drafted perturbations of catalog records, labeled by one human reviewer", not
  "real user queries".
- Always pair "0/40 wrong observed" with "6/15 answerable coverage" and the small sample.
- Don't use agentic, autonomous, fine-tuned, calibrated or production-scale.
