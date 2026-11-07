"""Resolution pipeline: normalize -> ISBN -> retrieve -> check -> decide -> adjudicate -> trace."""

from __future__ import annotations

import re
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass

from bera import isbn as isbnlib
from bera.catalog import Catalog
from bera.features import check_fields
from bera.llm.adjudicator import Adjudicator
from bera.llm.provider import LLMProvider
from bera.llm.routes import CLOSED_GATE, GATE_ELIGIBLE_REASONS, RouteGate, route_of
from bera.models import (
    MAX_ADJUDICATION_CANDIDATES,
    MAX_CANDIDATES_RETURNED,
    AdjudicationStatus,
    AdjudicationView,
    CandidateView,
    Capabilities,
    CheckStatus,
    Edition,
    Outcome,
    Query,
    Reason,
    ResolveResponse,
    Route,
)
from bera.policy import (
    CONFIDENCE_STATUS,
    POLICY_VERSION,
    Decision,
    apply_catalog_scan,
    decide,
    is_compatible,
)
from bera.retrieval import FtsBm25Retriever, Reranker, Retriever, TrigramRetriever, rrf_fuse
from bera.telemetry import TraceStore
from bera.text import detect_suspicious

RETRIEVE_K = 50
_ISBN_IN_TEXT = re.compile(r"(?<![\dX])(?:97[89][\d\- ]{10,14}|[\d][\d\- ]{8,11}[\dXx])(?![\dX])")

_ADJ_REASON = {
    AdjudicationStatus.INVALID_OUTPUT: Reason.LLM_OUTPUT_INVALID,
    AdjudicationStatus.EVIDENCE_INVALID: Reason.EVIDENCE_INVALID,
    AdjudicationStatus.PROVIDER_ERROR: Reason.LLM_PROVIDER_ERROR,
    AdjudicationStatus.DEADLINE: Reason.LLM_DEADLINE,
    AdjudicationStatus.BUDGET: Reason.LLM_BUDGET,
}


def extract_isbn_text(query: Query) -> str | None:
    if query.isbn:
        return query.isbn
    if query.free_text:
        m = _ISBN_IN_TEXT.search(query.free_text)
        if m:
            return m.group(0)
    return None


