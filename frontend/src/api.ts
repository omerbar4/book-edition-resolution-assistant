// Typed client for the local BERA API. Mirrors src/bera/models.py.

export type CheckStatus = "agree" | "disagree" | "unknown";

export interface FieldCheck {
  field: string;
  status: CheckStatus;
  query_value: string | null;
  candidate_value: string | null;
  detail: string | null;
}

export interface Edition {
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
  isbn_10: string[];
  isbn_13: string[];
  number_of_pages: number | null;
  translation_of: string | null;
  source: string;
  synthetic: boolean;
}

export interface CandidateView {
  rank: number;
  candidate_ref: string | null;
  edition: Edition;
  retrieval_sources: string[];
  lexical_score: number;
  checks: FieldCheck[];
  conflicts: number;
  agreements: number;
  unicode_flags: string[];
}

export interface EvidenceItem {
  candidate_id: string;
  field: string;
  value: string;
}

export interface AdjudicationView {
  status: string;
  provider: string;
  attempts: number;
  output: {
    choice: string;
    confidence: number;
    decision_reason: string;
    evidence_fields: EvidenceItem[];
    needs_human: boolean;
  } | null;
  chosen_edition_id: string | null;
  agrees_with_top1: boolean | null;
  validation_errors: string[];
}

export interface ResolveResponse {
  request_id: string;
  outcome: "suggest" | "review";
  suggested_edition_id: string | null;
  route: string;
  reasons: string[];
  candidates: CandidateView[];
  adjudication: AdjudicationView;
  query_unicode_flags: string[];
  confidence_status: string;
  capabilities: Record<string, string>;
  policy_version: string;
  timings_ms: Record<string, number>;
  disclaimer: string;
}

export type QueryInput = Partial<{
  isbn: string;
  title: string;
  author: string;
  physical_format: string;
  publish_year: number;
  publisher: string;
  language: string;
  edition: string;
  free_text: string;
}>;

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const j = (await res.json()) as { detail?: unknown };
      detail += `: ${typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail)}`;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export const resolveQuery = (q: QueryInput) => post<ResolveResponse>("/api/resolve", q);

export interface AppInfo {
  publicDemo: boolean;
  openLibrary: boolean;
}

export async function getAppInfo(): Promise<AppInfo> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(`${res.status}`);
  const j = (await res.json()) as {
    public_demo?: unknown;
    catalog_meta?: { sources?: unknown };
  };
  const sources = typeof j.catalog_meta?.sources === "string" ? j.catalog_meta.sources : "";
  return {
    publicDemo: j.public_demo === true,
    openLibrary: sources.split(",").some((s) => s.startsWith("openlibrary")),
  };
}

export const sendFeedback = (
  request_id: string,
  edition_id: string | null,
  decision: "confirm" | "reject",
) => post<{ feedback_id: number }>("/api/feedback", { request_id, edition_id, decision });
