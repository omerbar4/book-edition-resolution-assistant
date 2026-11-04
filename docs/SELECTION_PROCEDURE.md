# Corpus selection, v3 (PROPOSED: not approved for building)

> **v3 update (2026-11-03).** The owner accepted the 42 titles and the probe categories. v3
> keeps them unchanged (author keys identical to v2) and adds:
> - seed alias groups;
> - conservative work families for splitting;
> - diversity-preserving edition sampling instead of "first 60 by key";
> - author-identity ambiguity flags;
> - a per-probe absence audit with quarantine.
>
> v1 and v2 were superseded without being built.
>
> | v3 file | sha256 |
> |---|---|
> | `data/selection/seed_list_v3_proposed.jsonl` | `d1f4a1b3abc3d745aa8878fe346128340f02004f7903b5e0c9169cc1979a9e97` |
> | `data/selection/exclusions_v3_proposed.jsonl` | `c8c572efef31429248efe45dffdad7314d53dd5adcb43f0bd3fdfb70b4694664` |
> | `data/selection/selection_config_v3_proposed.json` | `8f1097f1557780d2d46f30ffa82572188047e1eb15122f1984142608121d0aaf` |

**Status.** v1 was frozen by checksum but **never built**. An audit before building found leak paths in its exclusion rules (see below), so v1 is superseded. v2 is a **proposal**: its checksums freeze the text for review; they are **not** the owner's approval. `scripts/build_corpus.sh build` refuses to run until the owner writes `data/selection/APPROVED_<version>.txt`. A `preview` (pass 1 plus selection only, no corpus) may run for review; it is provisional and is never used for labels, tuning or evaluation.

| file | sha256 |
|---|---|
| `data/selection/seed_list_v2_proposed.jsonl` | `b1d99cab9555798f81a244ee311ea20d6266e3b1f0f0547e8a1620b10a89ec3a` |
| `data/selection/exclusions_v2_proposed.jsonl` | `736d3b90e510365383a6ed8774467e276adf2170b76a54bbf81fc11330c7a7dd` |
| `data/selection/selection_config_v2_proposed.json` | `10d125e8868ce1bf533381cfeb1dc39a5d619599bbe8d4a55cb62ed8d670e94c` |

Author keys come from the verified `ol_dump_authors_2026-10-31`: an exact normalized-name match on `name`, `personal_name` or `alternate_names`. **All** duplicate/unmerged author records are listed. Work identifiers come from the selection preview once the editions dump is verified; they are not guessed.

## 1. Seed titles (42)

