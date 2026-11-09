import { useEffect, useState } from "react";
import { type AppInfo, type QueryInput, type ResolveResponse, getAppInfo, resolveQuery } from "./api";
import { LabelView } from "./LabelView";
import { Result } from "./Result";

const FIELDS: { key: keyof QueryInput; label: string; placeholder: string }[] = [
  { key: "isbn", label: "ISBN", placeholder: "978-… or 10-digit" },
  { key: "title", label: "Title", placeholder: "The Lantern Keeper's Daughter" },
  { key: "author", label: "Author", placeholder: "Mara Ellison" },
  { key: "physical_format", label: "Format", placeholder: "hardcover, paperback…" },
  { key: "publish_year", label: "Year", placeholder: "2012" },
  { key: "publisher", label: "Publisher", placeholder: "" },
  { key: "language", label: "Language", placeholder: "English, Spanish…" },
  { key: "edition", label: "Edition", placeholder: "2nd edition" },
];

export function buildQuery(form: Record<string, string>): QueryInput {
  const q: QueryInput = {};
  for (const [k, raw] of Object.entries(form)) {
    const v = raw.trim();
    if (!v) continue;
    if (k === "publish_year") {
      const n = Number.parseInt(v, 10);
      if (Number.isFinite(n)) q.publish_year = n;
    } else {
      (q as Record<string, string>)[k] = v;
    }
  }
  return q;
}

export default function App() {
  const [form, setForm] = useState<Record<string, string>>({});
  const [result, setResult] = useState<ResolveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState<"resolve" | "label">("resolve");
  const [labelEnabled, setLabelEnabled] = useState(false);
  // Unknown until /api/health answers; feedback stays hidden unless the server says it is
  // not a public demo (fail closed).
  const [info, setInfo] = useState<AppInfo | null>(null);

  useEffect(() => {
    getAppInfo()
      .then(setInfo)
      .catch(() => setInfo(null));
  }, []);

  useEffect(() => {
    // The labeling route does not exist in the public demo; only ask a local server.
    if (info === null || info.publicDemo) {
      setLabelEnabled(false);
      return;
    }
    fetch("/api/label/enabled")
      .then((r) => (r.ok ? r.json() : { enabled: false }))
      .then((j: { enabled?: boolean }) => setLabelEnabled(Boolean(j.enabled)))
      .catch(() => setLabelEnabled(false));
  }, [info]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setResult(await resolveQuery(buildQuery(form)));
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <header>
        <h1>
          Edition Resolution Review
          {info?.publicDemo && <span className="badge demo">Public demo</span>}
        </h1>
        <p className="muted" data-testid="disclaimer">
          Decision support only. Suggestions are not confirmed matches, and nothing is listed,
          priced or changed. A human reviewer makes the final decision.
        </p>
      </header>
      {labelEnabled && (
        <nav className="actions" aria-label="Mode">
          <button type="button" aria-pressed={tab === "resolve"} onClick={() => setTab("resolve")}>
            Resolve
          </button>
          <button type="button" aria-pressed={tab === "label"} onClick={() => setTab("label")}>
            Label dev cases
          </button>
        </nav>
      )}
      {tab === "label" ? (
        <LabelView />
      ) : (
      <>
      <form className="query" onSubmit={onSubmit} aria-label="Book description">
        {FIELDS.map((f) => (
          <label key={f.key}>
            <span>{f.label}</span>
            <input
              name={f.key}
              value={form[f.key] ?? ""}
              placeholder={f.placeholder}
              maxLength={f.key === "publish_year" ? 4 : 2000}
              inputMode={f.key === "publish_year" ? "numeric" : undefined}
              onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
            />
          </label>
        ))}
        <label className="wide">
          <span>Free text</span>
          <textarea
            name="free_text"
            rows={2}
            maxLength={2000}
            value={form.free_text ?? ""}
            placeholder="Anything else: damaged barcode, words from the cover…"
            onChange={(e) => setForm({ ...form, free_text: e.target.value })}
          />
        </label>
        <div className="actions">
          <button type="submit" disabled={busy}>
            {busy ? "Resolving…" : "Resolve"}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => {
              setForm({});
              setResult(null);
              setError(null);
            }}
          >
            Clear
          </button>
        </div>
      </form>

      {error && (
        <p role="alert" className="error">
          Request failed: {error}
        </p>
      )}
      {result && (
        <Result
          key={result.request_id}
          result={result}
          feedbackEnabled={info !== null && !info.publicDemo}
        />
      )}
      </>
      )}
      <footer className="muted small" data-testid="attribution">
        {info?.openLibrary ? (
          <p>
            Catalog: a derived subset of factual fields from the{" "}
            <a href="https://openlibrary.org/" rel="noopener noreferrer">
              Open Library
            </a>{" "}
            data dump dated 2026-10-31 (Internet Archive). Records may be incomplete or wrong;
            see DATA_NOTICE.md in the project repository.
          </p>
        ) : (
          <p>Catalog: local data (see the project README and DATA_NOTICE.md).</p>
        )}
        {info?.publicDemo && (
          <p>
            Public demo of a portfolio project. BERA does not store your queries; no account,
            listing or purchase is involved.
          </p>
        )}
      </footer>
    </main>
  );
}
