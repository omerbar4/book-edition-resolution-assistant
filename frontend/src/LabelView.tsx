import { useEffect, useMemo, useState } from "react";
import { visibleEscape as v } from "./visible";

interface QueueItem {
  draft_id: string;
  split: string;
  query: Record<string, string | number>;
  labeled: boolean;
  status?: "unlabeled" | "labeled" | "practice" | "exposed" | "skipped";
}
interface Queue {
  items: QueueItem[];
  reasons: string[];
  labeled: number;
  independent?: number;
  practice?: number;
  exposed?: number;
  skipped?: number;
  total: number;
  proposal_label_spec?: string;
  reveal_mode?: "per_case" | "after_batch" | "never";
  revealed?: boolean;
}
interface BatchRevealItem {
  draft_id: string;
  your_label: {
    expected: string;
    gold_edition_ids: string[];
    ambiguity_reason?: string | null;
  };
  proposed: {
    expected: string;
    gold_edition_ids: string[];
    ambiguity_reason?: string | null;
  };
  agrees_with_proposal: boolean;
  template?: string;
  template_note?: string | null;
}
interface BatchReveal {
  items: BatchRevealItem[];
  agree: number;
  total: number;
  note: string;
}
interface SearchPage {
  total: number;
  offset: number;
  limit: number;
  returned: number;
  truncated: boolean;
  match_rule: string;
  order: string;
  items: Row[];
}
const PAGE = 50;
interface Row {
  edition_id: string;
  work_id: string | null;
  title: string;
  subtitle: string | null;
  authors: string[];
  publishers: string[];
  publish_year: number | null;
  physical_format: string;
  edition_name: string | null;
  languages: string[];
  isbn_13: string[];
  isbn_10: string[];
}
interface Reveal {
  proposed: {
    expected: string;
    gold_edition_ids: string[];
    ambiguity_reason?: string | null;
  };
  agrees_with_proposal: boolean;
  proposal_label_spec?: string;
  template?: string;
  template_note?: string | null;
}

/** The labeler's answer. "" means not chosen yet; there is no default. */
type Answer = "" | "suggest" | "abstain";

const LABELER_KEY = "bera.labeler";

function readLabeler(): string {
  try {
    return localStorage.getItem(LABELER_KEY) ?? "";
  } catch {
    return "";
  }
}