| # | title | author | OL author keys | ambiguity tested |
|---|---|---|---|---|
| 1 | Pride and Prejudice | Jane Austen | OL16323475A, OL21594A (2) | classic; many editions, study guides, translations |
| 2 | Frankenstein | Mary Wollstonecraft Shelley | OL16593637A, OL25342A (2) | 1818 vs 1831 texts; many editions |
| 3 | Moby Dick | Herman Melville | OL16226145A, OL29497A (2) | many editions; title punctuation variants (Moby-Dick) |
| 4 | The Great Gatsby | F. Scott Fitzgerald | OL10146496A, OL12522279A, OL12794842A, OL15805471A, +3 more (7) | many formats; study guides |
| 5 | Nineteen Eighty-Four | George Orwell | OL118077A, OL15318546A, OL16029200A, OL16230010A, +1 more (5) | title variant '1984'; translations |
| 6 | 1984 | George Orwell | OL118077A, OL15318546A, OL16029200A, OL16230010A, +1 more (5) | numeric title variant of the above |
| 7 | To Kill a Mockingbird | Harper Lee | OL16022658A, OL498120A (2) | anniversary editions; study guides |
| 8 | The Hobbit | J. R. R. Tolkien | OL26320A (1) | illustrated/anniversary editions; translations |
| 9 | The Lord of the Rings | J. R. R. Tolkien | OL26320A (1) | single volume vs boxed set vs trilogy |
| 10 | The Fellowship of the Ring | J. R. R. Tolkien | OL26320A (1) | volume vs box set confusion |
| 11 | Harry Potter and the Philosopher's Stone | J. K. Rowling | OL16034707A, OL16230142A, OL16278610A, OL23919A (4) | UK title; illustrated editions |
| 12 | Harry Potter and the Sorcerer's Stone | J. K. Rowling | OL16034707A, OL16230142A, OL16278610A, OL23919A (4) | US title of the same book |
| 13 | The Little Prince | Antoine de Saint-Exupéry | OL16640711A, OL31901A (2) | translation of Le Petit Prince |
| 14 | Le Petit Prince | Antoine de Saint-Exupéry | OL16640711A, OL31901A (2) | original-language editions |
| 15 | One Hundred Years of Solitude | Gabriel García Márquez | OL15193084A, OL15290656A, OL15313724A, OL15389184A, +3 more (7) | translation; accented author |
| 16 | Cien años de soledad | Gabriel García Márquez | OL15193084A, OL15290656A, OL15313724A, OL15389184A, +3 more (7) | original-language editions |
| 17 | Don Quixote | Miguel de Cervantes Saavedra | OL15251925A, OL15302303A, OL15368764A, OL66452A (4) | many translators; abridged editions |
| 18 | War and Peace | Leo Tolstoy | OL15473846A, OL15536831A, OL15544955A, OL15844041A, +3 more (7) | transliteration variants (Lev Tolstoy) |
| 19 | Crime and Punishment | Fyodor Dostoyevsky | OL22242A (1) | spelling variants (Dostoevsky) |
| 20 | The Odyssey | Homer | OL10969187A, OL11412070A, OL11485315A, OL11570777A, +20 more (24) | many translators |
| 21 | Hamlet | William Shakespeare | OL12805924A, OL13002304A, OL16225388A, OL16278494A, +4 more (8) | study-guide heavy; series editions |
| 22 | Romeo and Juliet | William Shakespeare | OL12805924A, OL13002304A, OL16225388A, OL16278494A, +4 more (8) | study-guide heavy |
| 23 | The Catcher in the Rye | J. D. Salinger | OL13116434A, OL15414373A, OL15805450A, OL540486A (4) | many printings |
| 24 | Of Mice and Men | John Steinbeck | OL11543500A, OL14183913A, OL16229076A, OL2140114A, +1 more (5) | study guides |
| 25 | Dune | Frank Herbert | OL14885246A, OL79034A (2) | anniversary and deluxe editions |
| 26 | The Hunger Games | Suzanne Collins | OL12737091A, OL1394359A, OL5750621A (3) | trilogy box sets |
| 27 | A Game of Thrones | George R. R. Martin | OL16025431A, OL234664A, OL2748500A (3) | box sets; TV tie-in editions |
| 28 | The Chronicles of Narnia | C. S. Lewis | OL11467724A, OL11526173A, OL11544084A, OL12259816A, +15 more (19) | omnibus vs box set vs single volumes |
| 29 | Introduction to Algorithms | Thomas H. Cormen | OL1004780A (1) | numbered editions (textbook) |
| 30 | The C Programming Language | Brian W. Kernighan | OL946967A (1) | 1st vs 2nd edition |
| 31 | Structure and Interpretation of Computer Programs | Harold Abelson | OL14042988A, OL532838A (2) | 1st vs 2nd edition |
| 32 | The Elements of Style | William Strunk | OL2625113A (1) | many editions; illustrated edition |
| 33 | Little Women | Louisa May Alcott | OL153463A, OL16226129A, OL16226203A, OL26680A (4) | many editions; abridged |
| 34 | Jane Eyre | Charlotte Brontë | OL11275577A, OL113362A, OL16226019A, OL16461381A, +1 more (5) | many editions; similar author (Emily Brontë) |
| 35 | Wuthering Heights | Emily Brontë | OL15049488A, OL15058285A, OL15108810A, OL15294047A, +3 more (7) | many editions; similar author (Charlotte Brontë) |
| 36 | Alice's Adventures in Wonderland | Lewis Carroll | OL16224834A, OL16225014A, OL16228583A, OL16601139A, +1 more (5) | illustrated editions; omnibus with sequel |
| 37 | The Picture of Dorian Gray | Oscar Wilde | OL15611593A, OL16276738A, OL20646A (3) | 1890 vs 1891 versions |
| 38 | Dracula | Bram Stoker | OL10316489A, OL10485780A, OL11510274A, OL11977244A, +6 more (10) | many editions; annotated editions |
| 39 | Les Misérables | Victor Hugo | OL107571A, OL11431801A, OL12694371A, OL12694372A, +2 more (6) | abridged/unabridged; translations; accented title |
| 40 | The Count of Monte Cristo | Alexandre Dumas | OL15727719A, OL15841016A, OL15842507A, OL15862044A, +5 more (9) | abridged/unabridged |
| 41 | Beloved | Toni Morrison | OL31120A (1) | short title shared by unrelated books |
| 42 | The Road | Cormac McCarthy | OL16491925A, OL28104A (2) | short title shared by unrelated books |

## 2. Out-of-corpus probes (10)

