"""Bounded adjudication runner.

Budget (docs/THREAT_MODEL.md):
- one logical adjudication per request, at most MAX_ATTEMPTS = 2 provider attempts
- retry ONLY on transport errors/timeouts, and only if >= MIN_RETRY_BUDGET_S remains
- NEVER retry on schema or evidence failure (resampling until it passes is a bypass)
- per-attempt timeout 8 s, stage deadline 12 s, input <= 3000 est. tokens, output <= 400
Any failure yields a status that the policy maps to human review.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import ValidationError

from bera.evidence import ABSTAIN, validate_output
from bera.llm.prompt import build_messages, estimate_tokens, output_json_schema
from bera.llm.provider import (
    AdjudicationRequest,
    LLMProvider,
    ProviderError,
    ProviderTransportError,
)
from bera.models import (
    AdjudicationOutput,
    AdjudicationStatus,
    AdjudicationView,
    Edition,
    Query,
)

MAX_ATTEMPTS = 2
PER_ATTEMPT_TIMEOUT_S = 8.0
STAGE_DEADLINE_S = 12.0
MIN_RETRY_BUDGET_S = 4.0
RETRY_BACKOFF_S = 0.25
MAX_INPUT_TOKENS = 3000
MAX_OUTPUT_TOKENS = 400
MAX_RAW_OUTPUT_CHARS = 8000


@dataclass
class Adjudicator:
    provider: LLMProvider
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep

    def run(self, request_id: str, query: Query, refs: dict[str, Edition]) -> AdjudicationView:
        name = self.provider.name
        messages = build_messages(query, refs)
        est = estimate_tokens(messages)
        if est > MAX_INPUT_TOKENS:
            return AdjudicationView(
                status=AdjudicationStatus.BUDGET,
                provider=name,
                validation_errors=[f"estimated input tokens {est} > {MAX_INPUT_TOKENS}"],
            )
        req = AdjudicationRequest(
            request_id, messages, output_json_schema(), dict(refs), MAX_OUTPUT_TOKENS
        )
        start = self.clock()
        attempts = 0
        last_error = ""
        while attempts < MAX_ATTEMPTS:
            remaining = STAGE_DEADLINE_S - (self.clock() - start)
            if attempts > 0 and remaining < MIN_RETRY_BUDGET_S:
                return AdjudicationView(
                    status=AdjudicationStatus.DEADLINE,
                    provider=name,
                    attempts=attempts,
                    validation_errors=[last_error],
                )
            attempts += 1
            try:
                resp = self.provider.complete(req, min(PER_ATTEMPT_TIMEOUT_S, remaining))
            except ProviderTransportError as exc:
                last_error = f"transport: {type(exc).__name__}"
                if attempts < MAX_ATTEMPTS:
                    self.sleep(RETRY_BACKOFF_S)
                continue
            except ProviderError as exc:
                return AdjudicationView(
                    status=AdjudicationStatus.PROVIDER_ERROR,
                    provider=name,
                    attempts=attempts,
                    validation_errors=[f"provider: {type(exc).__name__}"],
                )
            if self.clock() - start > STAGE_DEADLINE_S:
                return AdjudicationView(
                    status=AdjudicationStatus.DEADLINE,
                    provider=name,
                    attempts=attempts,
                    validation_errors=["stage deadline exceeded"],
                )
            return self._validate(
                resp.text, refs, name, attempts, resp.input_tokens, resp.output_tokens
            )
        return AdjudicationView(
            status=AdjudicationStatus.PROVIDER_ERROR,
            provider=name,
            attempts=attempts,
            validation_errors=[last_error or "no attempts"],
        )

    @staticmethod
    def _validate(
        text: str,
        refs: dict[str, Edition],
        name: str,
        attempts: int,
        in_tok: int | None,
        out_tok: int | None,
    ) -> AdjudicationView:
        def view(
            status: AdjudicationStatus,
            errors: list[str],
            out: AdjudicationOutput | None = None,
            chosen: str | None = None,
        ) -> AdjudicationView:
            return AdjudicationView(
                status=status,
                provider=name,
                attempts=attempts,
                output=out,
                chosen_edition_id=chosen,
                validation_errors=errors,
                input_tokens=in_tok,
                output_tokens=out_tok,
            )

        if len(text) > MAX_RAW_OUTPUT_CHARS:
            return view(AdjudicationStatus.INVALID_OUTPUT, ["output too long"])
        try:
            out = AdjudicationOutput.model_validate_json(text, strict=True)
        except ValidationError as exc:
            errs = [f"{'.'.join(map(str, e['loc']))}: {e['type']}" for e in exc.errors()[:8]]
            return view(AdjudicationStatus.INVALID_OUTPUT, errs)
        errors = validate_output(out, refs)
        if errors:
            return view(AdjudicationStatus.EVIDENCE_INVALID, errors, out)
        chosen = None if out.choice == ABSTAIN else refs[out.choice].edition_id
        return view(AdjudicationStatus.COMPLETED, [], out, chosen)
