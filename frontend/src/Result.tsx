import { useState } from "react";
import { type CandidateView, type ResolveResponse, sendFeedback } from "./api";
import { visibleEscape as v } from "./visible";

type FeedbackState = { kind: "confirm" | "reject"; editionId: string | null } | null;

export function Result({
  result,
  feedbackEnabled = true,
}: {
  result: ResolveResponse;
  feedbackEnabled?: boolean;
}) {
  const [feedback, setFeedback] = useState<FeedbackState>(null);
  const [fbError, setFbError] = useState<string | null>(null);

  async function record(kind: "confirm" | "reject", editionId: string | null) {
    setFbError(null);
    try {
      await sendFeedback(result.request_id, editionId, kind);
      setFeedback({ kind, editionId });
    } catch (err) {
      setFbError(err instanceof Error ? err.message : String(err));
    }
  }

  const suggested = result.suggested_edition_id;
  const pending = Object.entries(result.capabilities).filter(([, s]) => s.startsWith("pending"));

  return (
    <section className="result" aria-label="Resolution result">
      <div className={`outcome ${result.outcome}`} data-testid="outcome">
        <strong>{result.outcome === "suggest" ? "Suggested match" : "Needs human review"}</strong>
        <span className="muted"> · route: {result.route}</span>
      </div>

      <ul className="reasons" aria-label="Reasons">
        {result.reasons.map((r) => (
          <li key={r}>
            <code>{r}</code>
          </li>
        ))}
      </ul>

      {result.query_unicode_flags.length > 0 && (
        <p className="warn" role="status">
          Query contains suspicious characters: {result.query_unicode_flags.join(", ")}
        </p>
      )}

      <details className="notes">
        <summary>Confidence and capability status</summary>
        <p>{result.confidence_status}</p>
        <ul>
          {pending.map(([k, s]) => (
            <li key={k}>
              {k}: {s}
            </li>
          ))}
          <li>llm: {result.capabilities.llm}</li>
        </ul>
        <p className="muted">
          policy {result.policy_version} · total {result.timings_ms.total?.toFixed(1)} ms
        </p>
      </details>

      <Adjudication result={result} />

      <h2>Candidates ({result.candidates.length})</h2>
      {result.candidates.length === 0 && <p>No candidates found in the local catalog.</p>}
      {result.candidates.map((c) => (
        <Candidate
          key={c.edition.edition_id}
          c={c}
          suggested={c.edition.edition_id === suggested}
          feedback={feedback}
          onFeedback={feedbackEnabled ? record : null}
        />
      ))}

      {feedbackEnabled && (
        <div className="actions">
          <button type="button" className="secondary" onClick={() => record("reject", null)}>
            None of these match
          </button>
        </div>
      )}
      {feedback && (
        <p role="status" className="ok">
          Recorded locally: {feedback.kind}
          {feedback.editionId ? ` ${feedback.editionId}` : " (no candidate)"}. Stored as
          feedback, not as an evaluation label.
        </p>
      )}
      {fbError && (
        <p role="alert" className="error">
          Feedback failed: {fbError}
        </p>
      )}
      <p className="muted small">{result.disclaimer}</p>
    </section>
  );
}

function Adjudication({ result }: { result: ResolveResponse }) {
  const a = result.adjudication;
  if (a.status === "not_needed") return null;
  return (
    <div className="adjudication" aria-label="Adjudication">
      <h2>Adjudication (advisory)</h2>
      <p>
        status <code>{a.status}</code> · provider <code>{a.provider}</code> · attempts {a.attempts}
      </p>
      {a.output && (
        <>
          <p>
            choice <code>{a.output.choice}</code>
            {a.chosen_edition_id && <> → {a.chosen_edition_id}</>} · model-reported confidence{" "}
            {a.output.confidence.toFixed(2)} <span className="muted">(logged only, not used)</span>
          </p>
          <p>
            reason: <q>{v(a.output.decision_reason)}</q>
          </p>
          <h3>Cited evidence</h3>
          <ul>
            {a.output.evidence_fields.map((e, i) => (
              <li key={`${e.candidate_id}-${e.field}-${i}`}>
                <code>
                  {e.candidate_id}.{e.field}
                </code>{" "}
                = <q>{v(e.value)}</q>
              </li>
            ))}
          </ul>
        </>
      )}
      {a.validation_errors.length > 0 && (
        <>
          <h3>Rejected because</h3>
          <ul className="error">
            {a.validation_errors.map((e) => (
              <li key={e}>{v(e)}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function Candidate(props: {
  c: CandidateView;
  suggested: boolean;
  feedback: FeedbackState;
  onFeedback: ((kind: "confirm" | "reject", editionId: string | null) => void) | null;
}) {
  const { c, suggested, feedback, onFeedback } = props;
  const e = c.edition;
  const chosen = feedback?.editionId === e.edition_id ? feedback.kind : null;
  return (
    <article className={`candidate${suggested ? " suggested" : ""}`} aria-label={e.edition_id}>
      <header>
        <span className="rank">#{c.rank}</span>
        {c.candidate_ref && <code className="ref">{c.candidate_ref}</code>}
        <strong>{v(e.title)}</strong>
        {e.subtitle && <span className="subtitle">: {v(e.subtitle)}</span>}
        {suggested && <span className="badge">suggested</span>}
        {e.synthetic && <span className="badge synthetic">synthetic fixture</span>}
      </header>
      <p className="meta">
        {e.authors.map(v).join("; ") || "author unknown"} · {e.publishers.map(v).join("; ") || "—"} ·{" "}
        {e.publish_year ?? "year unknown"} · {e.physical_format}
        {e.edition_name && <> · {v(e.edition_name)}</>} · {e.languages.join(", ") || "lang unknown"}
      </p>
      <p className="meta muted">
        {e.edition_id} · ISBN {[...e.isbn_13, ...e.isbn_10].join(", ") || "none"} · sources{" "}
        {c.retrieval_sources.join("+") || "—"} · uncalibrated lexical score{" "}
        {c.lexical_score.toFixed(4)}
      </p>
      {c.unicode_flags.length > 0 && (
        <p className="warn">Record has suspicious characters: {c.unicode_flags.join(", ")}</p>
      )}
      <table className="checks">
        <thead>
          <tr>
            <th>field</th>
            <th>check</th>
            <th>query</th>
            <th>record</th>
          </tr>
        </thead>
        <tbody>
          {c.checks.map((ch) => (
            <tr key={ch.field} className={ch.status}>
              <td>{ch.field}</td>
              <td>
                {ch.status}
                {ch.detail && <span className="muted"> ({ch.detail})</span>}
              </td>
              <td>{v(ch.query_value)}</td>
              <td>{v(ch.candidate_value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {onFeedback && (
      <div className="actions">
        <button
          type="button"
          onClick={() => onFeedback("confirm", e.edition_id)}
          aria-pressed={chosen === "confirm"}
        >
          Confirm this edition
        </button>
        <button
          type="button"
          className="secondary"
          onClick={() => onFeedback("reject", e.edition_id)}
          aria-pressed={chosen === "reject"}
        >
          Reject
        </button>
      </div>
      )}
    </article>
  );
}
