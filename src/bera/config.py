"""Runtime settings from environment variables. Defaults are safe: no LLM, local files only."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    var_dir: Path
    catalog_db: Path
    llm_provider: str  # "none" | "mock"
    mock_mode: str

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
        if provider not in {"none", "mock"}:
            raise ValueError(f"unsupported BERA_LLM_PROVIDER={provider!r} (allowed: none, mock)")
        return cls(
            var_dir=var_dir,
            catalog_db=Path(os.environ.get("BERA_CATALOG_DB", var_dir / "catalog.sqlite")),
            llm_provider=provider,
            mock_mode=os.environ.get("BERA_MOCK_MODE", "cite_first"),
        )