| # | title | author | OL author keys excluded |
|---|---|---|---|
| 1 | The Remains of the Day | Kazuo Ishiguro | OL16606566A, OL28493A |
| 2 | Never Let Me Go | Kazuo Ishiguro | OL16606566A, OL28493A |
| 3 | The Name of the Wind | Patrick Rothfuss | OL2830895A |
| 4 | Station Eleven | Emily St. John Mandel | OL6538530A |
| 5 | The Left Hand of Darkness | Ursula K. Le Guin | OL16568974A, OL31353A |
| 6 | A Wizard of Earthsea | Ursula K. Le Guin | OL16568974A, OL31353A |
| 7 | Gödel, Escher, Bach | Douglas R. Hofstadter | OL12634513A, OL12648693A, OL12648696A, OL57437A |
| 8 | Middlemarch | George Eliot | OL10045454A, OL15289655A, OL15301886A, OL16225493A, OL16225686A, OL16618273A, OL24528A, OL5099520A |
| 9 | The Pragmatic Programmer | Andrew Hunt | OL1391034A, OL2670651A, OL497272A, OL5164719A, OL9986033A |
| 10 | Their Eyes Were Watching God | Zora Neale Hurston | OL226273A |

### Exclusion rules (R1–R5, `bera.ingest.corpus.ExclusionRules`)

A **work** is excluded from every stratum if **any** of its editions triggers a rule. An
**edition** is dropped again in pass 2 if it triggers one.

- **R1 author key:** credited, after redirects, to any listed probe author key. This removes
  translations, omnibus volumes and retitled editions by the probe author, and also any work
  by a *different* person with the same name (e.g. the 5 "Andrew Hunt" records). That
  over-exclusion is accepted.
- **R2 title:** the folded title (NFKC, casefold, accents stripped, punctuation removed,
  leading articles removed) equals the probe's, contains it as a whole phrase (catches
  subtitled editions and study guides), or has rapidfuzz ratio ≥ 92 (minor spelling
  variants).
- **R3 translation_of:** `translation_of` matches a probe title under R2.
- **R4 by_statement:** the edition has no author keys, its `by_statement` mentions the probe
  author's surname, and its title matches under R2.
- **R5 ISBN:** the edition carries an ISBN listed for a probe (none are listed in v2).

### How a probe is kept from reappearing

| path | v1 (superseded) | v2 |
|---|---|---|
| Accent/spelling variant ("Godel, Escher, Bach") | **leaked** (no accent folding) | R2 folding + ratio ≥ 92 |
| Missing leading article ("Remains of the Day") | **leaked** | R2 strips leading articles |
| Subtitled title ("Gödel, Escher, Bach: an Eternal Golden Braid") | **leaked** | R2 phrase containment |
| Translation under another title ("Nunca me abandones") | **leaked** unless it shared the excluded work | R1 author key; R3 `translation_of` |
| Omnibus/box set by the probe author | **leaked** | R1 |
| Study guide about the probe | **leaked** (S4/S7) | R2 phrase containment |
| Edition with no author keys | **leaked** (title+author both required) | R2 title alone, R4 by_statement |
| Variant edition inside an otherwise-allowed work | only the dominant title was checked | every edition of every work is scanned |
| Random sampling (S7) and S4/S6 | S4 and S6 **bypassed** the filter | one excluded-works set applies to all strata |
| Other edition of the same work | excluded only if dominant title matched | any edition triggering R1–R5 excludes the whole work |

