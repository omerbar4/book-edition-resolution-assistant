"""Reproducible corpus construction from Open Library dumps.

Pass 1  stream editions -> per-edition feature rows in a scratch SQLite DB -> per-work stats
Select  strata rules fixed in code (below) -> sorted candidate keys -> seeded sampling
Pass 2  stream editions again -> keep editions of selected works (minus exclusions)
        -> optional works dump for work-level authors -> authors dump for names
Write   corpus.jsonl (sorted by edition_id) + manifest.json (inputs, digests, seed, quotas,
        stratum counts, drop reasons, exclusion verification, output digest)

Strata (all computed from pass-1 stats, BEFORE any filtering by outcome):
  S1 confusable  >= 8 editions with a valid ISBN and >= 2 known formats
  S2 translated  has English editions AND (another language OR translation_of/translated_from)
  S3 revised     some edition_name mentions revised/2nd+/anniversary/expanded/updated
  S4 companion   study-guide works whose stripped title equals a selected S1-S3 work title
  S5 box set     box-set works with >= 1 valid ISBN
  S6 same title  other works whose title equals a selected work's title (distractors)
  S7 random      English works with >= 1 valid ISBN (distractors)
  H  human seeds works whose title equals a title on the human seed list (all matches kept)
"""

from __future__ import annotations

import json
import random
import re
import sqlite3
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz, process

from bera import isbn as isbnlib
from bera.evalkit.splits import family_split
from bera.features import content_kind, parse_format
from bera.ingest.dumps import (
    DumpRow,
    ReadStats,
    Redirects,
    edition_author_keys,
    edition_work_key,
    file_digests,
    iter_dump,
    map_edition,
    parse_year,
)
from bera.ingest.quality import (
    GENERIC_AUTHOR_NAMES,
    AuditEdition,
    AuthorRecord,
    EdFeat,
    WorkInfo,
    author_ambiguity,
    build_families,
    cross_seed_families,
    primary_author_keys,
    probe_audit,
    sample_editions,
    suspicious_merges,
)
from bera.models import Edition, PhysicalFormat
from bera.text import fold_title, norm_person, norm_text, strip_accents

_REVISED_RE = re.compile(
    r"\b(revised|rev|expanded|updated|anniversary|(?:[2-9]|1\d)(?:nd|rd|th)|second|third|fourth)\b"
)
_GUIDE_PREFIX_RE = re.compile(
    r"^(study guide|sparknotes|cliffsnotes|cliffs notes|summary of|workbook for|"
    r"companion to|readers guide)( (for|to|on))?\s*"
)


@dataclass(frozen=True)
class Quotas:
    h_max_works_per_title: int = 3
    s1_confusable: int = 60
    s2_translated: int = 30
    s3_revised: int = 30
    s4_companion_max: int = 40
    s5_box_set: int = 15
    s6_same_title_max: int = 40
    s7_random: int = 60
    max_editions_per_work: int = 60


@dataclass
class BuildInputs:
    editions: Path
    authors: Path
    redirects: Path | None = None
    works: Path | None = None
    human_seeds: Path | None = None  # JSONL {"title": ..., "author": ...}
    exclusions: Path | None = None  # JSONL {"isbn"?: ..., "title"?: ..., "author"?: ...}


@dataclass
class Manifest:
    source_label: str
    seed: int
    quotas: dict[str, int]
    python_version: str
    inputs: dict[str, Any] = field(default_factory=dict)
    read_stats: dict[str, dict[str, Any]] = field(default_factory=dict)
    strata: dict[str, int] = field(default_factory=dict)
    selected_works: int = 0
    editions_written: int = 0
    dropped: dict[str, int] = field(default_factory=dict)
    exclusion_check: dict[str, Any] = field(default_factory=dict)
    human_seed_matches: dict[str, int] = field(default_factory=dict)
    output: dict[str, Any] = field(default_factory=dict)
    seed_alias_of_work: dict[str, str] = field(default_factory=dict)
    analysis: dict[str, Any] = field(default_factory=dict)


