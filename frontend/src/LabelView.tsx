import { useEffect, useMemo, useState } from "react";
import { visibleEscape as v } from "./visible";

interface QueueItem {
  draft_id: string;
  split: string;
  query: Record<string, string | number>;
  template: string;
  labeled: boolean;
}
interface Queue {
  items: QueueItem[];
  reasons: string[];
  labeled: number;
  total: number;
}
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
  proposed: { expected: string; gold_edition_ids: string[]; ambiguity_reason?: string | null };
  agrees_with_proposal: boolean;
}

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
  const [rows, setRows] = useState<Row[]>([]);
  const [gold, setGold] = useState<string[]>([]);
  const [abstain, setAbstain] = useState(false);
  const [reason, setReason] = useState("");
  const [labeler, setLabeler] = useState(readLabeler);
  const [notes, setNotes] = useState("");
  const [reveal, setReveal] = useState<Reveal | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadQueue() {
    const res = await fetch("/api/label/queue");
    if (!res.ok) throw new Error(`queue: ${res.status}`);
    setQueue((await res.json()) as Queue);
  }
  useEffect(() => {
    loadQueue().catch((e: unknown) => setError(String(e)));
  }, []);

  const item = queue?.items[idx];
  useEffect(() => {
    setGold([]);
    setAbstain(false);
    setReason("");
    setNotes("");
    setReveal(null);
    setRows([]);
    setSearch(typeof item?.query.title === "string" ? item.query.title.slice(0, 40) : "");
  }, [item?.draft_id]);

  const canSubmit = useMemo(
    () => labeler.trim() !== "" && (abstain ? reason !== "" : gold.length > 0) && !reveal,
    [labeler, abstain, reason, gold, reveal],
  );

  async function runSearch() {
    setError(null);
    const res = await fetch(`/api/label/search?title=${encodeURIComponent(search.trim())}`);
    if (!res.ok) {
      setError(`search failed: ${res.status}`);
      return;
    }
    setRows((await res.json()) as Row[]);
  }

  async function submit() {
    if (!item) return;
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
        expected: abstain ? "abstain" : "suggest",
        gold_edition_ids: abstain ? (reason === "underspecified" ? gold : []) : gold,
        ambiguity_reason: abstain ? reason : null,
        notes: notes.trim() || null,
      }),
    });
    if (!res.ok) {
      setError(`submit failed: ${res.status} ${await res.text()}`);
      return;
    }
    setReveal((await res.json()) as Reveal);
    await loadQueue();
  }

  if (error && !queue) return <p role="alert" className="error">{error}</p>;
  if (!queue) return <p>Loading queue…</p>;
  if (!item) return <p>The queue is empty.</p>;

  return (
    <section aria-label="Labeling">
      <p className="muted">
        Development queue · {queue.labeled}/{queue.total} labeled · held-out cases are not served
        here. Decide on your own first; the drafted proposal is shown only after you submit.
      </p>
      <div className="actions">
        <button type="button" className="secondary" disabled={idx === 0} onClick={() => setIdx(idx - 1)}>
          ← Previous
        </button>
        <span>
          {item.draft_id} ({idx + 1}/{queue.total}) {item.labeled ? "· labeled" : ""}
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
        <p className="muted small">template: {item.template}</p>
      </div>

      <div className="query">
        <label className="wide">
          <span>Search the catalog by title (alphabetical, unranked)</span>
          <input value={search} maxLength={200} onChange={(e) => setSearch(e.target.value)} />
        </label>
        <div className="actions">
          <button type="button" onClick={runSearch} disabled={search.trim().length < 2}>
            Search
          </button>
        </div>
      </div>

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
                  {r.subtitle && <span className="muted">: {v(r.subtitle)}</span>}
                </td>
                <td>{r.authors.map(v).join("; ")}</td>
                <td>
                  {r.publishers.map(v).join("; ")} · {r.publish_year ?? "?"} · {r.physical_format}
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
        <label>
          <span>
            <input type="checkbox" checked={abstain} onChange={(e) => setAbstain(e.target.checked)} />{" "}
            Correct behavior is human review (abstain)
          </span>
        </label>
        {abstain && (
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
          <input value={labeler} maxLength={40} onChange={(e) => setLabeler(e.target.value)} />
        </label>
        <label className="wide">
          <span>Notes (optional)</span>
          <input value={notes} maxLength={500} onChange={(e) => setNotes(e.target.value)} />
        </label>
        <div className="actions">
          <span className="muted">picked: {gold.join(", ") || "none"}</span>
          <button type="button" onClick={submit} disabled={!canSubmit}>
            Save label
          </button>
        </div>
      </div>

      {error && <p role="alert" className="error">{error}</p>}
      {reveal && (
        <p role="status" className={reveal.agrees_with_proposal ? "ok" : "warn"}>
          Saved. Drafted proposal: {reveal.proposed.expected}{" "}
          {reveal.proposed.gold_edition_ids.join(", ") || ""}
          {reveal.proposed.ambiguity_reason ? ` (${reveal.proposed.ambiguity_reason})` : ""} ·{" "}
          {reveal.agrees_with_proposal ? "matches your label" : "differs from your label (your label is kept)"}
        </p>
      )}
    </section>
  );
}
