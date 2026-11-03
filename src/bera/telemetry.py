"""Local request tracing WITHOUT raw query text, plus the local feedback store.

Stored per request: id, time, HMAC-SHA256 of the canonical query (keyed with a local random
salt so equal queries can be grouped without revealing them), which fields were present,
route, outcome, reasons, candidate edition ids, stage timings, adjudication status/provider/
attempts/tokens, and Unicode flag names. Never stored: raw query text, model reasoning text.

Feedback (confirm/reject) is a SEPARATE table and is never mixed into benchmark labels.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from bera.models import FeedbackDecision, Query, ResolveResponse

SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
    request_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    query_hmac TEXT NOT NULL,
    fields_present TEXT NOT NULL,
    route TEXT NOT NULL,
    outcome TEXT NOT NULL,
    reasons TEXT NOT NULL,
    candidate_ids TEXT NOT NULL,
    timings_ms TEXT NOT NULL,
    adjudication_status TEXT NOT NULL,
    provider TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    unicode_flags TEXT NOT NULL,
    policy_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL REFERENCES traces(request_id),
    edition_id TEXT,
    decision TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""


def _load_or_create_salt(path: Path) -> bytes:
    if path.exists():
        return path.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    salt = secrets.token_bytes(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(salt)
    return salt


class TraceStore:
    def __init__(self, db_path: Path, salt_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._salt = _load_or_create_salt(salt_path)
        with self._connect() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def query_hmac(self, query: Query) -> str:
        canonical = json.dumps(query.model_dump(), sort_keys=True, ensure_ascii=False)
        return hmac.new(self._salt, canonical.encode(), hashlib.sha256).hexdigest()

    def record(self, query: Query, resp: ResolveResponse) -> None:
        present = sorted(k for k, v in query.model_dump().items() if v not in (None, ""))
        adj = resp.adjudication
        with self._connect() as con:
            con.execute(
                "INSERT INTO traces VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    resp.request_id,
                    time.time(),
                    self.query_hmac(query),
                    json.dumps(present),
                    resp.route.value,
                    resp.outcome.value,
                    json.dumps([r.value for r in resp.reasons]),
                    json.dumps([c.edition.edition_id for c in resp.candidates]),
                    json.dumps(resp.timings_ms),
                    adj.status.value,
                    adj.provider,
                    adj.attempts,
                    adj.input_tokens,
                    adj.output_tokens,
                    json.dumps(sorted(set(resp.query_unicode_flags))),
                    resp.policy_version,
                ),
            )

    def candidate_ids(self, request_id: str) -> list[str] | None:
        with self._connect() as con:
            row = con.execute(
                "SELECT candidate_ids FROM traces WHERE request_id = ?", (request_id,)
            ).fetchone()
        return None if row is None else list(json.loads(row["candidate_ids"]))

    def add_feedback(
        self, request_id: str, edition_id: str | None, decision: FeedbackDecision
    ) -> int:
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO feedback (request_id, edition_id, decision, created_at) "
                "VALUES (?,?,?,?)",
                (request_id, edition_id, decision.value, time.time()),
            )
            return int(cur.lastrowid or 0)

    def summary(self) -> dict[str, object]:
        with self._connect() as con:
            outcomes = {
                r["outcome"]: r["n"]
                for r in con.execute("SELECT outcome, COUNT(*) n FROM traces GROUP BY outcome")
            }
            routes = {
                r["route"]: r["n"]
                for r in con.execute("SELECT route, COUNT(*) n FROM traces GROUP BY route")
            }
            fb = {
                r["decision"]: r["n"]
                for r in con.execute("SELECT decision, COUNT(*) n FROM feedback GROUP BY decision")
            }
        return {"outcomes": outcomes, "routes": routes, "feedback": fb}

    def raw_rows(self) -> list[dict[str, object]]:
        """For tests/audits: every stored column, to prove no raw text is persisted."""
        with self._connect() as con:
            return [dict(r) for r in con.execute("SELECT * FROM traces")]