@dataclass
class Resolver:
    catalog: Catalog
    traces: TraceStore | None
    provider: LLMProvider | None
    retrievers: list[Retriever] | None = None
    reranker: Reranker | None = None
    # Validated LLM suggestion path: closed unless built from frozen dev route evidence.
    route_gate: RouteGate = CLOSED_GATE
    clock: Callable[[], float] = time.perf_counter

    def __post_init__(self) -> None:
        if self.retrievers is None:
            self.retrievers = [FtsBm25Retriever(self.catalog), TrigramRetriever(self.catalog)]

    def capabilities(self) -> Capabilities:
        emb = [r for r in self.retrievers or [] if r.name == "embedding"]
        return Capabilities(
            embedding_retrieval=f"active: {getattr(emb[0], 'label', 'embedding')}"
            if emb
            else "not configured in this process",
            reranker=f"active: {self.reranker.label}"
            if self.reranker
            else "not configured in this process",
            llm="disabled"
            if self.provider is None
            else f"{self.provider.name} (test double, not a model)"
            if self.provider.name == "mock"
            else self.provider.name,
            calibration="pending: needs human-labeled dev set + grouped out-of-fold fit",
        )

    def resolve(self, query: Query) -> ResolveResponse:
        request_id = uuid.uuid4().hex
        timings: dict[str, float] = {}
        t0 = self.clock()

        flags: set[str] = set()
        for value in query.text_fields().values():
            if value:
                flags |= {f.value for f in detect_suspicious(value).flags}

        # ---- ISBN stage ------------------------------------------------------------------
        t = self.clock()
        pre: list[Reason] = []
        route = Route.RETRIEVAL
        isbn_ids: list[str] = []
        query_isbn13: str | None = None
        isbn_text = extract_isbn_text(query)
        if isbn_text:
            parsed = isbnlib.parse(isbn_text)
            if parsed.valid and parsed.isbn13:
                query_isbn13 = parsed.isbn13
                isbn_ids = self.catalog.lookup_isbn13(parsed.isbn13)
                if len(isbn_ids) == 1:
                    route = Route.ISBN_EXACT
                elif len(isbn_ids) > 1:
                    route = Route.ISBN_DUPLICATE
                else:
                    pre.append(Reason.ISBN_NOT_IN_CATALOG)
            elif parsed.status is isbnlib.IsbnStatus.BAD_CHECKSUM:
                pre.append(Reason.ISBN_BAD_CHECKSUM)
                for hyp in isbnlib.repair_hypotheses(parsed.compact):
                    isbn_ids.extend(i for i in self.catalog.lookup_isbn13(hyp) if i not in isbn_ids)
                if isbn_ids:
                    route = Route.ISBN_REPAIR
            else:
                pre.append(Reason.ISBN_BAD_FORMAT)
        timings["isbn"] = _ms(self.clock() - t)

        # ---- retrieval stage -------------------------------------------------------------
        t = self.clock()
        rrf: dict[str, tuple[float, list[str]]] = {}
        if route in (Route.RETRIEVAL, Route.ISBN_REPAIR):
            rankings = [r.retrieve(query, RETRIEVE_K) for r in self.retrievers or []]
            rrf = {eid: (s, src) for eid, s, src in rrf_fuse(rankings)}
        timings["retrieval"] = _ms(self.clock() - t)

        # ---- deterministic checks + ordering ---------------------------------------------
        t = self.clock()
        ids = list(dict.fromkeys([*isbn_ids, *list(rrf)[:RETRIEVE_K]]))
        editions = self.catalog.get(ids)
        views = [
            self._view(editions[i], query, query_isbn13, i in isbn_ids, rrf.get(i))
            for i in ids
            if i in editions
        ]
        timings["checks"] = _ms(self.clock() - t)
        t = self.clock()
        if route in (Route.ISBN_EXACT, Route.ISBN_DUPLICATE):
            views.sort(key=lambda v: (v.conflicts, v.edition.edition_id))
        else:
            if self.reranker is not None and views:
                pool = sorted(views, key=lambda v: (-v.lexical_score, v.edition.edition_id))
                pool = pool[: self.reranker.max_candidates]
                scores = self.reranker.score(query, [v.edition for v in pool])
                for v, s in zip(pool, scores, strict=True):
                    v.rerank_score = round(s, 6)
            views.sort(
                key=lambda v: (
                    -(v.agreements - 2 * v.conflicts),
                    -(v.rerank_score if v.rerank_score is not None else float("-inf")),
                    -v.lexical_score,
                    v.edition.edition_id,
                )
            )
        views = views[:MAX_CANDIDATES_RETURNED]
        for rank, v in enumerate(views, start=1):
            v.rank = rank
        timings["rerank_order"] = _ms(self.clock() - t)

        decision = decide(route, views, sorted(flags), pre)
        if route is Route.RETRIEVAL and decision.outcome is Outcome.SUGGEST:
            t = self.clock()
            decision, views = self._catalog_scan(decision, views, query)
            timings["catalog_scan"] = _ms(self.clock() - t)
        reasons = list(decision.reasons)
        outcome, suggested = decision.outcome, decision.suggested

        # ---- adjudication: advisory unless its route is open in the frozen route gate -----
        t = self.clock()
        adjudication = AdjudicationView(
            status=AdjudicationStatus.NOT_NEEDED,
            provider=self.provider.name if self.provider else "none",
        )
        if decision.ambiguous_ids:
            if self.provider is None:
                adjudication = AdjudicationView(status=AdjudicationStatus.DISABLED, provider="none")
                reasons.append(Reason.LLM_DISABLED)
            else:
                by_id = {v.edition.edition_id: v for v in views}
                amb = [i for i in decision.ambiguous_ids if i in by_id][
                    :MAX_ADJUDICATION_CANDIDATES
                ]
                refs: dict[str, Edition] = {}
                for n, eid in enumerate(amb, start=1):
                    ref = f"c{n}"
                    by_id[eid].candidate_ref = ref
                    refs[ref] = by_id[eid].edition
                adjudication = Adjudicator(self.provider).run(request_id, query, refs)
                if adjudication.status is AdjudicationStatus.COMPLETED:
                    if adjudication.chosen_edition_id is None:
                        reasons.append(Reason.LLM_ABSTAINED)
                    else:
                        adjudication.agrees_with_top1 = adjudication.chosen_edition_id == amb[0]
                        chosen = by_id.get(adjudication.chosen_edition_id)
                        llm_route = route_of(
                            adjudication.chosen_edition_id,
                            views[0].edition.edition_id if views else None,
                        )
                        if (
                            llm_route in self.route_gate.open_routes
                            and set(decision.reasons) <= GATE_ELIGIBLE_REASONS
                            and chosen is not None
                            and is_compatible(chosen)
                            and not flags
                        ):
                            outcome = Outcome.SUGGEST
                            suggested = adjudication.chosen_edition_id
                            reasons.append(Reason.LLM_VALIDATED_ROUTE)
                        else:
                            reasons.append(Reason.LLM_ADVISORY_ONLY)
                else:
                    reasons.append(_ADJ_REASON[adjudication.status])
        timings["adjudication"] = _ms(self.clock() - t)
        timings["total"] = _ms(self.clock() - t0)

        resp = ResolveResponse(
            request_id=request_id,
            outcome=outcome,
            suggested_edition_id=suggested,
            route=route,
            reasons=list(dict.fromkeys(reasons)),
            candidates=views,
            adjudication=adjudication,
            query_unicode_flags=sorted(flags),
            confidence_status=CONFIDENCE_STATUS,
            capabilities=self.capabilities(),
            policy_version=POLICY_VERSION,
            timings_ms=timings,
        )
        if self.traces is not None:
            self.traces.record(query, resp)
        return resp

    def _catalog_scan(
        self, decision: Decision, views: list[CandidateView], query: Query
    ) -> tuple[Decision, list[CandidateView]]:
        """Uniqueness across the catalog, not just the retrieved list (policy v1)."""
        sugg = next(v for v in views if v.edition.edition_id == decision.suggested)
        pool, complete = self.catalog.ambiguity_pool(sugg.edition.title, sugg.edition.work_id)
        seen = {v.edition.edition_id for v in views}
        extra = self.catalog.get(i for i in pool if i not in seen)
        alts = [self._view(extra[i], query, None, False, None) for i in sorted(extra)]
        alts = [a for a in alts if is_compatible(a)]
        for a in alts:
            a.retrieval_sources = ["catalog_ambiguity_scan"]
        new = apply_catalog_scan(decision, alts, complete)
        if new.outcome is Outcome.SUGGEST:
            return new, views
        shown = alts[:4]
        keep = [v for v in views if v.edition.edition_id in new.ambiguous_ids]
        rest = [v for v in views if v not in keep]
        merged = (keep + shown + rest)[:MAX_CANDIDATES_RETURNED]
        for rank, v in enumerate(merged, start=1):
            v.rank = rank
        return new, merged

    @staticmethod
    def _view(
        e: Edition,
        query: Query,
        query_isbn13: str | None,
        from_isbn: bool,
        rrf: tuple[float, list[str]] | None,
    ) -> CandidateView:
        checks = check_fields(query, e, query_isbn13)
        uflags: set[str] = set()
        for value in (e.title, e.subtitle, *e.authors, *e.publishers, e.edition_name):
            if value:
                uflags |= {f.value for f in detect_suspicious(value).flags}
        sources = (["isbn_index"] if from_isbn else []) + (rrf[1] if rrf else [])
        return CandidateView(
            rank=0,
            edition=e,
            retrieval_sources=sources,
            lexical_score=round(rrf[0], 6) if rrf else 0.0,
            checks=checks,
            conflicts=sum(c.status is CheckStatus.DISAGREE for c in checks),
            agreements=sum(c.status is CheckStatus.AGREE for c in checks),
            unicode_flags=sorted(uflags),
        )


def _ms(seconds: float) -> float:
    return round(seconds * 1000, 3)