export function LabelView() {
  const [queue, setQueue] = useState<Queue | null>(null);
  const [idx, setIdx] = useState(0);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState<SearchPage | null>(null);
  const rows = page?.items ?? [];
  const [skipReason, setSkipReason] = useState("");
  const [skippedMsg, setSkippedMsg] = useState<string | null>(null);
  const [gold, setGold] = useState<string[]>([]);
  const [answer, setAnswer] = useState<Answer>("");
  const [reason, setReason] = useState("");
  const [labeler, setLabeler] = useState(readLabeler);
  const [notes, setNotes] = useState("");
  const [reveal, setReveal] = useState<Reveal | null>(null);
  // after_batch queues: the save is confirmed, but nothing about the proposal is shown
  const [deferred, setDeferred] = useState<number | null>(null);
  const [batch, setBatch] = useState<BatchReveal | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadQueue() {
    const res = await fetch("/api/label/queue");
    if (!res.ok) throw new Error(`queue: ${res.status}`);
    const q = (await res.json()) as Queue;
    setQueue(q);
    return q;
  }
  useEffect(() => {
    loadQueue()
      .then((q) => {
        // start on the first case still to do (not labeled, practice or skipped)
        const first = q.items.findIndex(
          (i) =>
            !i.labeled &&
            (i.status ?? "unlabeled") !== "skipped" &&
            i.status !== "practice",
        );
        if (first > 0) setIdx(first);
      })
      .catch((e: unknown) => setError(String(e)));
  }, []);

  const item = queue?.items[idx];
  useEffect(() => {
    setGold([]);
    setAnswer("");
    setReason("");
    setNotes("");
    setReveal(null);
    setDeferred(null);
    setPage(null);
    setSkipReason("");
    setSkippedMsg(null);
    setSearch(
      typeof item?.query.title === "string"
        ? item.query.title.slice(0, 40)
        : "",
    );
  }, [item?.draft_id]);

  const canSubmit = useMemo(
    () =>
      labeler.trim() !== "" &&
      ((answer === "suggest" && gold.length > 0) ||
        (answer === "abstain" && reason !== "")) &&
      !reveal &&
      deferred === null &&
      !(queue?.reveal_mode === "after_batch" && queue.revealed),
    [labeler, answer, reason, gold, reveal, deferred, queue],
  );

  async function runSearch(offset = 0) {
    setError(null);
    const q = new URLSearchParams({
      title: search.trim(),
      offset: String(offset),
      limit: String(PAGE),
    });
    const res = await fetch(`/api/label/search?${q.toString()}`);
    if (!res.ok) {
      setError(`search failed: ${res.status}`);
      return;
    }
    setPage((await res.json()) as SearchPage);
  }

  async function skip() {
    if (!item) return;
    setError(null);
    const res = await fetch("/api/label/skip", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        draft_id: item.draft_id,
        labeler: labeler.trim(),
        reason: skipReason.trim() || null,
      }),
    });
    if (!res.ok) {
      setError(`skip failed: ${res.status} ${await res.text()}`);
      return;
    }
    setSkippedMsg(
      "Skipped for now. Nothing was labeled and the proposal stays hidden.",
    );
    await loadQueue();
  }

  async function submit() {
    if (!item || answer === "") return;
    const abstain = answer === "abstain";
    setError(null);
    try {
      localStorage.setItem(LABELER_KEY, labeler.trim());
    } catch {
      /* storage unavailable */
    }
    const res = await fetch("/api/label/submit", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        draft_id: item.draft_id,
        labeler: labeler.trim(),
        expected: answer,
        gold_edition_ids: abstain
          ? reason === "underspecified"
            ? gold
            : []
          : gold,
        ambiguity_reason: abstain ? reason : null,
        notes: notes.trim() || null,
      }),
    });
    if (!res.ok) {
      setError(`submit failed: ${res.status} ${await res.text()}`);
      return;
    }
    const body = (await res.json()) as Reveal & {
      reveal?: string;
      remaining?: number;
    };
    if (body.reveal === "after_batch" || body.reveal === "never")
      setDeferred(body.remaining ?? 0);
    else setReveal(body);
    await loadQueue();
  }

  async function showBatch() {
    setError(null);
    const res = await fetch("/api/label/reveal");
    if (!res.ok) {
      setError(`reveal refused: ${res.status} ${await res.text()}`);
      return;
    }
    setBatch((await res.json()) as BatchReveal);
    await loadQueue();
  }

  if (error && !queue)
    return (
      <p role="alert" className="error">
        {error}
      </p>
    );
  if (!queue) return <p>Loading queue…</p>;
  if (!item) return <p>The queue is empty.</p>;

  return (
    <section aria-label="Labeling">
      <details
        className="howto"
        open={(queue.independent ?? queue.labeled) === 0}
      >
        <summary>What am I deciding?</summary>
        <p>
          Someone typed the query below while trying to identify one specific
          printed edition. Your job is to say what the correct output should be,
          using only what the query says:
        </p>
        <ul>
          <li>
            <b>One edition</b>: exactly one catalog record fits, and every other
            plausible record is ruled out by something the query actually says
            (for example a different year or format). Tick that one record.
          </li>
          <li>
            <b>Human review (abstain)</b>: more than one record could be the
            right one, the book is not in the catalog, or the query contradicts
            itself. Pick a reason.
          </li>
          <li>
            Missing information is <b>unknown</b>, not a difference: a record
            with no year or format could still be the one. Tick several records
            only if you have positive evidence that they are the same edition.
          </li>
          <li>
            <b>Skip for now</b> if you cannot assess the case yet. A skip is not
            a label.
          </li>
        </ul>
        <p className="muted small">
          Search results are unranked. The program's drafted proposal stays
          hidden until you save your own label.
        </p>
      </details>
      <p className="muted">
        Development queue · {queue.independent ?? queue.labeled} independent
        labels · {queue.practice ?? 0} practice (not counted) ·{" "}
        {queue.exposed ?? 0} exposed before labeling (not counted) ·{" "}
        {queue.skipped ?? 0} skipped · {queue.total} cases. Held-out cases are
        not served here.
      </p>
      <div className="actions">
        <button
          type="button"
          className="secondary"
          disabled={idx === 0}
          onClick={() => setIdx(idx - 1)}
        >
          ← Previous
        </button>
        <span>
          {item.draft_id} ({idx + 1}/{queue.total}) ·{" "}
          {item.status ?? (item.labeled ? "labeled" : "unlabeled")}
          {item.status === "practice"
            ? " (AI-assisted practice, not counted)"
            : ""}
          {item.status === "exposed"
            ? item.labeled
              ? " (labeled; exposed before labeling, not counted)"
              : " (exposed before labeling: a label here will not count as independent)"
            : ""}
        </span>
        <button
          type="button"
          className="secondary"
          disabled={idx >= queue.total - 1}
          onClick={() => setIdx(idx + 1)}
        >
          Next →
        </button>
      </div>
      <div className="candidate">
        <h2>Query as a person typed it</h2>
        <table className="checks">
          <tbody>
            {Object.entries(item.query).map(([k, val]) => (
              <tr key={k}>
                <td>{k}</td>
                <td>{v(String(val))}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted small">
          Fields not listed were not given in this query.
        </p>
      </div>

      <div className="query">
        <label className="wide">
          <span>
            Search the catalog: every word must appear in a title, subtitle or
            original title
          </span>
          <input
            value={search}
            maxLength={200}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <div className="actions">
          <button
            type="button"
            onClick={() => runSearch(0)}
            disabled={search.trim().length < 2}
          >
            Search
          </button>
        </div>
      </div>

      {page && (
        <div className="actions" role="status">
          <span>
            {page.total === 0
              ? "No catalog records match."
              : `Showing ${page.offset + 1}–${page.offset + page.returned} of ${page.total} matching records`}
            {page.truncated
              ? " (more on the next page)"
              : page.total > 0
                ? " (all shown)"
                : ""}{" "}
            · {page.order}
          </span>
          <button
            type="button"
            className="secondary"
            disabled={page.offset === 0}
            onClick={() => runSearch(Math.max(0, page.offset - PAGE))}
          >
            ← Prev page
          </button>
          <button
            type="button"
            className="secondary"
            disabled={!page.truncated}
            onClick={() => runSearch(page.offset + PAGE)}
          >
            Next page →
          </button>
        </div>
      )}

      {rows.length > 0 && (
        <table className="checks" aria-label="Catalog records">
          <thead>
            <tr>
              <th>pick</th>
              <th>edition</th>
              <th>title</th>
              <th>authors</th>
              <th>publisher · year · format</th>
              <th>edition · lang</th>
              <th>ISBN</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.edition_id}>
                <td>
                  <input
                    type="checkbox"
                    aria-label={`pick ${r.edition_id}`}
                    checked={gold.includes(r.edition_id)}
                    onChange={(e) =>
                      setGold(
                        e.target.checked
                          ? [...gold, r.edition_id]
                          : gold.filter((g) => g !== r.edition_id),
                      )
                    }
                  />
                </td>
                <td>{r.edition_id}</td>
                <td>
                  {v(r.title)}
                  {r.subtitle && (
                    <span className="muted">: {v(r.subtitle)}</span>
                  )}
                </td>
                <td>{r.authors.map(v).join("; ")}</td>
                <td>
                  {r.publishers.map(v).join("; ")} · {r.publish_year ?? "?"} ·{" "}
                  {r.physical_format}
                </td>
                <td>
                  {v(r.edition_name)} · {r.languages.join(",")}
                </td>
                <td>{[...r.isbn_13, ...r.isbn_10].join(" ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="query">
        <fieldset className="wide" aria-label="Your answer">
          <legend>Your answer (required)</legend>
          <label>
            <input
              type="radio"
              name="answer"
              value="suggest"
              checked={answer === "suggest"}
              onChange={() => setAnswer("suggest")}
            />{" "}
            One specific edition (tick one or more matching records above)
          </label>
          <label>
            <input
              type="radio"
              name="answer"
              value="abstain"
              checked={answer === "abstain"}
              onChange={() => setAnswer("abstain")}
            />{" "}
            Human review (abstain): choose a reason
          </label>
        </fieldset>
        {answer === "abstain" && (
          <label>
            <span>Reason</span>
            <select value={reason} onChange={(e) => setReason(e.target.value)}>
              <option value="">choose…</option>
              {queue.reasons.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          <span>Your labeler id</span>
          <input
            value={labeler}
            maxLength={40}
            onChange={(e) => setLabeler(e.target.value)}
          />
        </label>
        <label className="wide">
          <span>Notes (optional)</span>
          <input
            value={notes}
            maxLength={500}
            onChange={(e) => setNotes(e.target.value)}
          />
        </label>
        <div className="actions">
          <span className="muted">picked: {gold.join(", ") || "none"}</span>
          <button type="button" onClick={submit} disabled={!canSubmit}>
            Save label
          </button>
        </div>
        <label className="wide">
          <span>Skip reason (optional)</span>
          <input
            value={skipReason}
            maxLength={300}
            onChange={(e) => setSkipReason(e.target.value)}
          />
        </label>
        <div className="actions">
          <button
            type="button"
            className="secondary"
            onClick={skip}
            disabled={labeler.trim() === "" || !!reveal}
          >
            Skip for now
          </button>
        </div>
      </div>
      {skippedMsg && <p role="status">{skippedMsg}</p>}

      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {deferred !== null && (
        <p role="status">
          {queue.reveal_mode === "never"
            ? `Saved. Drafted proposals are never shown for this queue (${deferred} remaining).`
            : `Saved. Drafted proposals stay hidden until every case in this batch is labeled (${deferred} remaining).`}
        </p>
      )}
      {queue.reveal_mode === "after_batch" && queue.labeled === queue.total && (
        <div className="query">
          <p className="muted">
            Every case is labeled.{" "}
            {queue.revealed
              ? "Proposals were revealed; labels are final."
              : "Showing the drafted proposals makes your labels final."}
          </p>
          <button type="button" onClick={showBatch}>
            Show drafted proposals for the whole batch
          </button>
        </div>
      )}
      {batch && (
        <div className="query">
          <p className="muted small">
            {batch.agree}/{batch.total} match your labels. {batch.note}.
          </p>
          <table>
            <thead>
              <tr>
                <th>case</th>
                <th>your label</th>
                <th>drafted proposal</th>
                <th>template</th>
              </tr>
            </thead>
            <tbody>
              {batch.items.map((x) => (
                <tr key={x.draft_id}>
                  <td>{x.draft_id}</td>
                  <td>
                    {x.your_label.expected}{" "}
                    {x.your_label.gold_edition_ids.join(", ")}
                    {x.your_label.ambiguity_reason
                      ? ` (${x.your_label.ambiguity_reason})`
                      : ""}
                  </td>
                  <td className={x.agrees_with_proposal ? "ok" : "warn"}>
                    {x.proposed.expected}{" "}
                    {x.proposed.gold_edition_ids.join(", ")}
                    {x.proposed.ambiguity_reason
                      ? ` (${x.proposed.ambiguity_reason})`
                      : ""}
                  </td>
                  <td>
                    {x.template ?? ""}
                    {x.template_note ? ` · ${x.template_note}` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {reveal && (
        <p
          role="status"
          className={reveal.agrees_with_proposal ? "ok" : "warn"}
        >
          Saved. Drafted proposal (label spec{" "}
          {reveal.proposal_label_spec ?? "unrecorded"}):{" "}
          {reveal.proposed.expected}{" "}
          {reveal.proposed.gold_edition_ids.join(", ") || ""}
          {reveal.proposed.ambiguity_reason
            ? ` (${reveal.proposed.ambiguity_reason})`
            : ""}{" "}
          ·{" "}
          {reveal.agrees_with_proposal
            ? "matches your label"
            : "differs from your label (your label is kept)"}
          {reveal.template ? ` · Generator template: ${reveal.template}` : ""}
          {reveal.template_note ? ` · ${reveal.template_note}` : ""}
        </p>
      )}
    </section>
  );
}
