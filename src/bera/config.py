"""Runtime settings from environment variables. Defaults are safe: no LLM, local files only.

`BERA_PUBLIC_DEMO=1` switches on the public-demo profile: LLM must stay disabled, the API docs,
feedback, trace-summary and labeling routes are not mounted, nothing is written to disk, the
catalog is opened read-only and must match `BERA_EXPECTED_CATALOG_SHA256` and
`BERA_EXPECTED_EDITIONS`, and HSTS / Permissions-Policy headers are added.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    var_dir: Path
    catalog_db: Path
    llm_provider: str  # "none" | "mock" | "openai_compat"
    mock_mode: str
    llm_base_url: str = "http://127.0.0.1:8080/v1"
    llm_model: str = ""
    label_queue: Path | None = None
    labels_path: Path | None = None
    label_allow_heldout: bool = False
    llm_route_evidence: Path | None = None  # frozen dev route evidence; None = gate closed
    public_demo: bool = False
    expected_catalog_sha256: str | None = None  # sha256 of the corpus the catalog was built from
    expected_editions: int | None = None
    rate_limit_per_minute: int = 30
    rate_limit_burst: int = 10
    trusted_proxy_hops: int = (
        0  # 0 = use the TCP peer; N = N-th X-Forwarded-For entry from the right
    )

    @property
    def trace_db(self) -> Path:
        return self.var_dir / "traces.sqlite"

    @property
    def salt_path(self) -> Path:
        return self.var_dir / "hmac_salt.bin"

    @classmethod
    def from_env(cls) -> Settings:
        var_dir = Path(os.environ.get("BERA_VAR_DIR", REPO_ROOT / "var"))
        provider = os.environ.get("BERA_LLM_PROVIDER", "none").strip().lower()
        if provider not in {"none", "mock", "openai_compat"}:
            raise ValueError(
                f"unsupported BERA_LLM_PROVIDER={provider!r} (allowed: none, mock, openai_compat)"
            )
        public_demo = os.environ.get("BERA_PUBLIC_DEMO", "0").strip() == "1"
        expected_editions = os.environ.get("BERA_EXPECTED_EDITIONS")
        return cls(
            var_dir=var_dir,
            catalog_db=Path(os.environ.get("BERA_CATALOG_DB", var_dir / "catalog.sqlite")),
            llm_provider=provider,
            mock_mode=os.environ.get("BERA_MOCK_MODE", "cite_first"),
            llm_base_url=os.environ.get("BERA_LLM_BASE_URL", "http://127.0.0.1:8080/v1"),
            llm_model=os.environ.get("BERA_LLM_MODEL", ""),
            label_queue=Path(q) if (q := os.environ.get("BERA_LABEL_QUEUE")) else None,
            labels_path=Path(
                os.environ.get(
                    "BERA_LABELS", REPO_ROOT / "data" / "eval" / "labels" / "dev_labels.jsonl"
                )
            ),
            label_allow_heldout=os.environ.get("BERA_LABEL_ALLOW_HELDOUT") == "1",
            llm_route_evidence=Path(r)
            if (r := os.environ.get("BERA_LLM_ROUTE_EVIDENCE"))
            else None,
            public_demo=public_demo,
            expected_catalog_sha256=os.environ.get("BERA_EXPECTED_CATALOG_SHA256") or None,
            expected_editions=int(expected_editions) if expected_editions else None,
            rate_limit_per_minute=int(os.environ.get("BERA_RATE_LIMIT_PER_MINUTE", "30")),
            rate_limit_burst=int(os.environ.get("BERA_RATE_LIMIT_BURST", "10")),
            trusted_proxy_hops=int(os.environ.get("BERA_TRUSTED_PROXY_HOPS", "0")),
        )

    def public_demo_problems(self) -> list[str]:
        """Configuration errors that make the public-demo profile unsafe (empty = ok)."""
        if not self.public_demo:
            return []
        problems = []
        if self.llm_provider != "none":
            problems.append("the LLM must stay disabled (BERA_LLM_PROVIDER=none)")
        if self.label_queue is not None:
            problems.append("labeling must not be enabled (unset BERA_LABEL_QUEUE)")
        if not self.expected_catalog_sha256:
            problems.append("BERA_EXPECTED_CATALOG_SHA256 is required")
        if not self.expected_editions:
            problems.append("BERA_EXPECTED_EDITIONS is required")
        if self.trusted_proxy_hops < 0:
            problems.append("BERA_TRUSTED_PROXY_HOPS must be >= 0")
        return problems
