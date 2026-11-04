# Selection preview (PROVISIONAL: not a corpus, not approved)

- Selected works: **387**
- Editions after diversity sampling: **5366**
- Excluded works: **2484**
- Families: **214** (edges by rule: {'F1_author_key': 98, 'F2_title': 56, 'F4_guide': 19})

## Counts by sampling group

| group | works | editions sampled |
|---|---|---|
| H | 112 | 3653 |
| S1 | 60 | 1203 |
| S2 | 30 | 161 |
| S3 | 30 | 99 |
| S4 | 40 | 75 |
| S5 | 15 | 16 |
| S6 | 40 | 64 |
| S7 | 60 | 95 |

## Warnings

- seed_author_ambiguous: Nineteen Eighty-Four ['multiple_records_same_name', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: 1984 ['multiple_records_same_name', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: One Hundred Years of Solitude ['multiple_records_same_name', 'different_birth_years_likely_different_people', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: Cien años de soledad ['multiple_records_same_name', 'different_birth_years_likely_different_people', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: War and Peace ['multiple_records_same_name', 'different_birth_years_likely_different_people']
- seed_author_ambiguous: The Odyssey ['multiple_records_same_name', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: Hamlet ['multiple_records_same_name', 'different_birth_years_likely_different_people', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: Romeo and Juliet ['multiple_records_same_name', 'different_birth_years_likely_different_people', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: The Catcher in the Rye ['multiple_records_same_name', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: Of Mice and Men ['multiple_records_same_name', 'different_birth_years_likely_different_people']
- seed_author_ambiguous: Dune ['multiple_records_same_name', 'different_birth_years_likely_different_people']
- seed_author_ambiguous: The Hunger Games ['multiple_records_same_name', 'different_birth_years_likely_different_people', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: Structure and Interpretation of Computer Programs ['multiple_records_same_name', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: Little Women ['multiple_records_same_name', 'different_birth_years_likely_different_people']
- seed_author_ambiguous: Wuthering Heights ['multiple_records_same_name', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: Dracula ['multiple_records_same_name', 'several_candidate_records_credited_in_matched_works']
- seed_author_ambiguous: The Count of Monte Cristo ['multiple_records_same_name', 'different_birth_years_likely_different_people', 'several_candidate_records_credited_in_matched_works']
- probe_author_keys_may_cover_other_people: The Pragmatic Programmer
- probe_preaudit_quarantine: Station Eleven ['2_resembling_editions']
- probe_preaudit_quarantine: The Left Hand of Darkness ['2_resembling_editions']
- probe_preaudit_quarantine: A Wizard of Earthsea ['2_resembling_editions']
- probe_preaudit_quarantine: The Pragmatic Programmer ['14_resembling_editions']
- possible_unrelated_merges: 95 merges across 20 families via generic/ambiguous author records or generic titles (see families)
- cross_seed_family: fam:OL102749W joins seed groups ['count of monte cristo', 'crime and punishment', 'dune', 'great gatsby', 'hobbit', 'moby dick', 'orwell-1984', 'picture of dorian gray', 'rowling-hp1', 'tolkien-lotr', 'wuthering heights'] (review)
- cross_seed_family: fam:OL15165350W joins seed groups ['hamlet', 'pride and prejudice', 'romeo and juliet'] (review)
- large_family: fam:OL102749W has 61 works

## Families (split unit)

- Independent families: **214** (singletons: 175)
- Merge edges by rule: {'F1_author_key': 98, 'F2_title': 56, 'F4_guide': 19}
- Limitation: family grouping reduces split leakage but cannot guarantee that every alias, duplicate work or translation is detected.

| largest family | works |
|---|---|
| fam:OL102749W | 61 |
| fam:OL15165350W | 21 |
| fam:OL20463684W | 8 |
| fam:OL10263W | 7 |
| fam:OL17930368W | 7 |

Author-link rule: F1 uses primary author keys only: credited on >= 20% of a work's editions or most-credited; generic/unnamed records never link.

### Families joining several seed titles (2)

- fam:OL102749W: count of monte cristo, crime and punishment, dune, great gatsby, hobbit, moby dick, orwell-1984, picture of dorian gray, rowling-hp1, tolkien-lotr, wuthering heights
- fam:OL15165350W: hamlet, pride and prejudice, romeo and juliet

### Most frequent secondary credits (not used for linking)

| key | name | works credited |
|---|---|---|
| OL8339403A | Natalie Montoto | 16 |
| OL8370471A | Mint Editions | 16 |
| OL8340621A | Maxim Montoto | 15 |
| OL8336888A | Raul Bracho | 13 |
| OL3488782A | Richard S. Hartmetz | 12 |
| OL2965820A | [author not identified] | 12 |
| OL2727144A | ICON Reference | 11 |
| OL8344990A | Paul Boer | 11 |
| OL8344991A | Excercere Cerebrum Publications | 11 |
| OL8349355A | Andronum (cover illustrator) | 11 |
| OL7679323A | Atlantic Editions | 11 |
| OL8262446A | Andrea Gouveia | 11 |
| OL8345577A | Sheba Blake | 11 |
| OL7976461A | Alex Struik | 10 |
| OL8337000A | The Perfect The Perfect Library | 10 |

### Possibly unrelated merges (95)

| rule | linking value | work a | work b | reason |
|---|---|---|---|---|
| F1_author_key | /authors/OL10316489A | OL14930024W | OL85875W | ambiguous_author_record |
| F1_author_key | /authors/OL10316489A | OL14930024W | OL85892W | ambiguous_author_record |
| F1_author_key | /authors/OL107571A | OL1063588W | OL34414763W | ambiguous_author_record |
| F1_author_key | /authors/OL107571A | OL1063588W | OL40516131W | ambiguous_author_record |
| F1_author_key | /authors/OL107571A | OL1063588W | OL40542345W | ambiguous_author_record |
| F1_author_key | /authors/OL113362A | OL1095427W | OL32417366W | ambiguous_author_record |
| F1_author_key | /authors/OL113362A | OL1095427W | OL37840844W | ambiguous_author_record |
| F1_author_key | /authors/OL118077A | OL1168083W | OL23745689W | ambiguous_author_record |
| F1_author_key | /authors/OL118077A | OL1168083W | OL5093999W | ambiguous_author_record |
| F1_author_key | /authors/OL118077A | OL1168083W | OL6934191W | ambiguous_author_record |
| F1_author_key | /authors/OL1394359A | OL19952185W | OL5735363W | ambiguous_author_record |
| F1_author_key | /authors/OL15290656A | OL43080931W | OL43108828W | ambiguous_author_record |
| F1_author_key | /authors/OL18236A | OL20201553W | OL35362573W | ambiguous_author_record |
| F1_author_key | /authors/OL18236A | OL20201553W | OL36287W | ambiguous_author_record |
| F1_author_key | /authors/OL18404A | OL26446888W | OL26784440W | ambiguous_author_record |
| F1_author_key | /authors/OL18404A | OL26446888W | OL61982W | ambiguous_author_record |
| F1_author_key | /authors/OL20646A | OL24596091W | OL25965892W | ambiguous_author_record |
| F1_author_key | /authors/OL20646A | OL24596091W | OL43892241W | ambiguous_author_record |
| F1_author_key | /authors/OL20646A | OL24596091W | OL8193416W | ambiguous_author_record |
| F1_author_key | /authors/OL21594A | OL15165350W | OL17737918W | ambiguous_author_record |
| F1_author_key | /authors/OL21594A | OL15165350W | OL27337290W | ambiguous_author_record |
| F1_author_key | /authors/OL21594A | OL15165350W | OL66554W | ambiguous_author_record |
| F1_author_key | /authors/OL22098A | OL138052W | OL28897559W | ambiguous_author_record |
| F1_author_key | /authors/OL22098A | OL138052W | OL31040865W | ambiguous_author_record |
| F1_author_key | /authors/OL234664A | OL16261015W | OL17412540W | ambiguous_author_record |
| F1_author_key | /authors/OL234664A | OL16261015W | OL17512507W | ambiguous_author_record |
| F1_author_key | /authors/OL234664A | OL16261015W | OL257943W | ambiguous_author_record |
| F1_author_key | /authors/OL23919A | OL15267600W | OL17937389W | ambiguous_author_record |
| F1_author_key | /authors/OL23919A | OL15267600W | OL20662064W | ambiguous_author_record |
| F1_author_key | /authors/OL23919A | OL15267600W | OL82563W | ambiguous_author_record |
| F1_author_key | /authors/OL24529A | OL21170W | OL21177W | ambiguous_author_record |
| F1_author_key | /authors/OL25342A | OL17504079W | OL25595002W | ambiguous_author_record |
| F1_author_key | /authors/OL25342A | OL17504079W | OL36141872W | ambiguous_author_record |
| F1_author_key | /authors/OL25342A | OL17504079W | OL450063W | ambiguous_author_record |
| F1_author_key | /authors/OL25788A | OL14942752W | OL17829994W | ambiguous_author_record |
| F1_author_key | /authors/OL25788A | OL14942752W | OL23204W | ambiguous_author_record |
| F1_author_key | /authors/OL26680A | OL29983W | OL36900288W | ambiguous_author_record |
| F1_author_key | /authors/OL26680A | OL29983W | OL39134546W | ambiguous_author_record |
| F1_author_key | /authors/OL26783A | OL267171W | OL40255790W | ambiguous_author_record |
| F1_author_key | /authors/OL27349A | OL31701067W | OL34381078W | ambiguous_author_record |
| F1_author_key | /authors/OL27349A | OL31701067W | OL37629951W | ambiguous_author_record |
| F1_author_key | /authors/OL27349A | OL31701067W | OL468431W | ambiguous_author_record |
| F1_author_key | /authors/OL27363A | OL274505W | OL29355621W | ambiguous_author_record |
| F1_author_key | /authors/OL27363A | OL274505W | OL39215842W | ambiguous_author_record |
| F1_author_key | /authors/OL27363A | OL274505W | OL40693424W | ambiguous_author_record |
| F1_author_key | /authors/OL28104A | OL15574537W | OL37891094W | ambiguous_author_record |
| F1_author_key | /authors/OL28104A | OL15574537W | OL40873W | ambiguous_author_record |
| F1_author_key | /authors/OL29497A | OL102749W | OL25985378W | ambiguous_author_record |
| F1_author_key | /authors/OL29497A | OL102749W | OL30932533W | ambiguous_author_record |
| F1_author_key | /authors/OL29497A | OL102749W | OL40870684W | ambiguous_author_record |
| F1_author_key | /authors/OL29497A | OL102749W | OL43259285W | ambiguous_author_record |
| F1_author_key | /authors/OL31574A | OL28394745W | OL31856465W | ambiguous_author_record |
| F1_author_key | /authors/OL31574A | OL28394745W | OL70988W | ambiguous_author_record |
| F1_author_key | /authors/OL31901A | OL10263W | OL27581609W | ambiguous_author_record |
| F1_author_key | /authors/OL31901A | OL10263W | OL34698237W | ambiguous_author_record |
| F1_author_key | /authors/OL31901A | OL10263W | OL34904927W | ambiguous_author_record |
| F1_author_key | /authors/OL31901A | OL10263W | OL40190092W | ambiguous_author_record |
| F1_author_key | /authors/OL31901A | OL10263W | OL41505543W | ambiguous_author_record |
| F1_author_key | /authors/OL498120A | OL12977329W | OL20168372W | ambiguous_author_record |
| F1_author_key | /authors/OL498120A | OL12977329W | OL3140822W | ambiguous_author_record |
| F1_author_key | /authors/OL540486A | OL17845943W | OL20645663W | ambiguous_author_record |
| F1_author_key | /authors/OL540486A | OL17845943W | OL3335245W | ambiguous_author_record |
| F1_author_key | /authors/OL66452A | OL37980084W | OL40380270W | ambiguous_author_record |
| F1_author_key | /authors/OL66452A | OL37980084W | OL503666W | ambiguous_author_record |
| F1_author_key | /authors/OL9388A | OL25429126W | OL26030510W | ambiguous_author_record |
| F1_author_key | /authors/OL9388A | OL25429126W | OL362026W | ambiguous_author_record |
| F1_author_key | /authors/OL9388A | OL25429126W | OL362081W | ambiguous_author_record |
| F1_author_key | /authors/OL9388A | OL25429126W | OL362427W | ambiguous_author_record |
| F1_author_key | /authors/OL9388A | OL25429126W | OL41534707W | ambiguous_author_record |
| F1_author_key | /authors/OL9388A | OL25429126W | OL9170454W | ambiguous_author_record |
| F2_title | 1984 | OL1168083W | OL39821738W | generic_or_high_fanout_title (5 works) |
| F2_title | 1984 | OL1168083W | OL9251197W | generic_or_high_fanout_title (5 works) |
| F2_title | catcher in the rye | OL17845943W | OL7106216W | generic_or_high_fanout_title (4 works) |
| F2_title | cien anos de soledad | OL274505W | OL34628880W | generic_or_high_fanout_title (4 works) |
| F2_title | cien anos de soledad | OL274505W | OL43080931W | generic_or_high_fanout_title (4 works) |
| F2_title | count of monte cristo | OL10368778W | OL20201553W | generic_or_high_fanout_title (4 works) |
| F2_title | crime and punishment | OL166894W | OL6224648W | generic_or_high_fanout_title (4 works) |
| F2_title | don quixote | OL26322301W | OL37980084W | generic_or_high_fanout_title (6 works) |
| F2_title | don quixote | OL26322301W | OL43110094W | generic_or_high_fanout_title (6 works) |
| F2_title | don quixote | OL26322301W | OL8508677W | generic_or_high_fanout_title (6 works) |
| … 15 more in JSON | | | | |

## Proposed dev / held-out balance (by family hash)

Split seed 20261103, dev fraction 0.6.

| split | families | works | editions | works by group | editions by group |
|---|---|---|---|---|---|
| dev | 118 | 237 | 3527 | {'H': 83, 'S1': 33, 'S2': 20, 'S3': 15, 'S4': 24, 'S5': 6, 'S6': 24, 'S7': 32} | {'H': 2532, 'S1': 713, 'S2': 77, 'S3': 47, 'S4': 56, 'S5': 7, 'S6': 42, 'S7': 53} |
| heldout | 96 | 150 | 1839 | {'H': 29, 'S1': 27, 'S2': 10, 'S3': 15, 'S4': 16, 'S5': 9, 'S6': 16, 'S7': 28} | {'H': 1121, 'S1': 490, 'S2': 84, 'S3': 52, 'S4': 19, 'S5': 9, 'S6': 22, 'S7': 42} |

| probe | family | split |
|---|---|---|
| The Remains of the Day | probe-author:OL16606566A | heldout |
| Never Let Me Go | probe-author:OL16606566A | heldout |
| The Name of the Wind | probe-author:OL2830895A | dev |
| Station Eleven | probe-author:OL6538530A | heldout |
| The Left Hand of Darkness | probe-author:OL16568974A | dev |
| A Wizard of Earthsea | probe-author:OL16568974A | dev |
| Gödel, Escher, Bach | probe-author:OL12634513A | dev |
| Middlemarch | probe-author:OL10045454A | heldout |
| The Pragmatic Programmer | probe-author:OL1391034A | heldout |
| Their Eyes Were Watching God | probe-author:OL226273A | dev |

## Edition sampling

Method: seeded greedy max-coverage over format/language/decade/publisher/edition_statement; SHA-256(seed:key) tie-break (cap 60).

Works whose kept sample could not cover every distinct value, by dimension: {'language': 21, 'publisher': 39, 'edition_statement': 34, 'decade': 12, 'format': 2}

Missing-metadata rate across all sampled editions: {'format': 0.681, 'language': 0.142, 'decade': 0.014, 'publisher': 0.007, 'edition_statement': 0.683}

## Seed author identity (provisional candidates)

| seed | flags | candidates (key: editions credited in matched works) |
|---|---|---|
| Pride and Prejudice | multiple_records_same_name | OL21594A: 3664 |
| Frankenstein | multiple_records_same_name | OL25342A: 2221 |
| Moby Dick | multiple_records_same_name | OL29497A: 1083 |
| The Great Gatsby | multiple_records_same_name | OL27349A: 1072 |
| Nineteen Eighty-Four | multiple_records_same_name, several_candidate_records_credited_in_matched_works | OL118077A: 553, OL15318546A: 1, OL16029200A: 3, OL16230010A: 1 |
| 1984 | multiple_records_same_name, several_candidate_records_credited_in_matched_works | OL118077A: 553, OL15318546A: 1, OL16029200A: 3, OL16230010A: 1 |
| To Kill a Mockingbird | multiple_records_same_name | OL498120A: 139 |
| The Hobbit | — | OL26320A: 369 |
| The Lord of the Rings | — | OL26320A: 394 |
| The Fellowship of the Ring | — | OL26320A: 394 |
| Harry Potter and the Philosopher's Stone | multiple_records_same_name | OL23919A: 304 |
| Harry Potter and the Sorcerer's Stone | multiple_records_same_name | OL23919A: 304 |
| The Little Prince | multiple_records_same_name | OL31901A: 661 |
| Le Petit Prince | multiple_records_same_name | OL31901A: 661 |
| One Hundred Years of Solitude | multiple_records_same_name, different_birth_years_likely_different_people, several_candidate_records_credited_in_matched_works | OL15290656A: 3, OL27363A: 175 |
| Cien años de soledad | multiple_records_same_name, different_birth_years_likely_different_people, several_candidate_records_credited_in_matched_works | OL15290656A: 3, OL27363A: 175 |
| Don Quixote | multiple_records_same_name | OL66452A: 1098 |
| War and Peace | multiple_records_same_name, different_birth_years_likely_different_people | OL26783A: 629 |
| Crime and Punishment | — | OL22242A: 1145 |
| The Odyssey | multiple_records_same_name, several_candidate_records_credited_in_matched_works | OL18404A: 1360, OL4589724A: 1, OL4589725A: 1 |
| Hamlet | multiple_records_same_name, different_birth_years_likely_different_people, several_candidate_records_credited_in_matched_works | OL2832629A: 21, OL9388A: 2346 |
| Romeo and Juliet | multiple_records_same_name, different_birth_years_likely_different_people, several_candidate_records_credited_in_matched_works | OL2832629A: 21, OL9388A: 1416 |
| The Catcher in the Rye | multiple_records_same_name, several_candidate_records_credited_in_matched_works | OL13116434A: 1, OL540486A: 151 |
| Of Mice and Men | multiple_records_same_name, different_birth_years_likely_different_people | OL25788A: 230 |
| Dune | multiple_records_same_name, different_birth_years_likely_different_people | OL79034A: 126 |
| The Hunger Games | multiple_records_same_name, different_birth_years_likely_different_people, several_candidate_records_credited_in_matched_works | OL12737091A: 15, OL1394359A: 76 |
| A Game of Thrones | multiple_records_same_name | OL234664A: 66 |
| The Chronicles of Narnia | multiple_records_same_name | OL31574A: 51 |
| Introduction to Algorithms | no_birth_year_on_any_record | OL1004780A: 15 |
| The C Programming Language | — | OL946967A: 41 |
| Structure and Interpretation of Computer Programs | multiple_records_same_name, several_candidate_records_credited_in_matched_works | OL14042988A: 2, OL532838A: 12 |
| The Elements of Style | — | OL2625113A: 336 |
| Little Women | multiple_records_same_name, different_birth_years_likely_different_people | OL26680A: 1860 |
| Jane Eyre | multiple_records_same_name | OL113362A: 1492 |
| Wuthering Heights | multiple_records_same_name, several_candidate_records_credited_in_matched_works | OL15108810A: 21, OL24529A: 784 |
| Alice's Adventures in Wonderland | multiple_records_same_name | OL22098A: 3309 |
| The Picture of Dorian Gray | multiple_records_same_name | OL20646A: 2890 |
| Dracula | multiple_records_same_name, several_candidate_records_credited_in_matched_works | OL10316489A: 900, OL11510274A: 1, OL11977244A: 1, OL12693789A: 3, OL12693790A: 1, OL15293680A: 2, OL15312690A: 1, OL15368964A: 1, OL31727A: 1360 |
| Les Misérables | multiple_records_same_name | OL107571A: 601 |
| The Count of Monte Cristo | multiple_records_same_name, different_birth_years_likely_different_people, several_candidate_records_credited_in_matched_works | OL18236A: 675, OL6819624A: 1 |
| Beloved | — | OL31120A: 94 |
| The Road | multiple_records_same_name | OL28104A: 69 |

## Probe author identity and pre-audit

| probe | identity flags | provisional pre-audit | reasons |
|---|---|---|---|
| The Remains of the Day | multiple_records_same_name | verified_absent | — |
| Never Let Me Go | multiple_records_same_name | verified_absent | — |
| The Name of the Wind | — | verified_absent | — |
| Station Eleven | — | quarantined | 2_resembling_editions |
| The Left Hand of Darkness | multiple_records_same_name, several_candidate_records_credited_in_matched_works | quarantined | 2_resembling_editions |
| A Wizard of Earthsea | multiple_records_same_name, several_candidate_records_credited_in_matched_works | quarantined | 2_resembling_editions |
| Gödel, Escher, Bach | multiple_records_same_name, several_candidate_records_credited_in_matched_works | verified_absent | — |
| Middlemarch | multiple_records_same_name, several_candidate_records_credited_in_matched_works | verified_absent | — |
| The Pragmatic Programmer | multiple_records_same_name, different_birth_years_likely_different_people, several_candidate_records_credited_in_matched_works | quarantined | 14_resembling_editions |
| Their Eyes Were Watching God | — | verified_absent | — |

## Selected works

| group | work | family | title | editions avail→sampled | distinct kept (fmt lang deca publ edit) | missing rate kept |
|---|---|---|---|---|---|---|
| H | OL10263W | fam:OL10263W | little prince | 700→60 | form=6 lang=38 deca=9 publ=60 edit=39 | form=0.683 lang=0.05 deca=0.0 publ=0.0 edit=0.35 |
| H | OL102749W | fam:OL102749W | moby dick | 1129→60 | form=6 lang=19 deca=14 publ=60 edit=42 | form=0.5 lang=0.05 deca=0.017 publ=0.0 edit=0.3 |
| H | OL1063588W | fam:OL1063588W | les misérables | 557→60 | form=6 lang=14 deca=17 publ=60 edit=47 | form=0.65 lang=0.083 deca=0.017 publ=0.0 edit=0.217 |
| H | OL1095427W | fam:OL1095427W | jane eyre | 1172→60 | form=6 lang=15 deca=17 publ=59 edit=47 | form=0.683 lang=0.067 deca=0.017 publ=0.0 edit=0.217 |
| H | OL1168083W | fam:OL102749W | 1984 | 727→60 | form=6 lang=25 deca=9 publ=60 edit=41 | form=0.4 lang=0.067 deca=0.033 publ=0.0 edit=0.317 |
| H | OL12977329W | fam:OL12977329W | to kill a mockingbird | 1→1 | form=0 lang=1 deca=0 publ=1 edit=0 | form=1.0 lang=0.0 deca=1.0 publ=0.0 edit=1.0 |
| H | OL138052W | fam:OL138052W | alices adventures in wonderland | 3548→60 | form=7 lang=28 deca=17 publ=60 edit=46 | form=0.483 lang=0.033 deca=0.0 publ=0.0 edit=0.233 |
| H | OL14930024W | fam:OL14930024W | dracula | 288→60 | form=2 lang=7 deca=8 publ=57 edit=5 | form=0.683 lang=0.45 deca=0.133 publ=0.017 edit=0.917 |
| H | OL14942752W | fam:OL14942752W | of mice and men | 3→3 | form=1 lang=1 deca=2 publ=2 edit=0 | form=0.0 lang=0.333 deca=0.0 publ=0.0 edit=1.0 |
| H | OL15165350W | fam:OL15165350W | pride and prejudice | 132→60 | form=2 lang=4 deca=16 publ=55 edit=9 | form=0.867 lang=0.033 deca=0.017 publ=0.017 edit=0.85 |
| H | OL15267600W | fam:OL102749W | harry potter and the sorcerers stone | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL15574537W | fam:OL15574537W | road | 6→6 | form=0 lang=1 deca=1 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL166894W | fam:OL102749W | crime and punishment | 1178→60 | form=6 lang=22 deca=16 publ=60 edit=39 | form=0.6 lang=0.1 deca=0.033 publ=0.0 edit=0.35 |
| H | OL17412540W | fam:OL16261015W | game of thrones | 4→4 | form=0 lang=1 deca=2 publ=3 edit=0 | form=1.0 lang=0.5 deca=0.0 publ=0.0 edit=1.0 |
| H | OL17512507W | fam:OL16261015W | game of thrones | 3→3 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.333 deca=0.0 publ=0.0 edit=1.0 |
| H | OL17829994W | fam:OL14942752W | of mice and men | 16→16 | form=2 lang=1 deca=6 publ=9 edit=2 | form=0.688 lang=0.25 deca=0.0 publ=0.0 edit=0.688 |
| H | OL17845943W | fam:OL17845943W | the catcher in the rye | 1→1 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL17937389W | fam:OL102749W | harry potter and the sorcerers stone | 1→1 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL19618275W | fam:OL102749W | dune | 10→10 | form=4 lang=1 deca=3 publ=7 edit=0 | form=0.3 lang=0.6 deca=0.0 publ=0.0 edit=1.0 |
| H | OL19952185W | fam:OL19952185W | the hunger games | 5→5 | form=1 lang=1 deca=1 publ=2 edit=1 | form=0.2 lang=0.8 deca=0.0 publ=0.0 edit=0.8 |
| H | OL19961152W | fam:OL102749W | hobbit | 3→3 | form=0 lang=2 deca=1 publ=3 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.667 |
| H | OL20168372W | fam:OL12977329W | to kill a mockingbird | 2→2 | form=1 lang=1 deca=2 publ=2 edit=0 | form=0.5 lang=0.5 deca=0.0 publ=0.0 edit=1.0 |
| H | OL20201553W | fam:OL102749W | count of monte cristo | 13→13 | form=2 lang=1 deca=3 publ=9 edit=0 | form=0.846 lang=0.154 deca=0.0 publ=0.0 edit=1.0 |
| H | OL20645663W | fam:OL17845943W | the catcher in the rye | 1→1 | form=0 lang=1 deca=0 publ=1 edit=0 | form=1.0 lang=0.0 deca=1.0 publ=0.0 edit=1.0 |
| H | OL20662064W | fam:OL102749W | harry potter and the philosophers stone | 1→1 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL20832265W | fam:OL102749W | dune | 13→13 | form=3 lang=1 deca=2 publ=7 edit=0 | form=0.385 lang=0.538 deca=0.077 publ=0.0 edit=1.0 |
| H | OL21170W | fam:OL102749W | wuthering heights | 18→18 | form=2 lang=1 deca=6 publ=6 edit=3 | form=0.667 lang=0.056 deca=0.111 publ=0.056 edit=0.667 |
| H | OL21177W | fam:OL102749W | wuthering heights | 2895→60 | form=6 lang=19 deca=18 publ=60 edit=53 | form=0.383 lang=0.0 deca=0.033 publ=0.0 edit=0.117 |
| H | OL219602W | fam:OL102749W | the hobbit | 10→10 | form=2 lang=3 deca=3 publ=8 edit=3 | form=0.6 lang=0.1 deca=0.0 publ=0.0 edit=0.6 |
| H | OL23204W | fam:OL14942752W | of mice and men | 293→60 | form=6 lang=22 deca=10 publ=60 edit=35 | form=0.45 lang=0.067 deca=0.017 publ=0.0 edit=0.417 |
| H | OL235881W | fam:OL15165350W | pride and prejudice | 15→15 | form=2 lang=1 deca=3 publ=8 edit=1 | form=0.6 lang=0.4 deca=0.0 publ=0.0 edit=0.933 |
| H | OL23745689W | fam:OL102749W | 1984 | 7→7 | form=2 lang=2 deca=2 publ=4 edit=1 | form=0.429 lang=0.429 deca=0.0 publ=0.0 edit=0.857 |
| H | OL24596091W | fam:OL102749W | the picture of dorian gray | 6→6 | form=2 lang=0 deca=1 publ=3 edit=0 | form=0.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL25429126W | fam:OL15165350W | hamlet | 81→60 | form=1 lang=7 deca=4 publ=8 edit=0 | form=0.967 lang=0.017 deca=0.0 publ=0.0 edit=1.0 |
| H | OL25595002W | fam:OL17504079W | frankenstein | 90→60 | form=3 lang=3 deca=6 publ=28 edit=7 | form=0.833 lang=0.1 deca=0.0 publ=0.0 edit=0.883 |
| H | OL257943W | fam:OL16261015W | a game of thrones | 136→60 | form=6 lang=17 deca=4 publ=52 edit=24 | form=0.183 lang=0.233 deca=0.0 publ=0.0 edit=0.583 |
| H | OL25965892W | fam:OL102749W | picture of dorian gray | 8→8 | form=1 lang=1 deca=2 publ=3 edit=0 | form=0.875 lang=0.125 deca=0.0 publ=0.0 edit=1.0 |
| H | OL25985378W | fam:OL102749W | moby dick | 25→25 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL26030510W | fam:OL15165350W | romeo and juliet | 342→60 | form=2 lang=6 deca=8 publ=54 edit=2 | form=0.683 lang=0.35 deca=0.017 publ=0.0 edit=0.967 |
| H | OL26446888W | fam:OL26446888W | odyssey | 118→60 | form=0 lang=1 deca=8 publ=50 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL26507392W | fam:OL26507392W | elements of style | 43→43 | form=0 lang=1 deca=5 publ=19 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL267171W | fam:OL267171W | war and peace | 647→60 | form=6 lang=16 deca=17 publ=59 edit=36 | form=0.633 lang=0.1 deca=0.033 publ=0.017 edit=0.4 |
| H | OL26784440W | fam:OL26446888W | odyssey | 240→60 | form=1 lang=2 deca=5 publ=24 edit=0 | form=0.967 lang=0.017 deca=0.0 publ=0.0 edit=1.0 |
| H | OL27448W | fam:OL102749W | the lord of the rings | 253→60 | form=4 lang=18 deca=7 publ=57 edit=27 | form=0.483 lang=0.2 deca=0.033 publ=0.0 edit=0.533 |
| H | OL274505W | fam:OL274505W | cien años de soledad | 208→60 | form=4 lang=16 deca=7 publ=58 edit=35 | form=0.633 lang=0.133 deca=0.0 publ=0.0 edit=0.4 |
| H | OL27482W | fam:OL102749W | the hobbit | 482→60 | form=7 lang=25 deca=9 publ=60 edit=49 | form=0.317 lang=0.05 deca=0.0 publ=0.0 edit=0.183 |
| H | OL27513W | fam:OL102749W | the fellowship of the ring | 319→60 | form=5 lang=26 deca=8 publ=58 edit=44 | form=0.283 lang=0.0 deca=0.0 publ=0.0 edit=0.267 |
| H | OL27581609W | fam:OL10263W | petit prince | 3→3 | form=0 lang=1 deca=2 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL28165123W | fam:OL102749W | crime and punishment | 8→8 | form=0 lang=1 deca=3 publ=3 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL28394745W | fam:OL28394745W | chronicles of narnia | 4→4 | form=0 lang=1 deca=2 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL28897559W | fam:OL138052W | alices adventures in wonderland | 13→13 | form=0 lang=1 deca=2 publ=5 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL29355621W | fam:OL274505W | one hundred years of solitude | 2→2 | form=0 lang=1 deca=2 publ=2 edit=0 | form=1.0 lang=0.5 deca=0.0 publ=0.0 edit=1.0 |
| H | OL29983W | fam:OL29983W | little women | 1890→60 | form=7 lang=14 deca=17 publ=60 edit=45 | form=0.6 lang=0.117 deca=0.0 publ=0.0 edit=0.25 |
| H | OL30932533W | fam:OL102749W | moby dick | 20→20 | form=0 lang=4 deca=1 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL31040865W | fam:OL138052W | alices adventures in wonderland | 11→11 | form=0 lang=1 deca=1 publ=4 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL3140822W | fam:OL12977329W | to kill a mockingbird | 214→60 | form=5 lang=14 deca=7 publ=60 edit=29 | form=0.517 lang=0.2 deca=0.0 publ=0.0 edit=0.517 |
| H | OL31701067W | fam:OL102749W | great gatsby | 55→55 | form=0 lang=3 deca=4 publ=12 edit=0 | form=1.0 lang=0.018 deca=0.0 publ=0.0 edit=1.0 |
| H | OL31856465W | fam:OL28394745W | chronicles of narnia | 3→3 | form=0 lang=1 deca=3 publ=3 edit=0 | form=1.0 lang=0.667 deca=0.0 publ=0.0 edit=1.0 |
| H | OL32417366W | fam:OL1095427W | jane eyre | 38→38 | form=0 lang=4 deca=6 publ=10 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL32525579W | fam:OL102749W | crime and punishment | 18→18 | form=0 lang=1 deca=4 publ=6 edit=0 | form=1.0 lang=0.167 deca=0.0 publ=0.0 edit=1.0 |
| H | OL3267304W | fam:OL3267304W | structure and interpretation of computer programs | 16→16 | form=2 lang=4 deca=5 publ=9 edit=5 | form=0.688 lang=0.312 deca=0.0 publ=0.0 edit=0.625 |
| H | OL3335245W | fam:OL17845943W | the catcher in the rye | 204→60 | form=5 lang=16 deca=8 publ=58 edit=23 | form=0.55 lang=0.2 deca=0.017 publ=0.017 edit=0.6 |
| H | OL34698237W | fam:OL10263W | little prince | 5→5 | form=0 lang=1 deca=2 publ=5 edit=0 | form=1.0 lang=0.6 deca=0.0 publ=0.0 edit=1.0 |
| H | OL34714467W | fam:OL102749W | the lord of the rings | 1→1 | form=0 lang=0 deca=1 publ=1 edit=0 | form=1.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL34904927W | fam:OL10263W | le petit prince | 3→3 | form=1 lang=1 deca=2 publ=2 edit=0 | form=0.667 lang=0.667 deca=0.0 publ=0.0 edit=1.0 |
| H | OL35362573W | fam:OL102749W | the count of monte cristo | 18→18 | form=1 lang=3 deca=8 publ=14 edit=0 | form=0.944 lang=0.0 deca=0.333 publ=0.0 edit=1.0 |
| H | OL36007535W | fam:OL26507392W | elements of style | 31→31 | form=0 lang=1 deca=2 publ=3 edit=0 | form=1.0 lang=0.065 deca=0.0 publ=0.0 edit=1.0 |
| H | OL36141872W | fam:OL17504079W | frankenstein | 43→43 | form=0 lang=6 deca=2 publ=10 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL362026W | fam:OL15165350W | romeo and juliet | 290→60 | form=2 lang=3 deca=5 publ=22 edit=3 | form=0.833 lang=0.117 deca=0.0 publ=0.0 edit=0.95 |
| H | OL362081W | fam:OL15165350W | hamlet | 84→60 | form=0 lang=17 deca=20 publ=44 edit=3 | form=1.0 lang=0.1 deca=0.0 publ=0.0 edit=0.95 |
| H | OL362427W | fam:OL15165350W | romeo and juliet | 987→60 | form=6 lang=15 deca=27 publ=60 edit=47 | form=0.5 lang=0.0 deca=0.0 publ=0.0 edit=0.217 |
| H | OL36287W | fam:OL102749W | count of monte cristo | 737→60 | form=6 lang=27 deca=20 publ=60 edit=36 | form=0.783 lang=0.017 deca=0.017 publ=0.0 edit=0.4 |
| H | OL36765642W | fam:OL267171W | war and peace | 154→60 | form=0 lang=2 deca=7 publ=27 edit=0 | form=1.0 lang=0.017 deca=0.0 publ=0.0 edit=1.0 |
| H | OL36900288W | fam:OL29983W | little women | 32→32 | form=0 lang=1 deca=11 publ=13 edit=0 | form=1.0 lang=0.094 deca=0.0 publ=0.031 edit=1.0 |
| H | OL37629951W | fam:OL102749W | great gatsby | 64→60 | form=0 lang=4 deca=6 publ=34 edit=0 | form=1.0 lang=0.017 deca=0.0 publ=0.0 edit=1.0 |
| H | OL37840844W | fam:OL1095427W | jane eyre | 558→60 | form=1 lang=9 deca=8 publ=59 edit=0 | form=0.983 lang=0.033 deca=0.017 publ=0.0 edit=1.0 |
| H | OL37891094W | fam:OL15574537W | the road | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL37980084W | fam:OL20463684W | don quixote | 8→8 | form=0 lang=1 deca=2 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL38128342W | fam:OL102749W | lord of the rings | 2→2 | form=0 lang=1 deca=2 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL38285W | fam:OL26507392W | the elements of style | 288→60 | form=6 lang=1 deca=10 publ=48 edit=31 | form=0.367 lang=0.267 deca=0.0 publ=0.0 edit=0.483 |
| H | OL39109952W | fam:OL3267304W | structure and interpretation of computer programs | 2→2 | form=0 lang=1 deca=2 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL39134546W | fam:OL29983W | little women | 10→10 | form=0 lang=1 deca=1 publ=9 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL39215842W | fam:OL274505W | one hundred years of solitude | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL40190092W | fam:OL10263W | little prince | 5→5 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL40255790W | fam:OL267171W | war and peace | 12→12 | form=0 lang=1 deca=2 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL40380270W | fam:OL20463684W | don quixote | 8→8 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL40516131W | fam:OL1063588W | los miserables | 19→19 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL40542345W | fam:OL1063588W | miserables | 83→60 | form=0 lang=2 deca=2 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL40693424W | fam:OL274505W | cien años de soledad | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL40873W | fam:OL15574537W | the road | 84→60 | form=5 lang=9 deca=3 publ=46 edit=16 | form=0.467 lang=0.3 deca=0.0 publ=0.0 edit=0.7 |
| H | OL41505543W | fam:OL10263W | petit prince | 4→4 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| H | OL43008309W | fam:OL102749W | wuthering heights | 21→21 | form=0 lang=1 deca=9 publ=19 edit=2 | form=1.0 lang=0.0 deca=0.0 publ=0.048 edit=0.905 |
| H | OL43080931W | fam:OL274505W | cien anos de soledad | 1→1 | form=0 lang=1 deca=1 publ=0 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=1.0 edit=1.0 |
| H | OL43108828W | fam:OL274505W | one hundred years of solitude | 2→2 | form=0 lang=1 deca=2 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.5 edit=1.0 |
| H | OL450063W | fam:OL17504079W | frankenstein | 2187→60 | form=6 lang=9 deca=18 publ=60 edit=45 | form=0.533 lang=0.083 deca=0.017 publ=0.0 edit=0.25 |
| H | OL4617640W | fam:OL4617640W | c programming language | 50→50 | form=2 lang=12 deca=6 publ=18 edit=12 | form=0.6 lang=0.32 deca=0.02 publ=0.0 edit=0.74 |
| H | OL468431W | fam:OL102749W | great gatsby | 1181→60 | form=6 lang=16 deca=11 publ=60 edit=43 | form=0.5 lang=0.05 deca=0.0 publ=0.0 edit=0.283 |
| H | OL4781294W | fam:OL4781294W | introduction to algorithms | 18→18 | form=2 lang=1 deca=4 publ=3 edit=4 | form=0.667 lang=0.111 deca=0.0 publ=0.0 edit=0.611 |
| H | OL503666W | fam:OL20463684W | don quixote | 1595→60 | form=4 lang=16 deca=38 publ=60 edit=53 | form=0.883 lang=0.017 deca=0.0 publ=0.0 edit=0.117 |
| H | OL50548W | fam:OL17728718W | beloved | 111→60 | form=6 lang=13 deca=5 publ=60 edit=9 | form=0.633 lang=0.183 deca=0.033 publ=0.0 edit=0.833 |
| H | OL5093999W | fam:OL102749W | nineteen eighty four | 2→2 | form=1 lang=1 deca=1 publ=2 edit=1 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=0.5 |
| H | OL5735363W | fam:OL19952185W | the hunger games | 143→60 | form=5 lang=19 deca=3 publ=54 edit=18 | form=0.433 lang=0.267 deca=0.017 publ=0.0 edit=0.7 |
| H | OL61982W | fam:OL26446888W | the odyssey | 1067→60 | form=6 lang=15 deca=37 publ=60 edit=47 | form=0.733 lang=0.067 deca=0.0 publ=0.0 edit=0.217 |
| H | OL66554W | fam:OL15165350W | pride and prejudice | 4085→60 | form=6 lang=13 deca=19 publ=60 edit=51 | form=0.233 lang=0.017 deca=0.0 publ=0.0 edit=0.15 |
| H | OL6934191W | fam:OL102749W | 1984 | 5→5 | form=1 lang=1 deca=4 publ=2 edit=0 | form=0.8 lang=0.2 deca=0.0 publ=0.2 edit=1.0 |
| H | OL70988W | fam:OL28394745W | the chronicles of narnia | 60→60 | form=3 lang=4 deca=5 publ=35 edit=18 | form=0.417 lang=0.383 deca=0.083 publ=0.017 edit=0.65 |
| H | OL8193416W | fam:OL102749W | picture of dorian gray | 3013→60 | form=6 lang=19 deca=14 publ=60 edit=46 | form=0.683 lang=0.05 deca=0.0 publ=0.0 edit=0.233 |
| H | OL82563W | fam:OL102749W | harry potter and the philosophers stone | 402→60 | form=7 lang=43 deca=4 publ=60 edit=38 | form=0.467 lang=0.033 deca=0.017 publ=0.0 edit=0.367 |
| H | OL85875W | fam:OL14930024W | dracula | 598→60 | form=4 lang=7 deca=10 publ=59 edit=2 | form=0.65 lang=0.417 deca=0.05 publ=0.0 edit=0.967 |
| H | OL85892W | fam:OL14930024W | dracula | 1919→60 | form=7 lang=14 deca=12 publ=60 edit=49 | form=0.133 lang=0.117 deca=0.0 publ=0.0 edit=0.183 |
| H | OL893414W | fam:OL102749W | dune | 155→60 | form=6 lang=13 deca=7 publ=58 edit=21 | form=0.483 lang=0.217 deca=0.017 publ=0.0 edit=0.65 |
| H | OL9170454W | fam:OL15165350W | hamlet | 2496→60 | form=6 lang=25 deca=30 publ=60 edit=49 | form=0.717 lang=0.017 deca=0.0 publ=0.0 edit=0.183 |
| S1 | OL1128022W | fam:OL1128022W | three partners | 23→23 | form=2 lang=1 deca=4 publ=13 edit=1 | form=0.391 lang=0.043 deca=0.0 publ=0.0 edit=0.957 |
| S1 | OL118132W | fam:OL118132W | see more readers | 13→13 | form=2 lang=1 deca=1 publ=2 edit=1 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=0.769 |
| S1 | OL1214250W | fam:OL1214250W | ideas and opinions | 15→15 | form=2 lang=1 deca=6 publ=13 edit=1 | form=0.8 lang=0.133 deca=0.0 publ=0.0 edit=0.933 |
| S1 | OL12872598W | fam:OL12872598W | the modern history of universalism | 9→9 | form=2 lang=1 deca=3 publ=5 edit=0 | form=0.556 lang=0.444 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL144305W | fam:OL144305W | sas | 10→10 | form=3 lang=1 deca=3 publ=6 edit=1 | form=0.5 lang=0.1 deca=0.0 publ=0.0 edit=0.9 |
| S1 | OL14909364W | fam:OL14909364W | the girl who kicked the hornets nest | 48→48 | form=5 lang=8 deca=3 publ=26 edit=6 | form=0.75 lang=0.354 deca=0.021 publ=0.021 edit=0.812 |
| S1 | OL14949682W | fam:OL14949682W | deliver us from evil | 26→26 | form=3 lang=2 deca=2 publ=12 edit=2 | form=0.654 lang=0.308 deca=0.0 publ=0.0 edit=0.885 |
| S1 | OL1527080W | fam:OL1527080W | de viris illustribus urbis romæ | 56→56 | form=2 lang=3 deca=16 publ=31 edit=16 | form=0.964 lang=0.018 deca=0.0 publ=0.018 edit=0.607 |
| S1 | OL1542661W | fam:OL1542661W | the montessori method | 54→54 | form=3 lang=3 deca=9 publ=31 edit=12 | form=0.667 lang=0.093 deca=0.056 publ=0.019 edit=0.722 |
| S1 | OL15464930W | fam:OL15464930W | tiger moon | 8→8 | form=2 lang=6 deca=2 publ=8 edit=3 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=0.625 |
| S1 | OL15688543W | fam:OL15688543W | world without heroes | 8→8 | form=2 lang=3 deca=1 publ=6 edit=1 | form=0.75 lang=0.25 deca=0.0 publ=0.0 edit=0.875 |
| S1 | OL16042490W | fam:OL16042490W | seahorse reef | 8→8 | form=2 lang=1 deca=1 publ=4 edit=3 | form=0.25 lang=0.0 deca=0.0 publ=0.0 edit=0.625 |
| S1 | OL16261015W | fam:OL16261015W | songs of the dying earth | 12→12 | form=2 lang=1 deca=2 publ=8 edit=1 | form=0.75 lang=0.333 deca=0.0 publ=0.0 edit=0.917 |
| S1 | OL167133W | fam:OL167133W | the pusher | 18→18 | form=3 lang=2 deca=7 publ=15 edit=3 | form=0.556 lang=0.167 deca=0.0 publ=0.0 edit=0.833 |
| S1 | OL17358870W | fam:OL17358870W | all dressed in white | 11→11 | form=2 lang=1 deca=1 publ=5 edit=2 | form=0.818 lang=0.182 deca=0.0 publ=0.182 edit=0.818 |
| S1 | OL17378277W | fam:OL17378277W | an astronauts guide to life on earth | 15→15 | form=2 lang=4 deca=2 publ=11 edit=3 | form=0.8 lang=0.133 deca=0.0 publ=0.0 edit=0.8 |
| S1 | OL17930368W | fam:OL17930368W | atomic habits | 42→42 | form=4 lang=7 deca=2 publ=26 edit=0 | form=0.405 lang=0.476 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL1794485W | fam:OL1794485W | beric the briton | 186→60 | form=4 lang=1 deca=8 publ=38 edit=0 | form=0.75 lang=0.133 deca=0.017 publ=0.017 edit=1.0 |
| S1 | OL18139W | fam:OL18139W | a legal fiction | 13→13 | form=3 lang=1 deca=6 publ=10 edit=5 | form=0.692 lang=0.231 deca=0.0 publ=0.0 edit=0.615 |
| S1 | OL1822441W | fam:OL1822441W | the woman warrior | 17→17 | form=4 lang=3 deca=5 publ=13 edit=3 | form=0.765 lang=0.059 deca=0.059 publ=0.0 edit=0.765 |
| S1 | OL18276728W | fam:OL18276728W | developmental spans in event comprehension and representation | 8→8 | form=2 lang=1 deca=2 publ=4 edit=1 | form=0.75 lang=0.0 deca=0.0 publ=0.0 edit=0.75 |
| S1 | OL18617W | fam:OL18617W | the silver hand | 21→21 | form=3 lang=2 deca=3 publ=15 edit=4 | form=0.476 lang=0.238 deca=0.0 publ=0.0 edit=0.762 |
| S1 | OL1881658W | fam:OL1881658W | master of the game | 50→50 | form=5 lang=7 deca=5 publ=34 edit=7 | form=0.74 lang=0.3 deca=0.04 publ=0.04 edit=0.82 |
| S1 | OL19087868W | fam:OL19087868W | girl interrupted | 13→13 | form=4 lang=1 deca=4 publ=8 edit=0 | form=0.538 lang=0.615 deca=0.0 publ=0.077 edit=1.0 |
| S1 | OL19356364W | fam:OL19356364W | private paris | 16→16 | form=3 lang=1 deca=1 publ=10 edit=1 | form=0.812 lang=0.125 deca=0.062 publ=0.0 edit=0.938 |
| S1 | OL19731786W | fam:OL19731786W | first man | 9→9 | form=3 lang=1 deca=2 publ=4 edit=1 | form=0.667 lang=0.444 deca=0.0 publ=0.0 edit=0.889 |
| S1 | OL1992670W | fam:OL1992670W | the mass psychology of fascism | 35→35 | form=3 lang=6 deca=8 publ=23 edit=9 | form=0.743 lang=0.2 deca=0.057 publ=0.086 edit=0.743 |
| S1 | OL2005703W | fam:OL2005703W | killing the dream | 10→10 | form=2 lang=1 deca=2 publ=6 edit=2 | form=0.7 lang=0.3 deca=0.0 publ=0.0 edit=0.8 |
| S1 | OL20643040W | fam:OL20643040W | including students with special needs | 13→13 | form=2 lang=1 deca=3 publ=4 edit=1 | form=0.769 lang=0.308 deca=0.0 publ=0.0 edit=0.923 |
| S1 | OL21997589W | fam:OL21997589W | beautiful necessity | 32→32 | form=2 lang=1 deca=2 publ=6 edit=0 | form=0.875 lang=0.125 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL22134825W | fam:OL102749W | possessed | 127→60 | form=3 lang=1 deca=13 publ=25 edit=0 | form=0.9 lang=0.267 deca=0.0 publ=0.017 edit=1.0 |
| S1 | OL22855592W | fam:OL22855592W | narrative of the life of moses grandy | 10→10 | form=2 lang=1 deca=4 publ=6 edit=0 | form=0.5 lang=0.5 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL23252W | fam:OL23252W | sharpes prey | 16→16 | form=3 lang=1 deca=2 publ=9 edit=2 | form=0.812 lang=0.125 deca=0.062 publ=0.062 edit=0.812 |
| S1 | OL24188392W | fam:OL24188392W | the history of the island of antigua one of the leeward caribbes in the west indies from the first settlement in 1635 to the present time | 8→8 | form=2 lang=1 deca=2 publ=3 edit=0 | form=0.25 lang=0.75 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL24202784W | fam:OL24202784W | madness of crowds | 12→12 | form=5 lang=1 deca=1 publ=6 edit=0 | form=0.583 lang=0.333 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL24418304W | fam:OL15165350W | complete works of william shakespeare | 9→9 | form=2 lang=1 deca=2 publ=4 edit=0 | form=0.667 lang=0.333 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL26231798W | fam:OL26231798W | one mans initiation 1917 | 9→9 | form=2 lang=1 deca=2 publ=5 edit=0 | form=0.778 lang=0.222 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL276653W | fam:OL276653W | the lost queen | 8→8 | form=3 lang=1 deca=1 publ=2 edit=1 | form=0.625 lang=0.0 deca=0.0 publ=0.0 edit=0.625 |
| S1 | OL2928020W | fam:OL2928020W | scientific progress | 13→13 | form=2 lang=1 deca=4 publ=4 edit=3 | form=0.538 lang=0.308 deca=0.0 publ=0.0 edit=0.769 |
| S1 | OL29315066W | fam:OL29315066W | science and health with key to the scriptures | 15→15 | form=3 lang=1 deca=8 publ=11 edit=0 | form=0.733 lang=0.533 deca=0.0 publ=0.067 edit=1.0 |
| S1 | OL29430W | fam:OL29430W | franklins secret club | 20→20 | form=4 lang=4 deca=3 publ=12 edit=0 | form=0.55 lang=0.2 deca=0.05 publ=0.0 edit=1.0 |
| S1 | OL3389024W | fam:OL3389024W | the angels of mons | 21→21 | form=2 lang=1 deca=5 publ=14 edit=1 | form=0.667 lang=0.19 deca=0.048 publ=0.0 edit=0.952 |
| S1 | OL3453135W | fam:OL3453135W | dirty weekend | 9→9 | form=2 lang=1 deca=2 publ=6 edit=1 | form=0.667 lang=0.333 deca=0.0 publ=0.0 edit=0.889 |
| S1 | OL3657210W | fam:OL3657210W | mr tickle | 16→16 | form=5 lang=2 deca=5 publ=12 edit=1 | form=0.438 lang=0.25 deca=0.062 publ=0.0 edit=0.875 |
| S1 | OL3787232W | fam:OL3787232W | a breed of heroes | 10→10 | form=2 lang=1 deca=3 publ=8 edit=4 | form=0.6 lang=0.5 deca=0.0 publ=0.0 edit=0.6 |
| S1 | OL4056550W | fam:OL4056550W | ginos arranged bride | 11→11 | form=2 lang=1 deca=2 publ=3 edit=3 | form=0.545 lang=0.091 deca=0.0 publ=0.0 edit=0.545 |
| S1 | OL4112829W | fam:OL4112829W | felo de se | 32→32 | form=2 lang=1 deca=5 publ=5 edit=0 | form=0.938 lang=0.031 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL4114751W | fam:OL28168849W | frida | 10→10 | form=2 lang=2 deca=2 publ=6 edit=4 | form=0.2 lang=0.3 deca=0.0 publ=0.0 edit=0.5 |
| S1 | OL4127441W | fam:OL4127441W | costume | 8→8 | form=3 lang=2 deca=2 publ=6 edit=3 | form=0.375 lang=0.25 deca=0.0 publ=0.0 edit=0.5 |
| S1 | OL483385W | fam:OL26507392W | stuart little | 92→60 | form=4 lang=7 deca=8 publ=54 edit=15 | form=0.383 lang=0.35 deca=0.017 publ=0.0 edit=0.75 |
| S1 | OL4977012W | fam:OL4977012W | wonderful adventures of mrs seacole in many lands | 62→60 | form=2 lang=3 deca=6 publ=30 edit=2 | form=0.85 lang=0.2 deca=0.0 publ=0.0 edit=0.967 |
| S1 | OL55205W | fam:OL55205W | the hand of the necromancer | 8→8 | form=2 lang=1 deca=2 publ=5 edit=1 | form=0.75 lang=0.125 deca=0.0 publ=0.0 edit=0.75 |
| S1 | OL56476W | fam:OL56476W | bad boy | 15→15 | form=3 lang=1 deca=1 publ=11 edit=5 | form=0.533 lang=0.2 deca=0.0 publ=0.0 edit=0.533 |
| S1 | OL58920W | fam:OL58920W | crossing the threshold of hope | 13→13 | form=2 lang=6 deca=2 publ=12 edit=6 | form=0.769 lang=0.0 deca=0.0 publ=0.0 edit=0.538 |
| S1 | OL71645W | fam:OL71645W | deterring democracy | 17→17 | form=2 lang=4 deca=4 publ=12 edit=4 | form=0.647 lang=0.118 deca=0.059 publ=0.059 edit=0.765 |
| S1 | OL7920569W | fam:OL7920569W | the engineer of human souls | 15→15 | form=2 lang=1 deca=4 publ=9 edit=0 | form=0.467 lang=0.867 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL8347651W | fam:OL8347651W | mystic christianity or the inner teachings of the master | 10→10 | form=3 lang=1 deca=2 publ=8 edit=0 | form=0.0 lang=0.1 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL8383189W | fam:OL8383189W | garden spells | 11→11 | form=4 lang=1 deca=1 publ=10 edit=5 | form=0.182 lang=0.182 deca=0.0 publ=0.0 edit=0.364 |
| S1 | OL8705183W | fam:OL17958323W | martin fierro | 9→9 | form=2 lang=1 deca=5 publ=9 edit=0 | form=0.333 lang=0.889 deca=0.0 publ=0.0 edit=1.0 |
| S1 | OL9290241W | fam:OL9290241W | the 33 strategies of war | 15→15 | form=3 lang=3 deca=4 publ=13 edit=0 | form=0.667 lang=0.267 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL1065659W | fam:OL1065659W | a history of modern philosophy | 2→2 | form=0 lang=2 deca=2 publ=2 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.5 |
| S2 | OL1170995W | fam:OL1170995W | the uprooted | 34→34 | form=1 lang=2 deca=4 publ=16 edit=5 | form=0.971 lang=0.294 deca=0.0 publ=0.029 edit=0.853 |
| S2 | OL1409989W | fam:OL1409989W | memoirs from the war years | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL1454224W | fam:OL1454224W | geschichten und gedichte | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL147482W | fam:OL147482W | catullus and his influence | 7→7 | form=0 lang=1 deca=4 publ=5 edit=0 | form=1.0 lang=0.143 deca=0.143 publ=0.143 edit=1.0 |
| S2 | OL15845230W | fam:OL15845230W | the song of roland | 1→1 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL1704883W | fam:OL1704883W | women in german history | 4→4 | form=0 lang=2 deca=2 publ=2 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.75 |
| S2 | OL19131258W | fam:OL19131258W | songčhao khao phī | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S2 | OL23832779W | fam:OL23832779W | an historical survey of the science of beauty and the literature on the subject | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S2 | OL28035W | fam:OL28035W | banner obrien | 6→6 | form=2 lang=2 deca=3 publ=3 edit=3 | form=0.167 lang=0.0 deca=0.0 publ=0.0 edit=0.5 |
| S2 | OL33075486W | fam:OL33075486W | el do de la vida | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL3393626W | fam:OL3393626W | the bantu composers of southern africa | 2→2 | form=0 lang=2 deca=2 publ=2 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.5 |
| S2 | OL35383W | fam:OL35383W | three lives | 149→60 | form=3 lang=3 deca=13 publ=60 edit=5 | form=0.667 lang=0.2 deca=0.0 publ=0.0 edit=0.917 |
| S2 | OL36641187W | fam:OL36641187W | betriebliche versicherungen als teil des risikomanagementprozesses in unternehmen | 2→2 | form=0 lang=2 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL39304183W | fam:OL39304183W | prehistoric diet transitions | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL39767582W | fam:OL39767582W | gotthold ephraim lessing 1729 1781 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL42717091W | fam:OL42717091W | the book of the twelve minor prophets | 2→2 | form=0 lang=1 deca=2 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.5 |
| S2 | OL4407967W | fam:OL4407967W | check list of parish registers | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL44647836W | fam:OL44647836W | 第二次世界大戦期のインドシナ・タイ そして日本・フランスに関する研究蓄積と一次資料の概観 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL45404882W | fam:OL45404882W | atlas diagramm t︠s︡vet svetimostʹ zvezdnykh skopleniĭ i assot︠s︡iat︠s︡iĭ | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL4594110W | fam:OL4594110W | mühl | 3→3 | form=0 lang=2 deca=1 publ=3 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL4609857W | fam:OL4609857W | turkish english comprehensive dictionary | 3→3 | form=1 lang=1 deca=1 publ=2 edit=0 | form=0.667 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL5711772W | fam:OL20372040W | martin luther king jr | 3→3 | form=2 lang=2 deca=1 publ=2 edit=0 | form=0.333 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL5802801W | fam:OL5802801W | dialogorum sacrorum | 6→6 | form=0 lang=2 deca=5 publ=5 edit=2 | form=1.0 lang=0.167 deca=0.0 publ=0.0 edit=0.667 |
| S2 | OL6016624W | fam:OL6016624W | asp developers guide | 2→2 | form=1 lang=2 deca=2 publ=2 edit=0 | form=0.5 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL625547W | fam:OL625547W | kampf um die macht | 3→3 | form=1 lang=2 deca=2 publ=2 edit=2 | form=0.333 lang=0.333 deca=0.0 publ=0.0 edit=0.333 |
| S2 | OL6699411W | fam:OL6699411W | the stolen seasons | 5→5 | form=0 lang=2 deca=2 publ=2 edit=0 | form=1.0 lang=0.2 deca=0.0 publ=0.2 edit=1.0 |
| S2 | OL7390726W | fam:OL7390726W | the psychology of set | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL7549720W | fam:OL1900223W | an introduction to the new testament | 3→3 | form=0 lang=1 deca=2 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S2 | OL9942119W | fam:OL9942119W | heroes of the equinox | 1→1 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S3 | OL11791404W | fam:OL11791404W | understanding bhs | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL119518W | fam:OL119518W | poetry markets for canadians | 2→2 | form=1 lang=1 deca=1 publ=2 edit=1 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=0.5 |
| S3 | OL11978761W | fam:OL11978761W | practical suggestions as to instruction in farming in canada the united states of america and tasmania | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL1243081W | fam:OL1243081W | yorkshire | 4→4 | form=0 lang=1 deca=4 publ=2 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.25 edit=0.75 |
| S3 | OL15435856W | fam:OL15435856W | legal writing handbook | 7→7 | form=1 lang=1 deca=3 publ=3 edit=2 | form=0.857 lang=0.143 deca=0.0 publ=0.0 edit=0.571 |
| S3 | OL16956827W | fam:OL16956827W | arthroscopic and endoscopic spinal surgery | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL16957978W | fam:OL16957978W | reconciling environment and trade | 2→2 | form=0 lang=1 deca=1 publ=2 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.5 |
| S3 | OL18420328W | fam:OL18420328W | a plain system of elocution or logical and musical reading and declamation | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL18565536W | fam:OL18565536W | the creative curriculum for preschool | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL1912856W | fam:OL18247351W | the american revolution | 1→1 | form=1 lang=1 deca=1 publ=1 edit=1 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL19238502W | fam:OL19238502W | community health nursing | 2→2 | form=1 lang=1 deca=2 publ=2 edit=2 | form=0.5 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL24000458W | fam:OL24000458W | ilhéus | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL24640259W | fam:OL24640259W | retail selling | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL2718912W | fam:OL2718912W | strategic management | 7→7 | form=1 lang=1 deca=1 publ=2 edit=3 | form=0.857 lang=0.0 deca=0.0 publ=0.0 edit=0.286 |
| S3 | OL2749460W | fam:OL2749460W | guide to eastern canada | 7→7 | form=1 lang=1 deca=2 publ=3 edit=4 | form=0.429 lang=0.0 deca=0.0 publ=0.0 edit=0.143 |
| S3 | OL3464537W | fam:OL3464537W | officer candidate tests | 6→6 | form=0 lang=1 deca=3 publ=6 edit=5 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.167 |
| S3 | OL3683146W | fam:OL3683146W | the fifties revisted | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL3908061W | fam:OL3908061W | accounting information systems | 2→2 | form=0 lang=1 deca=1 publ=1 edit=2 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL43290198W | fam:OL43290198W | s s and j l | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL44512709W | fam:OL44512709W | the literary remains of john evelyn | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL46031330W | fam:OL46031330W | código de processo penal | 5→5 | form=0 lang=1 deca=2 publ=1 edit=4 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.2 |
| S3 | OL5261784W | fam:OL5261784W | accounting for inflationand price level changes | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL6324411W | fam:OL6324411W | opportunities in music | 2→2 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.5 |
| S3 | OL6683305W | fam:OL6683305W | an introduction to the logic of marxism | 9→9 | form=1 lang=1 deca=3 publ=3 edit=5 | form=0.889 lang=0.222 deca=0.0 publ=0.0 edit=0.222 |
| S3 | OL7018466W | fam:OL7018466W | third world politics docutech | 1→1 | form=1 lang=1 deca=1 publ=1 edit=1 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL8292734W | fam:OL8292734W | fodors see it mexico | 2→2 | form=1 lang=1 deca=1 publ=2 edit=2 | form=0.5 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL8629087W | fam:OL8629087W | a dictionary of classical antiquities mythology religion literature and art | 13→13 | form=1 lang=1 deca=4 publ=8 edit=8 | form=0.923 lang=0.077 deca=0.0 publ=0.077 edit=0.308 |
| S3 | OL8657034W | fam:OL22145688W | the quran | 1→1 | form=1 lang=0 deca=1 publ=1 edit=1 | form=0.0 lang=1.0 deca=0.0 publ=0.0 edit=0.0 |
| S3 | OL8770934W | fam:OL8770934W | mapstart | 14→14 | form=2 lang=1 deca=2 publ=7 edit=3 | form=0.5 lang=0.5 deca=0.0 publ=0.0 edit=0.714 |
| S3 | OL9299854W | fam:OL9299854W | manual de laboratorio y ejercicios | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S4 | OL10368778W | fam:OL102749W | the count of monte cristo | 3→3 | form=0 lang=1 deca=2 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL20463684W | fam:OL20463684W | a companion to don quixote | 2→2 | form=1 lang=1 deca=2 publ=2 edit=0 | form=0.5 lang=0.5 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL27337290W | fam:OL15165350W | study guide for pride and prejudice | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL27497625W | fam:OL17930368W | summary of atomic habits | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL28071003W | fam:OL15165350W | study guide romeo and juliet | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL28071573W | fam:OL17930368W | workbook for atomic habits | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL28119293W | fam:OL17930368W | summary of atomic habits | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL29070229W | fam:OL102749W | cliffsnotes wuthering heights | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL29284967W | fam:OL102749W | study guide for wuthering heights | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL31326932W | fam:OL22145688W | companion to the quran | 1→1 | form=0 lang=0 deca=0 publ=0 edit=0 | form=1.0 lang=1.0 deca=1.0 publ=1.0 edit=1.0 |
| S4 | OL31777916W | fam:OL102749W | cliffsnotes wuthering heights | 1→1 | form=0 lang=0 deca=0 publ=0 edit=0 | form=1.0 lang=1.0 deca=1.0 publ=1.0 edit=1.0 |
| S4 | OL34257136W | fam:OL17930368W | summary of atomic habits | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL34381078W | fam:OL102749W | great gatsby | 14→14 | form=1 lang=1 deca=3 publ=5 edit=0 | form=0.857 lang=0.286 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL35318673W | fam:OL17930368W | workbook for atomic habits | 1→1 | form=0 lang=0 deca=1 publ=1 edit=0 | form=1.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL35327272W | fam:OL26446888W | a readers guide to odyssey | 1→1 | form=0 lang=0 deca=1 publ=1 edit=0 | form=1.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL36209397W | fam:OL17930368W | workbook for atomic habits | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL36486352W | fam:OL2718912W | strategic management | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL38183338W | fam:OL15165350W | study guide to pride and prejudice | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL39697566W | fam:OL102749W | hobbit | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL39821738W | fam:OL102749W | 1984 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL39987003W | fam:OL102749W | great gatsby | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL40294059W | fam:OL102749W | study guide moby dick | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL40376975W | fam:OL15165350W | summary of pride and prejudice | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL40673754W | fam:OL15165350W | hamlet | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL40792907W | fam:OL102749W | study guide dune | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL41034865W | fam:OL102749W | study guide the count of monte cristo | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL41392812W | fam:OL102749W | study guide 1984 | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL41412596W | fam:OL102749W | study guide the fellowship of the ring | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL41478513W | fam:OL102749W | study guide harry potter and the sorcerers stone | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL41757598W | fam:OL102749W | study guide the picture of dorian gray | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL41847827W | fam:OL102749W | study guide wuthering heights | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL41861898W | fam:OL102749W | study guide the hobbit | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL44607583W | fam:OL15165350W | study guide to romeo and juliet | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL4786872W | fam:OL20463684W | a companion to don quixote | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL6027878W | fam:OL26446888W | cliffsnotes the odyssey | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL6224648W | fam:OL102749W | crime and punishment | 8→8 | form=1 lang=1 deca=4 publ=5 edit=1 | form=0.875 lang=0.0 deca=0.0 publ=0.0 edit=0.875 |
| S4 | OL7796761W | fam:OL102749W | cliffsnotes wuthering heights | 6→6 | form=0 lang=1 deca=2 publ=5 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL8403628W | fam:OL22145688W | companion to the quran | 2→2 | form=1 lang=1 deca=2 publ=2 edit=1 | form=0.5 lang=0.0 deca=0.0 publ=0.0 edit=0.5 |
| S4 | OL8508677W | fam:OL20463684W | don quixote | 3→3 | form=0 lang=1 deca=3 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S4 | OL9251197W | fam:OL102749W | 1984 | 2→2 | form=0 lang=1 deca=1 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL1057047W | fam:OL1057047W | the partha chatterjee omnibus | 2→2 | form=0 lang=1 deca=2 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL15385490W | fam:OL15385490W | gallagher girls 3 book pbk boxed set | 1→1 | form=0 lang=0 deca=1 publ=1 edit=0 | form=1.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL17428656W | fam:OL17428656W | the pellucidar sf gateway omnibus | 1→1 | form=0 lang=0 deca=1 publ=1 edit=0 | form=1.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL21837559W | fam:OL21837559W | harlequin love inspired suspense december 2017 box set 2 of 2 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL21870421W | fam:OL21870421W | harlequin historical january 2020 box set 2 of 2 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL21890318W | fam:OL21890318W | harlequin romantic suspense august 2020 box set | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL27969614W | fam:OL27969614W | moving in series | 1→1 | form=1 lang=0 deca=1 publ=1 edit=0 | form=0.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL29203923W | fam:OL29203923W | guesthouse on the green series books 1 2 and 3 with bonus content | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL30182057W | fam:OL30182057W | sudoku jigsaw puzzle books 400 easy to master puzzles 8x8 volume 2 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL30370304W | fam:OL30182057W | suguru puzzle books 400 easy to master puzzles 12x12 volume 8 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL32411639W | fam:OL32411639W | modern collection january 2020 books 5 8 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL38015694W | fam:OL38015694W | faraway paladin manga omnibus 5 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL40685100W | fam:OL40685100W | blood skies omnibus vol 1 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL45342062W | fam:OL45342062W | the chronicles of narnia 7 books collection box set | 1→1 | form=0 lang=0 deca=1 publ=1 edit=0 | form=1.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S5 | OL7920808W | fam:OL7920808W | the complete bloody history of britain omnibus | 1→1 | form=1 lang=0 deca=1 publ=1 edit=0 | form=0.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL13224155W | fam:OL1243081W | yorkshire | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL17504079W | fam:OL17504079W | frankenstein | 3→3 | form=1 lang=1 deca=2 publ=2 edit=1 | form=0.333 lang=0.0 deca=0.0 publ=0.0 edit=0.667 |
| S6 | OL17728718W | fam:OL17728718W | beloved | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S6 | OL17737918W | fam:OL15165350W | pride and prejudice | 1→1 | form=1 lang=1 deca=1 publ=1 edit=1 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S6 | OL17958323W | fam:OL17958323W | martín fierro | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL18247351W | fam:OL18247351W | the american revolution | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL1900223W | fam:OL1900223W | an introduction to the new testament | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL20372040W | fam:OL20372040W | martin luther king jr | 1→1 | form=1 lang=0 deca=1 publ=1 edit=0 | form=0.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL21334761W | fam:OL1170995W | uprooted | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL21606826W | fam:OL17728718W | beloved | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL22145688W | fam:OL22145688W | the qurân | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL22212140W | fam:OL1900223W | an introduction to the new testament | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL25731799W | fam:OL1063588W | miserables | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL26322301W | fam:OL20463684W | don quixote | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL27266977W | fam:OL15574537W | road | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL28168849W | fam:OL28168849W | frida | 1→1 | form=0 lang=0 deca=1 publ=1 edit=0 | form=1.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL30124541W | fam:OL15165350W | romeo and juliet | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL31640402W | fam:OL102749W | the hobbit | 1→1 | form=0 lang=0 deca=1 publ=1 edit=0 | form=1.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL33967231W | fam:OL1063588W | les miserables | 1→1 | form=0 lang=0 deca=1 publ=1 edit=0 | form=1.0 lang=1.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL34414763W | fam:OL1063588W | miserables | 2→2 | form=0 lang=2 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL34481537W | fam:OL16261015W | game of thrones | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL34628880W | fam:OL274505W | cien anos de soledad | 1→1 | form=0 lang=0 deca=0 publ=0 edit=0 | form=1.0 lang=1.0 deca=1.0 publ=1.0 edit=1.0 |
| S6 | OL40607040W | fam:OL10263W | little prince | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL40609987W | fam:OL15165350W | romeo and juliet | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL40870684W | fam:OL102749W | moby dick | 4→4 | form=0 lang=1 deca=2 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL41521450W | fam:OL22145688W | quran | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL41534707W | fam:OL15165350W | complete works of william shakespeare | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL43110094W | fam:OL20463684W | don quixote | 2→2 | form=0 lang=1 deca=2 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL43259285W | fam:OL102749W | moby dick | 2→2 | form=0 lang=2 deca=2 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL43892241W | fam:OL102749W | the picture of dorian gray | 4→4 | form=0 lang=1 deca=3 publ=2 edit=0 | form=1.0 lang=0.5 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL4440317W | fam:OL15165350W | hamlet | 2→2 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.5 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL4615157W | fam:OL35383W | three lives | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL625573W | fam:OL625547W | kampf um die macht | 5→5 | form=0 lang=1 deca=2 publ=4 edit=3 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.4 |
| S6 | OL7106216W | fam:OL17845943W | catcher in the rye | 3→3 | form=0 lang=1 deca=3 publ=3 edit=1 | form=1.0 lang=0.333 deca=0.0 publ=0.0 edit=0.667 |
| S6 | OL7214853W | fam:OL20372040W | martin luther king jr | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL8226332W | fam:OL12977329W | to kill a mockingbird | 2→2 | form=0 lang=1 deca=2 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL8390488W | fam:OL14930024W | dracula | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL8915961W | fam:OL1243081W | yorkshire | 2→2 | form=1 lang=1 deca=1 publ=2 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL9253955W | fam:OL1065659W | history of modern philosophy | 2→2 | form=2 lang=1 deca=2 publ=2 edit=0 | form=0.0 lang=0.5 deca=0.0 publ=0.0 edit=1.0 |
| S6 | OL9793266W | fam:OL14949682W | deliver us from evil | 2→2 | form=1 lang=1 deca=2 publ=2 edit=0 | form=0.5 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL11777177W | fam:OL11777177W | bedtime for baby | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL12327757W | fam:OL12327757W | beauty flash | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL16949809W | fam:OL16949809W | human rights and scots law | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL17893950W | fam:OL17893950W | what to do when you cant decide | 4→4 | form=0 lang=1 deca=1 publ=4 edit=0 | form=1.0 lang=0.25 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL17999580W | fam:OL17999580W | bernard of clairvaux | 1→1 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL18231043W | fam:OL18231043W | democratizing democracy | 2→2 | form=0 lang=2 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.5 publ=0.0 edit=1.0 |
| S7 | OL19050532W | fam:OL19050532W | high power lasers | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL20427347W | fam:OL20427347W | darkwoods | 2→2 | form=1 lang=1 deca=1 publ=2 edit=0 | form=0.5 lang=0.5 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL21170273W | fam:OL21170273W | the adventure of living | 3→3 | form=0 lang=1 deca=2 publ=3 edit=1 | form=1.0 lang=0.333 deca=0.0 publ=0.0 edit=0.667 |
| S7 | OL21656217W | fam:OL21656217W | adventures on the china wine trail | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL24396680W | fam:OL24396680W | to spark a fae war | 3→3 | form=2 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.333 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL2461199W | fam:OL2461199W | norway | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S7 | OL25435171W | fam:OL25435171W | adult coloring book for men 2 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL25883444W | fam:OL25883444W | handwriting practice workbook for kids | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL27360665W | fam:OL27360665W | caxley chronicles | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL27600034W | fam:OL27600034W | grade 1 now its hot | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL27854666W | fam:OL27854666W | 1932 census of the standing rock sioux reservation | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL28022273W | fam:OL28022273W | opportunity index | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL28362224W | fam:OL28362224W | pulling dogs | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL28370794W | fam:OL28370794W | on the orient | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL28435023W | fam:OL28435023W | 2022 smart city symposium prague scsp | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL28559109W | fam:OL28559109W | basia joannis secundi nicolai hagensis | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL28868440W | fam:OL28868440W | night owl | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL30164275W | fam:OL30164275W | my name is yehuda | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL30177930W | fam:OL30177930W | keto bread | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL30322473W | fam:OL30322473W | eggtraordinary eggventures of eggville the kings dinner guest | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL30406494W | fam:OL30406494W | gwen | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL30425489W | fam:OL30425489W | best love is the one that makes you a better person without changing you into someone other than yourself | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL30577577W | fam:OL30577577W | coloring book | 7→7 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL30631747W | fam:OL30631747W | fun trace time activity workbook for little princess | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL3313936W | fam:OL3313936W | the 2007 2012 outlook for playground equipment in the united states | 1→1 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL3320726W | fam:OL3313936W | the 2007 2012 world outlook for commercial deep fat fryers excluding electric | 1→1 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL34076033W | fam:OL34076033W | preceptor | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL34471609W | fam:OL34471609W | office organizer im a math teacher of course i have problems teacher | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL3509560W | fam:OL3509560W | argentinas lost patrol | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL36045432W | fam:OL36045432W | palliative care in hematologic malignancies and serious blood disorders | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL3682417W | fam:OL3682417W | investing in all the people | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL36828238W | fam:OL36828238W | life is like a beautiful painting | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL37585725W | fam:OL37585725W | iberian apollonius of tyre | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL38102820W | fam:OL38102820W | poetry of heart | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL38140975W | fam:OL38140975W | cmajournal issue two territory | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL38376505W | fam:OL38376505W | nowhere to call home | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL3973285W | fam:OL3973285W | hypnosis complications | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL39785228W | fam:OL39785228W | shaped in iniquity conceived in sin | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL40270390W | fam:OL40270390W | food gift recipes from natures bounty | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL4095317W | fam:OL4095317W | intercultural encounters | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL41414243W | fam:OL41414243W | 150 tips and tricks for the kindle fire and kindle fire hd | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL41780751W | fam:OL41780751W | young brainpower volume 7 | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL42456940W | fam:OL42456940W | double edged reckoning | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL42543497W | fam:OL42543497W | 1000 platforms | 2→2 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL45609205W | fam:OL45609205W | pathology and imaging of muscles and tendons musculoskeletal ultrasound | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL4632631W | fam:OL4632631W | patterns of abuse | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL4732910W | fam:OL4732910W | wills for ontario | 6→6 | form=0 lang=1 deca=2 publ=2 edit=6 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |
| S7 | OL5286296W | fam:OL5286296W | cross stitch patterns | 3→3 | form=1 lang=1 deca=2 publ=3 edit=0 | form=0.667 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL5373171W | fam:OL5373171W | games and lore of young americans | 1→1 | form=0 lang=1 deca=1 publ=1 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL6215526W | fam:OL6215526W | stray | 6→6 | form=3 lang=1 deca=1 publ=5 edit=0 | form=0.333 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL8105115W | fam:OL8105115W | fixing the family | 3→3 | form=0 lang=1 deca=1 publ=2 edit=0 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL8576726W | fam:OL8576726W | technology applications in prevention journal of prevention intervention in the community monographic journal of prevention intervention in the community monographic | 1→1 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL8746552W | fam:OL8746552W | michigan copper country | 1→1 | form=1 lang=1 deca=1 publ=1 edit=0 | form=0.0 lang=0.0 deca=0.0 publ=0.0 edit=1.0 |
| S7 | OL8953570W | fam:OL8953570W | night sky star wheel | 1→1 | form=0 lang=1 deca=1 publ=1 edit=1 | form=1.0 lang=0.0 deca=0.0 publ=0.0 edit=0.0 |

## Exclusions

By rule: {'R2_title': 314, 'R1_author_key': 2166, 'R3_translation_of': 4}

| work | rule | title | editions |
|---|---|---|---|
| OL10000026W | R2_title | study the remains of the day de k ishiguro | 1 |
| OL10215W | R1_author_key | we | 210 |
| OL10273150W | R1_author_key | the mill on the floss | 1 |
| OL10371323W | R2_title | the quest for self in zora neale hurstons their eyes were watching god toni morrisons sula and gayl jones corregidora | 1 |
| OL10374276W | R2_title | their eyes were watching god | 2 |
| OL10632203W | R1_author_key | the man of the mountain | 1 |
| OL11112688W | R1_author_key | polk county | 4 |
| OL11350669W | R1_author_key | the atheist ansvvered and his errour confuted by george elliot author of gods warning piece to london each spire of grass and every silly flie bias us take heed how we a god deny this whole creation with a sweet conseat proclaim a being thats omnipotent | 1 |
| OL11350670W | R1_author_key | londons lamentation or godly sorrow and submission by george elliott author of gods warning piece to london | 1 |
| OL11639738W | R2_title | middlemarch george eliot video bbc | 1 |
| OL11704429W | R2_title | the remains of the day | 1 |
| OL11833911W | R2_title | middlemarch from notebook to novel | 4 |
| OL11837483W | R1_author_key | adam bede silas marner | 1 |
| OL11837485W | R1_author_key | impressions of theophrastus such miscellaneous essays | 1 |
| OL11837487W | R1_author_key | the mill on the floss scenes of clerical life | 1 |
| OL11837488W | R1_author_key | miscellaneous essays impressions of theophrastus such the veil lifted brother jacob | 2 |
| OL11837489W | R1_author_key | poems essays and leaves from a note book | 2 |
| OL11837490W | R1_author_key | romola theophrastus such | 1 |
| OL11837493W | R1_author_key | george eliots works | 1 |
| OL11984327W | R1_author_key | the turning | 1 |
| OL12348882W | R1_author_key | jierfei xian sheng di qing shi | 1 |
| OL12607366W | R2_title | individual and society a study of george eliots adam bede the mill on the floss and middlemarch | 1 |
| OL13045098W | R2_title | structure and motif in middlemarch | 1 |
| OL13090948W | R1_author_key | the legend of jubal and other poems and other poems | 1 |
| OL13090949W | R1_author_key | o may i join the choir invisible and other favorite poems | 1 |
| OL13090950W | R1_author_key | poems | 12 |
| OL13090951W | R1_author_key | poems together with brother jacob and the lifted veil | 2 |
| OL13090957W | R1_author_key | wise witty and tender sayings in prose and verse selected from the works of george eliot | 1 |
| OL13171583W | R1_author_key | the essence of christianity | 7 |
| OL13193958W | R2_title | middlemarch george eliot | 1 |
| OL13549024W | R2_title | middlemarch subspecies spinoza | 1 |
| OL1360720W | R2_title | middlemarch george eliot | 4 |
| OL13683810W | R1_author_key | last night in montreal | 6 |
| OL14873187W | R1_author_key | the best short stories by black writers 1899 1967 | 1 |
| OL14875858W | R1_author_key | conversations with kazuo ishiguro | 1 |
| OL14875862W | R1_author_key | early japanese stories | 1 |
| OL14875876W | R1_author_key | remains of the day | 1 |
| OL14875878W | R1_author_key | the review of contemporary fiction 25 1 | 1 |
| OL14875879W | R1_author_key | threebies kazuo ishiguro | 1 |
| OL14875886W | R1_author_key | nocturnes | 34 |
| OL14911102W | R1_author_key | selected essays poems and other writings penguin classics | 3 |
| OL14912498W | R1_author_key | beginnings birth rebirth and the new world five fingers review 17 | 1 |
| OL14914261W | R1_author_key | isaac asimovs space of her own | 1 |
| OL14924207W | R1_author_key | galaxy magazine august 1974 volume 35 no 4 | 1 |
| OL14929068W | R1_author_key | tolkiens erbe | 1 |
| OL14929069W | R1_author_key | tolkiens zauber | 1 |
| OL14942550W | R2_title | their eyes were watching god | 1 |
| OL14942634W | R2_title | zora neale hurstons their eyes were watching god | 1 |
| OL14942704W | R1_author_key | spark notes silas marner | 1 |
| OL14942723W | R1_author_key | spark notes their eyes were watching god | 1 |
| OL14943414W | R1_author_key | george eliots silas marner the weaver of raveloe | 2 |
| OL14944748W | R1_author_key | obwl4 silas marner level 4 | 1 |
| OL14949413W | R1_author_key | through other eyes | 1 |
| OL14958258W | R1_author_key | the magazine of fantasy and science fiction june 2000 volume 98 no 6 | 1 |
| OL14963788W | R1_author_key | gemelas del sueño | 1 |
| OL14963794W | R1_author_key | the twins the dream las gemelas el sueno | 1 |
| OL14982262W | R1_author_key | silas marner bookworm ser | 1 |
| OL14987908W | R1_author_key | romola | 1 |
| OL14988395W | R1_author_key | lao tzu tao te ching | 5 |
| OL15000280W | R1_author_key | women | 1 |
| OL15001013W | R1_author_key | the soul of a woman black classics | 1 |
| OL15056518W | R1_author_key | the adventure of cobblers rune | 2 |
| OL15056519W | R1_author_key | alejandro el espléndido y los alagatos | 1 |
| OL15056520W | R1_author_key | the altered i | 3 |
| OL15056524W | R1_author_key | the blind geometer the new atlantis tor double novel no 13 | 1 |
| OL15056525W | R1_author_key | blue moon over thurman street | 1 |
| OL15056527W | R1_author_key | buffalo gals 1st edition | 2 |
| OL15056529W | R1_author_key | cat dreams | 1 |
| OL15056541W | R1_author_key | dialogues with northwest writers northwest review book | 1 |
| OL15056542W | R1_author_key | direction of the road | 2 |
| OL15056545W | R1_author_key | earthsea revisioned | 1 |
| OL15056552W | R1_author_key | fire and stone | 1 |
| OL15056553W | R1_author_key | balik corbasi | 2 |
| OL15056554W | R1_author_key | five complete novels | 1 |
| OL15056556W | R1_author_key | from elfland to poughkeepsie | 1 |
| OL15056558W | R1_author_key | going out with peacocks and other poems | 2 |
| OL15056559W | R1_author_key | gwilans harp | 1 |
| OL15056560W | R1_author_key | gwilans harp and intracom swc 1556 | 2 |
| OL15056561W | R1_author_key | hard words and other poems | 1 |
| OL15056562W | R1_author_key | historias de terramar ii la costa más lejana tehanu | 2 |
| OL15056565W | R1_author_key | historias de terramar i | 3 |
| OL15056567W | R1_author_key | in the red zone | 1 |
| OL15056577W | R1_author_key | a lesson plan book for catwings innovations experiencing literature in the classroom | 1 |
| OL15056578W | R1_author_key | tehanu | 30 |
| OL15056580W | R1_author_key | more tales of the catwings | 1 |
| OL15056583W | R1_author_key | the norton book of science fiction | 5 |
| OL15056584W | R1_author_key | quienes se alejan de omelas | 8 |
| OL15056590W | R1_author_key | powers | 12 |
| OL15056594W | R1_author_key | рыбак из внутриморья | 1 |
| OL15056596W | R1_author_key | the shobies story | 1 |
| OL15056598W | R1_author_key | tales of the catwings | 2 |
| OL15056607W | R1_author_key | ursula k le guin | 1 |
| OL15056610W | R1_author_key | a very long way from anywhere else | 7 |
| OL15056612W | R1_author_key | the visionary | 1 |
| OL15056613W | R1_author_key | the visionary wonders hidden | 1 |
| OL15056614W | R1_author_key | voices | 14 |
| OL15056616W | R1_author_key | the water is wide | 1 |
| OL15056617W | R1_author_key | the wave in the mind | 5 |
| OL15056618W | R1_author_key | wild angels | 1 |
| OL15056622W | R1_author_key | a woman writing or the fisherwomans daughter | 1 |
| OL15056627W | R1_author_key | wynn bullock | 1 |
| OL15056630W | R1_author_key | walking in cornwall | 3 |
| OL15059831W | R1_author_key | the singers gun | 8 |
| OL15210342W | R1_author_key | adam bede film tv tie in series | 1 |
| OL15210344W | R1_author_key | adam bede and other works | 1 |
| OL15210348W | R1_author_key | adam bede and scenes of clerical life | 1 |
| OL15210350W | R1_author_key | adam bede tales retold s | 1 |
| OL15210351W | R1_author_key | among the dangs | 1 |
| OL15210352W | R1_author_key | amos barton hesperus classics | 1 |
| OL15210353W | R1_author_key | brother jacob the lifted veil | 1 |
| OL15210354W | R1_author_key | clarendon edition of the novels of george eliot | 1 |
| OL15210355W | R1_author_key | clerical life and sentimental behaviour | 1 |
| OL15210356W | R1_author_key | cliffsnotes middlemarch | 1 |
| OL15210357W | R1_author_key | collected poems skoob seriph | 1 |
| OL15210358W | R1_author_key | the complete poems of george eliot | 1 |
| OL15210359W | R1_author_key | complete poems with introduction notice by matthew browne 84 | 1 |
| OL15210360W | R1_author_key | complete poetical works | 1 |
| OL15210361W | R1_author_key | the complete shorter poetry of george eliot pickering masters | 1 |
| OL15210367W | R1_author_key | daniel deronda | 1 |
| OL15210370W | R1_author_key | die mühle am floss | 1 |
| OL15210371W | R1_author_key | edward neville | 1 |
| OL15210372W | R1_author_key | eliots middlemarch | 1 |
| OL15210373W | R1_author_key | el molino del floss the mill on the floss clasicos classics | 1 |
| OL15210375W | R1_author_key | essays complete | 1 |
| OL15210376W | R1_author_key | the essays complete collected and arranged with an introd on her analysis of motives by nathan sheppard | 1 |
| OL15210378W | R1_author_key | essays and uncollected papers | 1 |
| OL15210379W | R1_author_key | essays and uncollected papers | 1 |
| OL15210380W | R1_author_key | ethics of benedict spinoza translated by george eliot salzburg studies in romantic reassessment | 1 |
| OL15210381W | R1_author_key | felix holt impressions of theophrastus such | 1 |
| OL15210382W | R1_author_key | felix holt jubal and other poems and the spanish gypsy | 2 |
| OL15210389W | R1_author_key | four novels of george eliot | 1 |
| OL15210390W | R1_author_key | the george eliot birthday book | 1 |
| OL15210391W | R1_author_key | george eliot collected poems | 1 |
| OL15210392W | R1_author_key | george eliot day by day | 1 |
| OL15210393W | R1_author_key | the george eliot letters in seven volumes | 1 |
| OL15210394W | R1_author_key | george eliot on cd rom | 1 |
| OL15210395W | R1_author_key | the george eliot portfolio | 1 |
| OL15210396W | R1_author_key | george eliots complete works | 1 |
| OL15210397W | R1_author_key | george eliots complete works illustrated | 1 |
| OL15210398W | R1_author_key | george eliots daniel deronda notebooks | 1 |
| OL15210399W | R1_author_key | george eliot selected works | 1 |
| OL15210400W | R1_author_key | george eliots life as related in her letters and journals set | 1 |
| OL15210401W | R1_author_key | george eliots life part 1 | 1 |
| OL15210402W | R1_author_key | george eliots life part 2 | 1 |
| OL15210403W | R1_author_key | george eliots life part 3 | 1 |
| OL15210404W | R1_author_key | george eliots middlemarch notebooks | 1 |
| OL15210405W | R1_author_key | george eliots mill on the floss | 1 |
| OL15210406W | R1_author_key | george eliots silas marner and middlemarch | 1 |
| OL15210407W | R1_author_key | george eliot the critical heritage the collected critical heritage 19th century novelists | 1 |
| OL15210408W | R1_author_key | great novels of george eliot the golden library | 1 |
| OL15210409W | R1_author_key | if russia strikes | 1 |
| OL15210410W | R1_author_key | impression of theophrastus such | 1 |
| OL15210413W | R1_author_key | in the world | 1 |
| OL15210414W | R1_author_key | the journals of george eliot | 1 |
| OL15210415W | R1_author_key | the legend of jaibal and other poems old and new | 1 |
| OL15210416W | R1_author_key | letters from george eliot to elma stuart | 1 |
| OL15210417W | R1_author_key | letters to elma stuart 1872 1880 | 1 |
| OL15210418W | R1_author_key | the life of jesus | 1 |
| OL15210419W | R1_author_key | lifted veil and brother jacob | 1 |
| OL15210420W | R1_author_key | the lifted veil and castle rackrent classic books on cassettes collection | 1 |
| OL15210421W | R1_author_key | the lifted veil classic 60s | 1 |
| OL15210422W | R1_author_key | middlemarch a study of provincial life part 1 | 1 |
| OL15210423W | R1_author_key | middlemarch a study of provincial life part 2 | 1 |
| OL15210424W | R1_author_key | middlemarch a study of provincial life part 3 | 1 |
| OL15210427W | R1_author_key | middlemarch by g eliot | 1 |
| OL15210428W | R1_author_key | middlemarch by george eliot | 1 |
| OL15210429W | R1_author_key | middlemarch | 1 |
| OL15210430W | R1_author_key | middlemarch classic literature with classical music | 1 |
| OL15210432W | R1_author_key | middlemarch eine studie über das leben in der provinz | 1 |
| OL15210433W | R1_author_key | middlemarch eine studie des provinzlebens | 1 |
| OL15210435W | R1_author_key | a middlemarch miscellany | 1 |
| OL15210437W | R1_author_key | middlemarch part 1 | 1 |
| OL15210438W | R1_author_key | middlemarch part i dodo press | 1 |
| OL15210439W | R1_author_key | middlemarch part ii dodo press | 1 |
| OL15210440W | R1_author_key | middlemarch | 1 |
| OL15210441W | R1_author_key | middlemarch | 1 |
| OL15210442W | R1_author_key | middlemarch silas marner amos barton | 1 |
| OL15210443W | R2_title | middlemarch silas marner amos barton great classic library | 1 |
| OL15210444W | R1_author_key | the mill on he floss | 1 |
| OL15210447W | R1_author_key | the mill on the floss cambridge literature | 1 |
| OL15210448W | R1_author_key | the mill on the floss | 1 |
| OL15210454W | R1_author_key | mill on the floss gift | 1 |
| OL15210457W | R1_author_key | the mill on the floss | 1 |
| OL15210458W | R1_author_key | mill on the floss | 1 |
| OL15210460W | R1_author_key | mill on the floss | 1 |
| OL15210464W | R1_author_key | the mill on the floss and silas marner | 1 |
| OL15210469W | R1_author_key | the night school and the schoolmaster toms first half | 1 |
| OL15210470W | R1_author_key | notes on george eliots the mill on the floss | 1 |
| OL15210471W | R1_author_key | o may i join the choir invisible and other favourite poems illustrated edition dodo press | 1 |
| OL15210472W | R1_author_key | oxford reading tree stage 16b treetops classics | 1 |
| OL15210473W | R1_author_key | oxford reading tree stage 16 treetops classics | 1 |
| OL15210474W | R1_author_key | the personal edition of george eliots works | 1 |
| OL15210475W | R1_author_key | poems | 1 |
| OL15210476W | R1_author_key | the popular short tales of george eliot | 1 |
| OL15210478W | R1_author_key | romola part 1 | 1 |
| OL15210479W | R1_author_key | romola part 2 | 1 |
| OL15210480W | R1_author_key | romola with an introd by rudolf dircks | 1 |
| OL15210481W | R1_author_key | the sad fortunes of revd amos barton | 1 |
| OL15210482W | R1_author_key | sad fortunes of the reverend amos barton the large print | 1 |
| OL15210486W | R1_author_key | scenes of clerical life life of george eliot | 1 |
| OL15210489W | R1_author_key | scenes of clerical life and silas marner | 1 |
| OL15210490W | R1_author_key | silar marner | 1 |
| OL15210492W | R1_author_key | silas manor | 1 |
| OL15210497W | R1_author_key | george eliots silas marner | 1 |
| OL15210498W | R1_author_key | silas marner and brother jacob | 1 |
| OL15210499W | R1_author_key | silas marner brother jacob | 1 |
| OL15210520W | R1_author_key | silas marner the lifted veil brother jacob clerical life | 1 |
| OL15210521W | R1_author_key | silas marner the lifted veil brother jacob and scenes of clerical life | 1 |
| OL15210526W | R1_author_key | silas marner and two short stories barnes noble classics series barnes noble classics | 1 |
| OL15210528W | R1_author_key | the spanish gipsy | 1 |
| OL15210531W | R1_author_key | the spanish gypsy pickering masters | 1 |
| OL15210533W | R1_author_key | spanish gypsy the | 1 |
| OL15210534W | R1_author_key | stories from george eliot | 1 |
| OL15210536W | R1_author_key | the story of little tom and maggie from the mill on the floss of george eliot | 1 |
| OL15210537W | R1_author_key | theophrastus such | 1 |
| OL15210538W | R1_author_key | two lovers | 1 |
| OL15210539W | R1_author_key | velo alzado el | 1 |
| OL15210540W | R1_author_key | a view of middlemarch | 1 |
| OL15210542W | R1_author_key | vodenica na flosi | 1 |
| OL15210543W | R1_author_key | the wisdom of george eliot | 1 |
| OL15210548W | R1_author_key | a writers notebook 1854 1879 and uncollected writings | 1 |
| OL15210549W | R1_author_key | writings 25 volumes | 1 |
| OL15210550W | R1_author_key | writings of george eliot 25 volume set | 1 |
| OL15210551W | R1_author_key | the writings of george eliot 25 volumes the writings of george eliot | 1 |
| OL15210552W | R1_author_key | york notes advanced | 1 |
| OL15210554W | R1_author_key | zhi gong manan zhuan | 1 |
| OL15210555W | R1_author_key | headwork classics | 2 |
| OL15210558W | R1_author_key | letters | 2 |
| OL15210560W | R1_author_key | the sad fortunes of the reverend amos barton | 2 |
| OL15210561W | R1_author_key | selected critical writings | 2 |
| OL15210562W | R1_author_key | selections from george eliots letters | 2 |
| OL15210564W | R1_author_key | some george eliot notebooks | 2 |
| OL15210569W | R1_author_key | complete poems | 6 |
| OL15210570W | R1_author_key | essays | 7 |
| OL15210574W | R1_author_key | the george eliot letters | 27 |
| OL1525083W | R2_title | never let me go | 1 |
| OL15321203W | R3_translation_of | der pragmatische programmierer | 2 |
| OL15321223W | R1_author_key | programming ruby | 2 |
| OL15330629W | R3_translation_of | ozherelʹe planet ėkumeny | 2 |
| OL15338527W | R1_author_key | ambigrammi | 1 |
| OL15391967W | R1_author_key | bottle up and go | 1 |
| OL15391968W | R1_author_key | the prize plays and other one acts published in periodicals african american women writers 1910 1940 | 2 |
| OL15401121W | R1_author_key | ursula k le guins the phoenix gish jens the water faucet vision | 1 |
| OL15401242W | R1_author_key | orbit 12 | 7 |
| OL15429904W | R1_author_key | the mill on the floss george eliot | 1 |
| OL15449125W | R1_author_key | bookmarks in the pages of life | 1 |
| OL15460545W | R1_author_key | adam bede a play dramatized from george eliots novel adam bede | 1 |
| OL15460556W | R1_author_key | the life of jesus critically examined | 1 |
| OL15678246W | R1_author_key | the adventures of the princess and mr whiffle | 4 |
| OL15746505W | R1_author_key | how lisa loved the king | 1 |
| OL15757476W | R1_author_key | the writings of george eliot | 2 |
| OL15758472W | R1_author_key | el velo descubierto | 1 |
| OL15815184W | R1_author_key | the complete poetical works of george eliot | 1 |
| OL15819926W | R1_author_key | how lisa loved the king | 1 |
| OL15822732W | R1_author_key | how lisa loved the king | 1 |
| OL15822827W | R1_author_key | the spanish gypsy | 1 |
| OL15822897W | R1_author_key | the spanish gypsy | 1 |
| OL15851240W | R1_author_key | the complete poetical works of george eliot | 1 |
| OL15855820W | R1_author_key | lavinia | 22 |
| OL15856643W | R1_author_key | scenes of clerical life | 65 |
| OL15867466W | R1_author_key | chronicle of the year 1992 | 2 |
| OL15897314W | R1_author_key | pragmatic thinking and learning | 1 |
| OL15910065W | R1_author_key | the complete poetical works of george eliot | 1 |
| OL15913134W | R1_author_key | how lisa loved the king | 1 |
| OL15987177W | R2_title | their eyes were watching god | 1 |
| OL16042612W | R1_author_key | interfaces | 2 |
| OL16052687W | R1_author_key | moral swindlers | 1 |
| OL16065936W | R1_author_key | great novels of george eliot | 1 |
| OL16171657W | R2_title | never let me go | 2 |
| OL16204347W | R1_author_key | romola | 1 |
| OL16239866W | R1_author_key | the lola quartet | 8 |
| OL16419954W | R1_author_key | among others | 32 |
| OL16471402W | R2_title | womens issues in zora neale hurstons their eyes were watching god social issues in literature | 3 |
| OL16618501W | R1_author_key | finding my elegy | 2 |
| OL16712981W | R1_author_key | out here | 1 |
| OL16747643W | R1_author_key | essays complete | 1 |
| OL16781091W | R1_author_key | silas marner abridged for use in public and high schools by george eliot with annotations by o j stevenson | 1 |
| OL16781092W | R1_author_key | silas marner by george eliot edited with notes and an introduction by edward l gulick | 1 |
| OL16802834W | R2_title | middle march | 1 |
| OL16817144W | R1_author_key | die furcht des weisen | 5 |
| OL16817145W | R1_author_key | die furcht des weisen | 5 |
| OL16826159W | R1_author_key | the spanish gypsy | 1 |
| OL16835663W | R2_title | ursula k le guins a wizard of earthsea | 1 |
| OL16835781W | R1_author_key | impressions of theophrastus such | 1 |
| OL16850097W | R1_author_key | middlemarch vol 1 | 1 |
| OL16871698W | R1_author_key | romola | 1 |
| OL16872662W | R1_author_key | impressions of theophrastus such | 1 |
| OL16882630W | R1_author_key | the mill on the floss | 1 |
| OL16911791W | R1_author_key | silas marner scenes of clerical life | 1 |
| OL16925488W | R1_author_key | pragmatic unit testing in java with junit | 1 |
| OL16964006W | R1_author_key | the mill on the floss | 1 |
| OL16980232W | R1_author_key | the new utopian politics of ursula k le guins the dispossessed | 3 |
| OL17009310W | R1_author_key | life as related in her letters and journals | 1 |
| OL17067388W | R1_author_key | la música del silencio | 23 |
| OL17076856W | R1_author_key | the life and works of george eliot | 1 |
| OL17085292W | R1_author_key | impressions of theophrastus such | 1 |
| OL17199439W | R1_author_key | practices of an agile developer | 1 |
| OL17202418W | R1_author_key | station eleven | 18 |
| OL17315629W | R1_author_key | witches | 2 |
| OL17330724W | R1_author_key | the poems of george eliot | 1 |
| … | | 2184 more in the JSON | |