def _load_jsonl(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _edition_title(d: dict[str, Any]) -> str:
    raw_title, raw_prefix = d.get("title"), d.get("title_prefix")
    title: str = raw_title if isinstance(raw_title, str) else ""
    prefix: str = raw_prefix if isinstance(raw_prefix, str) else ""
    if prefix and not title.lower().startswith(prefix.lower()):
        title = f"{prefix} {title}"
    return title


# ---- exclusion rules -----------------------------------------------------------------------
TITLE_FUZZY_RATIO = 92.0
R4_PARTIAL_RATIO = 85.0


@dataclass
class Probe:
    title: str
    author: str
    author_keys: frozenset[str]
    ftitle: str
    surname: str


@dataclass
class ExclusionRules:
    """Out-of-corpus probes. A work or edition is excluded if ANY of these hold:

    R1  it is credited (edition author keys, after redirects) to any OL author key listed for
        a probe author; all duplicate/unmerged author records are listed, so translations,
        omnibus volumes and re-titled editions by that author are excluded too
    R2  its folded title (accents, leading articles, punctuation removed) equals a probe's
        folded title, contains it as a whole phrase, or has rapidfuzz ratio >= 92 to it
    R3  its folded `translation_of` matches a probe title under R2
    R4  it has no author keys, its by_statement mentions the probe author's surname, and its
        title matches under R2
    R5  it carries an ISBN listed for a probe
    Study guides about a probe are caught by R2's phrase containment.
    """

    probes: list[Probe]
    isbns: set[str]

    @classmethod
    def load(cls, rows: list[dict[str, Any]]) -> ExclusionRules:
        probes = []
        for r in rows:
            if r.get("title"):
                author = str(r.get("author") or "")
                probes.append(
                    Probe(
                        title=str(r["title"]),
                        author=author,
                        author_keys=frozenset(
                            f"/authors/{k}" if not str(k).startswith("/") else k
                            for k in r.get("author_keys", [])
                        ),
                        ftitle=fold_title(str(r["title"])),
                        surname=strip_accents(norm_text(author)).split()[-1] if author else "",
                    )
                )
        isbns = {
            p.isbn13
            for p in (isbnlib.parse(str(r["isbn"])) for r in rows if r.get("isbn"))
            if p.valid and p.isbn13
        }
        return cls(probes, isbns)

    @property
    def author_keys(self) -> frozenset[str]:
        return frozenset(k for p in self.probes for k in p.author_keys)

    def title_hit(self, ftitle: str) -> Probe | None:
        if not ftitle:
            return None
        padded = f" {ftitle} "
        for p in self.probes:
            if (
                ftitle == p.ftitle
                or f" {p.ftitle} " in padded
                or fuzz.ratio(ftitle, p.ftitle) >= TITLE_FUZZY_RATIO
            ):
                return p
        return None

    def edition_reason(
        self,
        *,
        author_keys: set[str],
        ftitle: str,
        ftrans: str,
        by_statement: str,
        isbn13s: set[str],
    ) -> str | None:
        if author_keys & self.author_keys:
            return "R1_author_key"
        if self.title_hit(ftitle):
            return "R2_title"
        if ftrans and self.title_hit(ftrans):
            return "R3_translation_of"
        if not author_keys and by_statement:
            low = strip_accents(by_statement.casefold())
            for p in self.probes:
                if (
                    p.surname
                    and p.surname in low
                    and ftitle
                    and fuzz.partial_ratio(p.ftitle, ftitle) >= R4_PARTIAL_RATIO
                ):
                    return "R4_by_statement"
        if isbn13s & self.isbns:
            return "R5_isbn"
        return None


# ---- pass 1 --------------------------------------------------------------------------------
def pass1_stats(
    editions: Path, redirects: Redirects, scratch: sqlite3.Connection, stats: ReadStats
) -> None:
    scratch.executescript("""
        PRAGMA journal_mode = OFF;
        PRAGMA synchronous = OFF;
        PRAGMA cache_size = -1000000;
        PRAGMA temp_store = FILE;
        DROP TABLE IF EXISTS ed;
        CREATE TABLE ed (work TEXT, has_isbn INT, fmt TEXT, eng INT, other_lang INT,
                         translated INT, revised INT, kind TEXT, ntitle TEXT, ftitle TEXT,
                         ftrans TEXT, authors TEXT, bystmt TEXT, isbns TEXT,
                         ekey TEXT, lang1 TEXT, pyear INT, pub TEXT, edname TEXT);
    """)
    batch: list[tuple[Any, ...]] = []
    for row in iter_dump(editions, stats):
        if row.type != "/type/edition":
            continue
        d = row.data
        work = edition_work_key(d, redirects)
        if work is None:
            continue
        raw_isbns = [
            x for x in [*d.get("isbn_10", []), *d.get("isbn_13", [])] if isinstance(x, str)
        ]
        valid13 = sorted({p.isbn13 for p in map(isbnlib.parse, raw_isbns) if p.valid and p.isbn13})
        fmt_raw = d.get("physical_format")
        fmt = parse_format(fmt_raw) if isinstance(fmt_raw, str) else PhysicalFormat.UNKNOWN
        langs = {
            lk.get("key", "").rsplit("/", 1)[-1]
            for lk in d.get("languages", [])
            if isinstance(lk, dict)
        }
        trans = d.get("translation_of") if isinstance(d.get("translation_of"), str) else ""
        translated = bool(trans or d.get("translated_from"))
        ed_name = d.get("edition_name") if isinstance(d.get("edition_name"), str) else ""
        raw_title = _edition_title(d)
        title = norm_text(raw_title)
        subtitle = d.get("subtitle") if isinstance(d.get("subtitle"), str) else ""
        lang_list = [
            lk.get("key", "").rsplit("/", 1)[-1]
            for lk in d.get("languages", [])
            if isinstance(lk, dict)
        ]
        pubs = [x for x in d.get("publishers", []) if isinstance(x, str) and x.strip()]
        pdate = d.get("publish_date") if isinstance(d.get("publish_date"), str) else None
        raw_by = d.get("by_statement")
        by: str = raw_by if isinstance(raw_by, str) else ""
        batch.append(
            (
                work,
                int(bool(valid13)),
                fmt.value,
                int("eng" in langs),
                int(bool(langs - {"eng"})),
                int(translated),
                int(bool(_REVISED_RE.search(norm_text(ed_name)))),
                content_kind(f"{title} {subtitle}"),
                title,
                fold_title(raw_title),
                fold_title(trans),
                " ".join(edition_author_keys(d, redirects)),
                by[:200],
                " ".join(valid13),
                row.key,
                lang_list[0] if lang_list else "",
                parse_year(pdate)[0],
                fold_title(pubs[0]) if pubs else "",
                norm_text(ed_name),
            )
        )
        if len(batch) >= 10_000:
            scratch.executemany(
                "INSERT INTO ed VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch
            )
            batch.clear()
    scratch.executemany("INSERT INTO ed VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
    scratch.executescript("""
        CREATE INDEX ed_work ON ed(work);
        DROP TABLE IF EXISTS titles;
        CREATE TABLE titles AS
            SELECT work, ntitle, ftitle, c,
                   ROW_NUMBER() OVER (PARTITION BY work ORDER BY c DESC, ntitle) rn
            FROM (SELECT work, ntitle, ftitle, COUNT(*) c FROM ed WHERE ntitle != ''
                  GROUP BY work, ntitle, ftitle);
        CREATE INDEX titles_work_rn ON titles(work, rn);
        DROP TABLE IF EXISTS agg;
        CREATE TABLE agg AS
            SELECT work, COUNT(*) n, SUM(has_isbn) n_isbn,
                   COUNT(DISTINCT CASE WHEN fmt NOT IN ('unknown','other') THEN fmt END) n_fmt,
                   MAX(eng) eng, MAX(other_lang) other_lang, MAX(translated) translated,
                   MAX(revised) revised, MAX(kind = 'study_guide') guide,
                   MAX(kind = 'box_set') boxset
            FROM ed GROUP BY work;
        DROP TABLE IF EXISTS works;
        CREATE TABLE works AS
            SELECT a.*, t.ntitle AS title, t.ftitle AS ftitle
            FROM agg a LEFT JOIN titles t ON t.work = a.work AND t.rn = 1;
        CREATE INDEX works_work ON works(work);
        CREATE INDEX works_title ON works(title);
        CREATE INDEX works_ftitle ON works(ftitle);
    """)


def bulk_title_hits(titles: list[str], rules: ExclusionRules) -> set[str]:
    """Distinct folded titles matching any probe under R2, computed in bulk: exact, whole
    phrase (one compiled regex), or rapidfuzz ratio >= TITLE_FUZZY_RATIO (vectorized cdist).
    Equivalent to ExclusionRules.title_hit, which is used per edition in pass 2."""
    if not rules.probes or not titles:
        return set()
    probe_titles = [p.ftitle for p in rules.probes if p.ftitle]
    phrase = re.compile(r"(?:^| )(?:" + "|".join(re.escape(x) for x in probe_titles) + r")(?: |$)")
    hits = {t for t in titles if phrase.search(t)}
    matrix = process.cdist(
        probe_titles,
        titles,
        scorer=fuzz.ratio,
        score_cutoff=TITLE_FUZZY_RATIO,
        dtype="uint8",
        workers=-1,
    )
    for j in set(matrix.nonzero()[1].tolist()):
        hits.add(titles[j])
    return hits


def excluded_works(scratch: sqlite3.Connection, rules: ExclusionRules) -> dict[str, str]:
    """work -> first rule that excludes it. Every edition of every work is checked (not just
    the dominant title), so a work cannot re-enter through a variant edition."""
    titles = sorted(
        {
            r[0]
            for r in scratch.execute(
                "SELECT DISTINCT ftitle FROM ed WHERE ftitle != '' "
                "UNION SELECT DISTINCT ftrans FROM ed WHERE ftrans != ''"
            )
        }
    )
    hit_titles = bulk_title_hits(titles, rules)
    keys = rules.author_keys
    surnames = [p.surname for p in rules.probes if p.surname]
    out: dict[str, str] = {}
    for work, authors, ftitle, ftrans, by, isbns in scratch.execute(
        "SELECT work, authors, ftitle, ftrans, bystmt, isbns FROM ed"
    ):
        if work in out:
            continue
        akeys = set(authors.split()) if authors else set()
        if keys and akeys & keys:
            out[work] = "R1_author_key"
        elif ftitle in hit_titles:
            out[work] = "R2_title"
        elif ftrans and ftrans in hit_titles:
            out[work] = "R3_translation_of"
        elif not akeys and by and any(s in strip_accents(by.casefold()) for s in surnames):
            reason = rules.edition_reason(
                author_keys=akeys,
                ftitle=ftitle or "",
                ftrans=ftrans or "",
                by_statement=by,
                isbn13s=set(),
            )
            if reason:
                out[work] = reason
        elif rules.isbns and isbns and set(isbns.split()) & rules.isbns:
            out[work] = "R5_isbn"
    return out


# ---- selection -----------------------------------------------------------------------------
def _sample(rng: random.Random, keys: Iterable[str], k: int, taken: set[str]) -> list[str]:
    pool = sorted(set(keys) - taken)
    picked = pool if len(pool) <= k else rng.sample(pool, k)
    picked = sorted(picked)
    taken.update(picked)
    return picked


@dataclass
class Seed:
    title: str
    ftitle: str
    author_keys: frozenset[str]
    alias_group: str | None = None


def load_seeds(rows: list[dict[str, Any]]) -> list[Seed]:
    return [
        Seed(
            str(r["title"]),
            fold_title(str(r["title"])),
            frozenset(
                f"/authors/{k}" if not str(k).startswith("/") else k
                for k in r.get("author_keys", [])
            ),
            r.get("alias_group"),
        )
        for r in rows
        if r.get("title")
    ]


def select_works(
    scratch: sqlite3.Connection,
    seed: int,
    q: Quotas,
    seeds: list[Seed],
    excluded: dict[str, str],
    manifest: Manifest,
) -> dict[str, str]:
    """Return work -> stratum. Every stratum (including S4 and S6) skips excluded works."""
    rng = random.Random(seed)  # noqa: S311 - reproducible sampling, not security

    def keys(sql: str, params: tuple[Any, ...] = ()) -> list[str]:
        return [r[0] for r in scratch.execute(sql, params) if r[0] not in excluded]

    def credited(work: str, akeys: frozenset[str]) -> bool:
        for (authors,) in scratch.execute("SELECT authors FROM ed WHERE work = ?", (work,)):
            if authors and set(authors.split()) & akeys:
                return True
        return False

    taken: set[str] = set()
    strata: dict[str, list[str]] = {"H": []}
    for s in seeds:
        matches = keys("SELECT work FROM works WHERE ftitle = ? ORDER BY n DESC, work", (s.ftitle,))
        if s.author_keys:  # author-constrained when keys are known
            matches = [w for w in matches if credited(w, s.author_keys)]
        manifest.human_seed_matches[s.title] = len(matches)
        chosen = [m for m in matches if m not in taken][: q.h_max_works_per_title]
        for m in chosen:
            manifest.seed_alias_of_work[m] = s.alias_group or s.ftitle
        strata["H"] += chosen
        taken.update(chosen)
    strata["S1"] = _sample(
        rng, keys("SELECT work FROM works WHERE n_isbn >= 8 AND n_fmt >= 2"), q.s1_confusable, taken
    )
    strata["S2"] = _sample(
        rng,
        keys("SELECT work FROM works WHERE eng = 1 AND (other_lang = 1 OR translated = 1)"),
        q.s2_translated,
        taken,
    )
    strata["S3"] = _sample(
        rng, keys("SELECT work FROM works WHERE revised = 1"), q.s3_revised, taken
    )
    core = strata["H"] + strata["S1"] + strata["S2"] + strata["S3"]
    core_titles = (
        {
            r[0]
            for r in scratch.execute(
                f"SELECT ftitle FROM works WHERE work IN ({','.join('?' * len(core))})",  # noqa: S608
                core,
            )
            if r[0]
        }
        if core
        else set()
    )
    guides = [
        w
        for w, t in scratch.execute("SELECT work, ftitle FROM works WHERE guide = 1 ORDER BY work")
        if w not in excluded and fold_title(_GUIDE_PREFIX_RE.sub("", t or "")) in core_titles
    ]
    strata["S4"] = _sample(rng, guides, q.s4_companion_max, taken)
    strata["S5"] = _sample(
        rng, keys("SELECT work FROM works WHERE boxset = 1 AND n_isbn >= 1"), q.s5_box_set, taken
    )
    same: list[str] = []
    for t in sorted(core_titles):
        same += keys("SELECT work FROM works WHERE ftitle = ?", (t,))
    strata["S6"] = _sample(rng, same, q.s6_same_title_max, taken)
    strata["S7"] = _sample(
        rng, keys("SELECT work FROM works WHERE eng = 1 AND n_isbn >= 1"), q.s7_random, taken
    )

    manifest.strata = {k: len(v) for k, v in strata.items()}
    return {w: k for k, ws in strata.items() for w in ws}


def write_preview(
    scratch: sqlite3.Connection,
    selected: dict[str, str],
    excluded: dict[str, str],
    sampled: dict[str, list[str]],
    manifest: Manifest,
    path: Path,
) -> dict[str, Any]:
    fam = manifest.analysis["families"]["family_of"]
    per_work = manifest.analysis["edition_sampling"]["per_work"]
    rows = []
    for work, stratum in sorted(selected.items(), key=lambda kv: (kv[1], kv[0])):
        r = scratch.execute(
            "SELECT title, n, n_isbn, n_fmt, eng, other_lang, translated, revised, guide, boxset "
            "FROM works WHERE work = ?",
            (work,),
        ).fetchone()
        wid = work.rsplit("/", 1)[-1]
        rows.append(
            {
                "stratum": stratum,
                "work": wid,
                "family": fam[wid],
                "title": r[0],
                "seed_alias": manifest.seed_alias_of_work.get(work),
                "editions_available": r[1],
                "editions_sampled": len(sampled[work]),
                "valid_isbn": r[2],
                "formats": r[3],
                "eng": r[4],
                "other_lang": r[5],
                "translated": r[6],
                "revised": r[7],
                "guide": r[8],
                "box_set": r[9],
                "distinct_available": per_work[wid]["distinct_available"],
                "distinct_kept": per_work[wid]["distinct_kept"],
                "missing_rate_kept": per_work[wid]["missing_rate_kept"],
            }
        )
    excl_rows = []
    for work, reason in sorted(excluded.items()):
        t = scratch.execute("SELECT title, n FROM works WHERE work = ?", (work,)).fetchone()
        excl_rows.append(
            {
                "work": work.rsplit("/", 1)[-1],
                "rule": reason,
                "title": t[0] if t else None,
                "editions": t[1] if t else None,
            }
        )
    preview = {
        "status": "PROVISIONAL selection preview: not a corpus, not approved",
        "selected_works": len(rows),
        "expected_editions": sum(len(v) for v in sampled.values()),
        "strata": manifest.strata,
        "selected": rows,
        "excluded_works": excl_rows,
        "analysis": manifest.analysis,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(preview, indent=1, ensure_ascii=False))
    return preview


def audit_corpus(editions: list[Edition], rules: ExclusionRules) -> list[dict[str, str]]:
    """Looser independent scan for anything resembling a probe (for manual review)."""
    hits = []
    for e in editions:
        texts = [e.title, e.subtitle or "", e.translation_of or ""]
        authors = {strip_accents(norm_person(a)) for a in e.authors}
        for p in rules.probes:
            pa = strip_accents(norm_person(p.author))
            title_like = any(
                fuzz.partial_ratio(p.ftitle, fold_title(t)) >= 90
                for t in texts
                if t and len(fold_title(t)) >= 4
            )
            if title_like or (pa and pa in authors):
                hits.append(
                    {
                        "edition_id": e.edition_id,
                        "title": e.title,
                        "authors": "; ".join(e.authors),
                        "probe": p.title,
                        "signal": "title" if title_like else "author_name",
                    }
                )
    return hits


# ---- selection analysis (shared by preview and build) -------------------------------------
def analyze_selection(
    scratch: sqlite3.Connection,
    selected: dict[str, str],
    excluded: dict[str, str],
    seeds: list[Seed],
    rules: ExclusionRules,
    authors_path: Path,
    q: Quotas,
    seed: int,
    manifest: Manifest,
    split_seed: int = 20261103,
    dev_fraction: float = 0.6,
) -> dict[str, list[str]]:
    """Fill manifest.analysis; return work -> sampled edition keys."""
    sampled: dict[str, list[str]] = {}
    sampling: dict[str, Any] = {}
    infos: list[WorkInfo] = []
    work_credits: dict[str, tuple[Counter[str], int]] = {}
    unmet_counter: Counter[str] = Counter()
    for work in sorted(selected):
        rows = scratch.execute(
            "SELECT ekey, fmt, lang1, pyear, pub, edname, ftitle, ftrans, authors "
            "FROM ed WHERE work = ? ORDER BY ekey",
            (work,),
        ).fetchall()
        feats = [
            EdFeat(
                r[0],
                None if r[1] in ("unknown", "other") else r[1],
                r[2] or None,
                r[3],
                r[4] or None,
                r[5] or None,
            )
            for r in rows
        ]
        keys, rep = sample_editions(feats, q.max_editions_per_work, seed)
        sampled[work] = keys
        unmet_counter.update(rep.unmet_dimensions)
        sampling[work.rsplit("/", 1)[-1]] = asdict(rep)
        guide_target = None
        if selected[work] == "S4":
            t = scratch.execute("SELECT ftitle FROM works WHERE work = ?", (work,)).fetchone()[0]
            guide_target = fold_title(_GUIDE_PREFIX_RE.sub("", t or ""))
        credits: Counter[str] = Counter()
        for r in rows:
            credits.update(set((r[8] or "").split()))
        work_credits[work] = (credits, len(rows))
        infos.append(
            WorkInfo(
                work=work,
                titles={r[6] for r in rows if r[6]},
                translation_of={r[7] for r in rows if r[7]},
                author_keys=set(),  # primary keys filled in below, once names are known
                guide_target=guide_target,
                alias_group=manifest.seed_alias_of_work.get(work),
            )
        )

    # author identity candidates (provisional): seed keys, probe keys, all credited keys
    wanted = (
        {k for s in seeds for k in s.author_keys}
        | set(rules.author_keys)
        | {k for c, _ in work_credits.values() for k in c}
    )
    records: dict[str, AuthorRecord] = {}
    for row in iter_dump(authors_path):
        if row.key in wanted:
            bd = row.data.get("birth_date")
            nm = row.data.get("name")
            records[row.key] = AuthorRecord(
                row.key.rsplit("/", 1)[-1],
                nm if isinstance(nm, str) else None,
                bd if isinstance(bd, str) else None,
            )

    # F1 links only through primary author keys; generic/unnamed records never link.
    def _generic(k: str) -> bool:
        name = (records[k].name or "") if k in records else ""
        return not name.strip() or name.strip().casefold() in GENERIC_AUTHOR_NAMES

    non_linking = {k for k in wanted if _generic(k)}
    secondary: Counter[str] = Counter()
    for wi in infos:
        credits, n = work_credits[wi.work]
        # Study guides link only to their target (F4): a guide's credited "author" is usually
        # a guide brand shared across unrelated titles, which would chain those titles.
        is_guide = wi.guide_target is not None
        wi.author_keys = set() if is_guide else primary_author_keys(credits, n, non_linking)
        secondary.update(k for k in credits if k not in wi.author_keys)
    fams = build_families(infos)
    sizes = fams.sizes()
    seed_group_of_work = {
        wi.work: wi.alias_group for wi in infos if selected[wi.work] == "H" and wi.alias_group
    }
    cross_seed = cross_seed_families(fams.family_of, seed_group_of_work)

    seed_amb: dict[str, dict[str, Any]] = {}
    for s in seeds:
        h_works = [
            w for w, a in manifest.seed_alias_of_work.items() if a == (s.alias_group or s.ftitle)
        ]
        credited: Counter[str] = Counter()
        for w in h_works:
            for (authors,) in scratch.execute("SELECT authors FROM ed WHERE work = ?", (w,)):
                for k in (authors or "").split():
                    if k in s.author_keys:
                        credited[k.rsplit("/", 1)[-1]] += 1
        recs = [records[k] for k in sorted(s.author_keys) if k in records]
        seed_amb[s.title] = author_ambiguity(recs, credited)
    probe_amb: dict[str, dict[str, Any]] = {}
    excl_by_key: Counter[str] = Counter()
    for w, why in excluded.items():
        if why == "R1_author_key":
            for (authors,) in scratch.execute("SELECT authors FROM ed WHERE work = ?", (w,)):
                for k in (authors or "").split():
                    if k in rules.author_keys:
                        excl_by_key[k.rsplit("/", 1)[-1]] += 1
    for p in rules.probes:
        recs = [records[k] for k in sorted(p.author_keys) if k in records]
        probe_amb[p.title] = author_ambiguity(recs, excl_by_key)

    # merges that may have joined unrelated works
    ambiguous_keys: set[str] = set()
    for group in (seeds, rules.probes):
        for item in group:
            amb = (seed_amb if group is seeds else probe_amb)[item.title]
            if {
                "multiple_records_same_name",
                "different_birth_years_likely_different_people",
            } & set(amb["flags"]):
                ambiguous_keys |= set(item.author_keys)
    title_fanout: Counter[str] = Counter(t for w in infos for t in w.titles)
    names_by_key = {f"/authors/{r.key}": r.name for r in records.values()}
    suspicious = suspicious_merges(fams, names_by_key, ambiguous_keys, title_fanout)

    # proposed dev/held-out balance (families hashed with the split seed)
    split_of = {f: family_split(f, split_seed, dev_fraction) for f in set(fams.family_of.values())}
    balance: dict[str, Any] = {"split_seed": split_seed, "dev_fraction": dev_fraction}
    for split in ("dev", "heldout"):
        ws = [wi for wi in infos if split_of[fams.family_of[wi.work]] == split]
        by_stratum: Counter[str] = Counter(selected[wi.work] for wi in ws)
        eds_by_stratum: Counter[str] = Counter()
        for wi in ws:
            eds_by_stratum[selected[wi.work]] += len(sampled[wi.work])
        balance[split] = {
            "families": sum(1 for v in split_of.values() if v == split),
            "works": len(ws),
            "editions": sum(len(sampled[wi.work]) for wi in ws),
            "works_by_group": dict(sorted(by_stratum.items())),
            "editions_by_group": dict(sorted(eds_by_stratum.items())),
        }
    probe_fams = {}
    for p in rules.probes:
        k = sorted(p.author_keys)
        pf = f"probe-author:{k[0].rsplit('/', 1)[-1]}" if k else f"probe:{p.title}"
        probe_fams[p.title] = {"family": pf, "split": family_split(pf, split_seed, dev_fraction)}
    balance["probes"] = probe_fams

    # provisional probe pre-audit against the editions of the selected works
    audit_eds = [
        AuditEdition(
            r[0], r[1] or "", "", r[2] or "", frozenset(), strip_accents((r[3] or "").casefold())
        )
        for w in sorted(selected)
        for r in scratch.execute("SELECT ekey, ftitle, ftrans, bystmt FROM ed WHERE work = ?", (w,))
    ]
    pre_audit = {
        p.title: probe_audit(p.ftitle, "", p.surname, len(p.author_keys), audit_eds)
        for p in rules.probes
    }

    quotas = {
        "S1": q.s1_confusable,
        "S2": q.s2_translated,
        "S3": q.s3_revised,
        "S4": q.s4_companion_max,
        "S5": q.s5_box_set,
        "S6": q.s6_same_title_max,
        "S7": q.s7_random,
    }
    warnings: list[str] = []
    for stratum, quota in quotas.items():
        got = manifest.strata.get(stratum, 0)
        if got < quota and stratum not in ("S4", "S6"):
            warnings.append(f"quota_unmet {stratum}: {got}/{quota} (candidate pool exhausted)")
    for s in seeds:
        n = sum(1 for a in manifest.seed_alias_of_work.values() if a == (s.alias_group or s.ftitle))
        if manifest.human_seed_matches.get(s.title, 0) == 0:
            warnings.append(f"seed_unmatched: {s.title}")
        elif n == 0:
            warnings.append(f"seed_matched_but_all_works_already_taken: {s.title}")
        flags = seed_amb[s.title]["flags"]
        if (
            "different_birth_years_likely_different_people" in flags
            or "several_candidate_records_credited_in_matched_works" in flags
        ):
            warnings.append(f"seed_author_ambiguous: {s.title} {flags}")
    for title, amb in probe_amb.items():
        if "different_birth_years_likely_different_people" in amb["flags"]:
            warnings.append(f"probe_author_keys_may_cover_other_people: {title}")
    for title, a in pre_audit.items():
        if a["status"] != "verified_absent":
            warnings.append(f"probe_preaudit_quarantine: {title} {a['reasons']}")
    largest = sizes.most_common(5)
    if suspicious:
        fams_hit = {fams.family_of[f"/works/{m['a']}"] for m in suspicious}
        warnings.append(
            f"possible_unrelated_merges: {len(suspicious)} merges across {len(fams_hit)} "
            "families via generic/ambiguous author records or generic titles (see families)"
        )
    for f, gs in cross_seed.items():
        warnings.append(f"cross_seed_family: {f} joins seed groups {gs} (review)")
    if largest and largest[0][1] > max(5, len(selected) // 10):
        warnings.append(f"large_family: {largest[0][0]} has {largest[0][1]} works")

    manifest.analysis = {
        "edition_sampling": {
            "method": "seeded greedy max-coverage over format/language/decade/publisher/"
            "edition_statement; SHA-256(seed:key) tie-break",
            "cap": q.max_editions_per_work,
            "works_with_unmet_diversity_by_dimension": dict(unmet_counter),
            "per_work": sampling,
        },
        "families": {
            "count": len(sizes),
            "edges": fams.edge_counts,
            "largest": [{"family": f, "works": n} for f, n in largest],
            "singleton_families": sum(1 for n in sizes.values() if n == 1),
            "suspicious_merges": suspicious,
            "author_link_rule": "F1 uses primary author keys only: credited on >= 20% of a "
            "work's editions or most-credited; generic/unnamed records never link; study "
            "guides link only via F4 to their target",
            "secondary_credit_keys_not_linking": [
                {
                    "key": k.rsplit("/", 1)[-1],
                    "name": records[k].name if k in records else None,
                    "works": n,
                }
                for k, n in secondary.most_common(25)
            ],
            "cross_seed_families": cross_seed,
            "cross_seed_family_merges": {
                f: [
                    {"rule": t, "value": v, "a": a.rsplit("/", 1)[-1], "b": b.rsplit("/", 1)[-1]}
                    for t, v, a, b in fams.merges
                    if fams.family_of[a] == f
                ]
                for f in cross_seed
            },
            "limitation": "family grouping reduces split leakage but cannot guarantee that "
            "every alias, duplicate work or translation is detected",
            "family_of": {w.rsplit("/", 1)[-1]: f for w, f in fams.family_of.items()},
        },
        "author_identity": {"seeds": seed_amb, "probes": probe_amb},
        "probe_preaudit_provisional": pre_audit,
        "split_balance": balance,
        "warnings": warnings,
    }
    return sampled


# ---- pass 2 + write ------------------------------------------------------------------------
def build_corpus(
    inputs: BuildInputs,
    out_dir: Path,
    *,
    seed: int,
    source_label: str,
    quotas: Quotas | None = None,
    scratch_path: Path | None = None,
    preview_only: bool = False,
    split_seed: int = 20261103,
    dev_fraction: float = 0.6,
    reuse_scratch: bool = False,
) -> Manifest:
    """`reuse_scratch` (preview only) skips pass 1 and re-runs selection and analysis on an
    existing scratch DB from a previous preview of the same dump. Full builds always rescan."""
    if reuse_scratch and not (preview_only and scratch_path and scratch_path.exists()):
        raise ValueError("reuse_scratch requires preview_only and an existing scratch DB")
    q = quotas or Quotas()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = Manifest(
        source_label=source_label,
        seed=seed,
        quotas=asdict(q),
        python_version=sys.version.split()[0],
    )
    for name in ("editions", "authors", "redirects", "works", "human_seeds", "exclusions"):
        path = getattr(inputs, name)
        if path is not None:
            manifest.inputs[name] = {"file": path.name, **file_digests(path)}

    redirects = Redirects.from_dump(inputs.redirects, ("/works/", "/authors/", "/books/"))
    seeds = load_seeds(_load_jsonl(inputs.human_seeds))
    rules = ExclusionRules.load(_load_jsonl(inputs.exclusions))

    scratch = sqlite3.connect(scratch_path or ":memory:")
    if reuse_scratch:
        manifest.read_stats["editions_pass1"] = {"reused_scratch": str(scratch_path)}
    else:
        s1 = ReadStats()
        pass1_stats(inputs.editions, redirects, scratch, s1)
        manifest.read_stats["editions_pass1"] = asdict(s1)
    excluded = excluded_works(scratch, rules)
    selected = select_works(scratch, seed, q, seeds, excluded, manifest)
    manifest.selected_works = len(selected)
    manifest.exclusion_check = {
        "excluded_works": len(excluded),
        "excluded_by_rule": dict(
            sorted(
                {
                    r: sum(1 for v in excluded.values() if v == r) for r in set(excluded.values())
                }.items()
            )
        ),
    }
    sampled = analyze_selection(
        scratch,
        selected,
        excluded,
        seeds,
        rules,
        inputs.authors,
        q,
        seed,
        manifest,
        split_seed,
        dev_fraction,
    )
    if preview_only:
        preview = write_preview(
            scratch, selected, excluded, sampled, manifest, out_dir / "selection_preview.json"
        )
        manifest.output = {
            "preview": "selection_preview.json",
            "expected_editions": preview["expected_editions"],
        }
        scratch.close()
        (out_dir / "manifest.json").write_text(
            json.dumps(asdict(manifest), indent=2, sort_keys=True)
        )
        return manifest
    scratch.close()

    sampled_keys = {k for ks in sampled.values() for k in ks}
    # pass 2: collect raw rows of the sampled editions of selected works
    kept: dict[str, list[DumpRow]] = {}
    dropped: dict[str, int] = {}
    s2 = ReadStats()
    for row in iter_dump(inputs.editions, s2):
        if row.type != "/type/edition":
            continue
        work = edition_work_key(row.data, redirects)
        if work is None or work not in selected:
            continue
        if row.key not in sampled_keys:
            dropped["not_sampled"] = dropped.get("not_sampled", 0) + 1
            continue
        kept.setdefault(work, []).append(row)
    manifest.read_stats["editions_pass2"] = asdict(s2)

    for rows in kept.values():
        rows.sort(key=lambda r: r.key)

    work_authors: dict[str, list[str]] = {}
    if inputs.works is not None:
        for row in iter_dump(inputs.works):
            if row.key in selected:
                ks = [
                    redirects.resolve(a["author"]["key"])
                    for a in row.data.get("authors", [])
                    if isinstance(a, dict)
                    and isinstance(a.get("author"), dict)
                    and isinstance(a["author"].get("key"), str)
                ]
                work_authors[row.key] = ks

    needed = {
        k for rows in kept.values() for r in rows for k in edition_author_keys(r.data, redirects)
    }
    needed |= {k for ks in work_authors.values() for k in ks}
    names: dict[str, str] = {}
    for row in iter_dump(inputs.authors):
        if row.key in needed:
            author_name = row.data.get("name") or row.data.get("personal_name")
            if isinstance(author_name, str) and author_name.strip():
                names[row.key] = author_name.strip()

    def reason_for(r: DumpRow, e: Edition) -> str | None:
        return rules.edition_reason(
            author_keys=set(edition_author_keys(r.data, redirects)),
            ftitle=fold_title(e.title),
            ftrans=fold_title(e.translation_of),
            by_statement=str(r.data.get("by_statement") or ""),
            isbn13s={
                p.isbn13
                for p in map(isbnlib.parse, (*e.isbn_10, *e.isbn_13))
                if p.valid and p.isbn13
            },
        )

    editions = []
    raw_by_id: dict[str, DumpRow] = {}
    for rows in kept.values():
        for r in rows:
            e = map_edition(
                r,
                redirects=redirects,
                author_names=names,
                work_author_keys=work_authors,
                source=source_label,
            )
            if e is None:
                dropped["no_title_no_isbn"] = dropped.get("no_title_no_isbn", 0) + 1
                continue
            reason = reason_for(r, e)
            if reason:
                dropped[f"excluded_{reason}"] = dropped.get(f"excluded_{reason}", 0) + 1
                continue
            editions.append(e)
            raw_by_id[e.edition_id] = r
    editions.sort(key=lambda e: e.edition_id)
    manifest.dropped = dict(sorted(dropped.items()))

    # Independent re-checks: strict rules must find nothing; the loose audit lists anything
    # that merely resembles a probe, for human review.
    violations = sorted(e.edition_id for e in editions if reason_for(raw_by_id[e.edition_id], e))
    manifest.exclusion_check["violations"] = violations
    manifest.exclusion_check["audit_hits_for_review"] = audit_corpus(editions, rules)

    final_eds = [
        AuditEdition(
            e.edition_id,
            fold_title(e.title),
            fold_title(e.subtitle),
            fold_title(e.translation_of),
            frozenset(strip_accents(norm_person(a)) for a in e.authors),
            strip_accents(str(raw_by_id[e.edition_id].data.get("by_statement") or "").casefold()),
        )
        for e in editions
    ]
    probe_status = {
        p.title: probe_audit(
            p.ftitle, strip_accents(norm_person(p.author)), p.surname, len(p.author_keys), final_eds
        )
        for p in rules.probes
    }
    manifest.exclusion_check["probe_status"] = {k: v["status"] for k, v in probe_status.items()}
    (out_dir / "probe_audit.json").write_text(
        json.dumps(probe_status, indent=1, ensure_ascii=False)
    )
    (out_dir / "families.json").write_text(
        json.dumps(manifest.analysis["families"]["family_of"], indent=0, sort_keys=True)
    )

    corpus = out_dir / "corpus.jsonl"
    with corpus.open("w", encoding="utf-8") as fh:
        for e in editions:
            fh.write(e.model_dump_json() + "\n")
    manifest.editions_written = len(editions)
    manifest.output = {"file": corpus.name, **file_digests(corpus)}
    (out_dir / "manifest.json").write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True))
    return manifest


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - thin CLI
    import argparse

    p = argparse.ArgumentParser(prog="bera-build-corpus")
    for name in ("editions", "authors"):
        p.add_argument(f"--{name}", type=Path, required=True)
    for name in ("redirects", "works", "human-seeds", "exclusions"):
        p.add_argument(f"--{name}", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--source-label", required=True)
    p.add_argument("--scratch", type=Path, help="on-disk scratch DB for large dumps")
    p.add_argument("--config", type=Path, help="selection_config_vN.json (quotas)")
    p.add_argument(
        "--preview-only",
        action="store_true",
        help="stop after selection; write selection_preview.json, no corpus",
    )
    p.add_argument(
        "--reuse-scratch",
        action="store_true",
        help="preview only: skip pass 1 and re-analyze the existing --scratch DB",
    )
    a = p.parse_args(argv)
    cfg = json.loads(a.config.read_text()) if a.config else {}
    quotas = Quotas(**cfg["quotas"]) if cfg else None
    m = build_corpus(
        BuildInputs(a.editions, a.authors, a.redirects, a.works, a.human_seeds, a.exclusions),
        a.out,
        seed=a.seed,
        source_label=a.source_label,
        quotas=quotas,
        scratch_path=a.scratch,
        preview_only=a.preview_only,
        split_seed=int(cfg.get("split_seed", 20261103)),
        dev_fraction=float(cfg.get("dev_fraction", 0.6)),
        reuse_scratch=a.reuse_scratch,
    )
    print(
        json.dumps(
            {
                "editions": m.editions_written,
                "strata": m.strata,
                "exclusion_check": {
                    k: v for k, v in m.exclusion_check.items() if k != "audit_hits_for_review"
                },
            }
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