After the build, the strict rules are re-run on the output and must find **zero**
violations. A looser audit (partial-ratio ≥ 90 on title/subtitle/`translation_of`, or the
probe author's name on the edition) lists every resemblance in the manifest for **human
review**.

**Remaining known gaps** (not fully closable from dump data):
- a translation by a translator-credited record whose title shares no phrase with the
  original and which lacks the original author's key and `translation_of`;
- probes whose author records are absent from the authors dump.

These are listed honestly rather than claimed solved.

Tests: `tests/unit/test_exclusion_leaks.py` (accent variant, retitled translation, omnibus
through a redirected author key, study guide, `translation_of`, author-less record, random
sampling, author-constrained seeds).

## 3. Caps, sampling rules, expected size

Seed `20261103`. Candidates in each stratum are sorted by work key, then sampled with
CPython's `random.Random(seed).sample`. The Python version is recorded in the manifest.

| stratum | rule | cap |
|---|---|---|
| H seeds | works whose folded dominant title equals the seed title **and** that have ≥ 1 edition credited to a listed seed author key; largest first | 3 works per title |
| S1 confusable | ≥ 8 editions with a valid ISBN and ≥ 2 known formats | 60 |
| S2 translated | has English editions and another language or translation markers | 30 |
| S3 revised | an `edition_name` mentions revised / 2nd+ / anniversary / expanded / updated | 30 |
| S4 companions | study-guide works whose stripped folded title equals a selected H/S1–S3 title | ≤ 40 |
| S5 box sets | box-set markers and ≥ 1 valid ISBN | 15 |
| S6 same title | other works with a folded title equal to a selected core title | ≤ 40 |
| S7 random | English, ≥ 1 valid ISBN | 60 |
| per work | first 60 editions by edition key | 60 |

**Expected size.** At most 126 + 60 + 30 + 30 + 40 + 15 + 40 + 60 = **401 works**, so at most
401 × 60 = **24,060 editions**. This is an upper bound. Many sampled works have only a few
editions, so the real count should be well below it, but it is **unknown until the
preview runs**; the preview reports the exact number.

## 4. v3 additions

### Work families (split unit; `bera.ingest.quality.build_families`)

Open Library may hold the same book under several work ids. For split assignment, selected
works are merged into one family if **any** of the following holds:

| rule | condition |
|---|---|
| F1 | they share a (provisional) author key |
| F2 | they share any folded edition title |
| F3 | one's `translation_of` matches the other's title |
| F4 | one is a study guide whose target title matches the other |
| F5 | they belong to the same seed alias group |

Seed alias groups:

| group | titles |
|---|---|
| `orwell-1984` | *1984* / *Nineteen Eighty-Four* |
| `rowling-hp1` | *Philosopher's Stone* / *Sorcerer's Stone* |
| `saint-exupery-petit-prince` | *The Little Prince* / *Le Petit Prince* |
| `garcia-marquez-solitude` | *One Hundred Years of Solitude* / *Cien años de soledad* |
| `tolkien-lotr` | *The Lord of the Rings* / *The Fellowship of the Ring* |

**Limitation (explicit):** family grouping *reduces* split leakage but **cannot guarantee**
that every alias, duplicate work or translation is detected. Works linked only by facts absent
from the dump stay in separate families. Examples: an unmerged duplicate work with a different
title and a different, unmerged author record; a retitled translation with no
`translation_of`. Residual leakage of this kind is possible and will be disclosed with any
held-out result.

The opposite error is also reported. The preview lists **possibly unrelated merges**: unions
made through generic or unnamed author records ("Anonymous", "Unknown", "Various"), through
author records flagged ambiguous, or through generic or high-fan-out titles ("Collected
Poems"). These merges are kept (conservative) but shown for review.

Over-merging is deliberate: F1 puts every selected work by one author record into one family.
That reduces the number of independent families but can never let an alias cross dev and
held-out. Probes by the same author share a family (`probe-author:<key>`). Splits hash the
**family**, never the work id. The preview reports the family count and the largest families.

### Edition sampling (`sample_editions`)

- A work with ≤ 60 editions keeps all of them.
- Larger works use a deterministic greedy max-coverage sample over five dimensions: format,
  primary language, publication decade, first publisher, and edition statement. Missing values
  add no coverage. Ties go to SHA-256(`seed:edition_key`).
- The per-work report lists distinct values available vs kept, the missing-metadata rate among
  kept editions, and **unmet dimensions**: where the cap could not keep every distinct value.
  These are reported, not hidden.

### Author identity

Exact-name matches are **provisional identity candidates**, not verified identities. For every
seed and probe, the preview lists each candidate record (key, name, birth date, editions
credited within scope) and raises flags:
- several same-name records;
- differing birth years (likely different people);
- several candidates credited in the matched works;
- no birth year on any record.

### Out-of-corpus claims

Exclusion rules reduce leakage; they **cannot prove absence** when metadata is incomplete.
After the final corpus is frozen, every probe is audited against it
(`probe_audit.json`). A probe is `verified_absent` only if:
- its author resolved to at least one record, and
- no edition resembles it by title, subtitle or `translation_of` (partial ratio ≥ 85), by
  author name, or by `by_statement` surname.

Otherwise it is **`quarantined`**: it gets no abstention draft or label until a human resolves
it. The drafter refuses unaudited and quarantined probes.

**Limitation.** Removing whole authors (R1) makes this out-of-corpus subset **narrower than
general open-set evaluation**. Every probe is an unseen author, so it does not measure, for
example, an unseen edition of a known work or an unseen book by a known author. Results on
this subset will be reported with that caveat.

All of these decisions depend only on dump metadata, never on retrieval or model performance.
