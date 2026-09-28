# The Unofficial Guide

**K-Sqr** · corpus: `campus_life`

---

# Unit 1

## What This Does

This is a question-answering system over `campus_life`, 88 short posts by
students about life at one university: dining halls, dorms, courses, and the
administrative rules nobody explains properly. It answers specific, factual
questions whose answer sits in one or two sentences of a post. Examples: "How
long is the lunch wait at Kestrel Commons?", "How late can I declare pass/fail?",
"How much is laundry in Aldridge Hall?", "When does the library close during
reading week?" Every answer names the file it came from. If nothing in the
corpus is close enough to the question, the system replies "I don't have enough
information about that" and doesn't guess.

## Chunking Strategy

**Chunk size:** one paragraph per chunk, with the post's title line in front
of it. Paragraphs are capped at 400 characters and split at sentence ends if
longer. The longest paragraph in campus_life is 373, so the cap never fires on
this corpus. That produces 183 chunks, averaging 167 characters (shortest 63,
longest 397).
**Overlap:** 0 characters. The only thing neighbouring chunks share is the
title line, which is repeated in front of every chunk from the same post.

**What in the documents made me pick this.** The starter's 800-character
windows made 88 chunks from 88 documents. No campus_life post is longer than
563 characters, so `fallback_split` never cut anything, and each whole post
became one chunk. When I read the posts, though, most of them are a title line
followed by 2–4 short paragraphs, each on a different topic:

- `dining_kestrel_commons.txt` has wait times and the stir-fry station in the
  first paragraph, then hours and cost ("Costs one meal swipe, or $12.50 cash")
  in the second.
- The housing posts are split into "The good:", "The bad:", and then laundry
  and noise, each its own paragraph.

With one chunk per post, a question about Kestrel's hours was matched against a
chunk that was mostly about queues. Splitting on the blank line keeps each
topic whole, and no sentence is ever cut in half.

Splitting had one cost. A second paragraph such as "Hours are 7:00am to 9:00pm
weekdays..." never says which dining hall it's about; only the title does. So
instead of a character overlap, which would just bring in the end of the
wait-times paragraph, every chunk starts with its post's title. That's also why
I didn't merge the short paragraphs. The shortest body paragraph is 36
characters ("Expect 4 hours a week outside class." in
`course_econ_101.txt`), but with "ECON 101 …" in front of it, it answers a
workload question on its own.

**Changed my mind:** I first planned to merge any paragraph under ~120
characters into its neighbour, because 120 is close to the median paragraph
length (112). But the short paragraphs turned out to be the most answerable
ones: one fact, once the title is in front. Merging them would have put the
two-topics-in-one-chunk problem back.

## Sample Chunks

From `python app.py chunks -n 5` (183 chunks total, sampled across the corpus).

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** — source: `course_cs_340_exams.txt#1` — produced by: `chunker.py::split_documents`

```
CS 340 Databases — assessment

Start the term project in week three, not week eight; everyone learns this the hard way.
```

**Chunk 3** — source: `course_phys_130_workload.txt#0` — produced by: `chunker.py::split_documents`

```
Workload for PHYS 130 Mechanics

People keep asking so: 7 hours a week, plus 3 on lab weeks. That's real time, not optimistic time.
```

**Chunk 4** — source: `dining_verrill_street_grill_followup.txt#1` — produced by: `chunker.py::split_documents`

```
Re: Verrill Street Grill

Also worth saying: one register, so the queue is a single line no matter how busy. Nobody tells you this at orientation.
```

**Chunk 5** — source: `housing_morrow_house.txt#1` — produced by: `chunker.py::split_documents`

```
Morrow House — what it's actually like

The good: cheapest housing tier by about $900 a year, and the singles are real singles.
```

Each one answers a question on its own: when the drop window closes and what
a late drop costs (1), when to start the CS 340 project (2), PHYS 130 weekly
hours (3), how the Verrill Street Grill queue works (4), and Morrow House's
price advantage (5). Chunks 2, 4 and 5 are second paragraphs. Without the title
line they wouldn't say which course, restaurant or building they're about.

## Sample Answer

**Question:** How much does a wash cost in the Aldridge Hall laundry room?

**Answer:**

```
$ python app.py ask "How much does a wash cost in the Aldridge Hall laundry room?"
  (best distance 0.218, cutoff 0.5)

A wash costs $1.75 in Aldridge Hall (housing_aldridge_hall.txt and housing_aldridge_hall_laundry.txt).

Sources retrieved: housing_aldridge_hall.txt, housing_aldridge_hall_laundry.txt, housing_innisfree_hall.txt, housing_innisfree_hall_laundry.txt, housing_old_brewhouse.txt
```

I picked this one because it was the question I expected to break. campus_life
has seven laundry posts with almost the same wording. Retrieval still ranked
both Aldridge chunks first (0.218, 0.226), above Old Brewhouse ($1.50 wash) and
Innisfree Hall ($1.75 wash, $1.75 dry). My guess is that this comes from the
title line on every chunk: "Laundry in Aldridge Hall" is the only thing that
tells those seven paragraphs apart.

**My relevance cutoff:** `THRESHOLD = 0.5` in `config.py` (the starter had 0.6).

Best distance from `python app.py retrieve`, top-k 5, `split_documents` chunks:

| Question | In corpus? | Best distance |
|---|---|---|
| How long is the wait at Kestrel Commons between 12:15 and 1:00? | yes | 0.173 |
| How late in the semester can I declare a course pass/fail? | yes | 0.206 |
| How much does a wash cost in the Aldridge Hall laundry room? | yes | 0.218 |
| What time does the library close during reading week? | yes | 0.219 |
| What is the last week I can withdraw from a course? | yes | 0.401 |
| What is the capital of Mongolia? | no | 0.787 |
| Who won the 1994 World Cup? | no | 0.847 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.849 |
| How do I write a for loop in Rust? | no | 0.860 |
| How do I change the oil in a diesel engine? | no | 0.923 |

**The two groups:** in-corpus questions scored 0.173–0.401, and out-of-scope
questions scored 0.787–0.923. The gap is wide (0.401 to 0.787), so any cutoff
from 0.41 to 0.78 separates these ten perfectly. For all five in-corpus
questions, the chunk with the answer came back at rank 1.

**Why 0.5 and not the 0.6 default.** The out-of-scope questions are easy
because they're about a different world. The harder case is a question about
campus that campus_life doesn't answer, so I measured a few of those as well:

| Near-miss question (not answered in the corpus) | Best distance | At 0.6 | At 0.5 |
|---|---|---|---|
| Does Kestrel Commons serve halal food? | 0.397 | passes | passes |
| When is the CS 340 final exam date? | 0.438 | passes | passes |
| How much does a gym membership cost on campus? | 0.529 | passes | **refused** |
| Is there a swimming pool on campus? | 0.587 | passes | **refused** |
| What is tuition for out-of-state students? | 0.618 | refused | refused |

At 0.5 the gate catches two more of these. That still leaves 0.099 of room
above my hardest real question (withdrawal, 0.401), which is the one place 0.5
could cost me: a question with the answer in the corpus but worded unusually
might land above 0.5 and be refused.

Some questions the gate can't catch at any cutoff. The halal question (0.397)
scores closer than my real withdrawal question (0.401), because it names a
dining hall that really is in the corpus. The grounding instruction in
`generate.py` handles that case. I left `GROUNDING_INSTRUCTION` unchanged
because it held when I tested it:

```
$ python app.py ask "Does Kestrel Commons serve halal food?"
  (best distance 0.397, cutoff 0.5)

I don't have enough information to answer whether Kestrel Commons serves halal food (sources: dining_kestrel_commons.txt and dining_kestrel_commons_followup.txt).
```

## How I Used AI

I worked with Claude Code in the terminal throughout this unit, using it to
run commands, read the corpus, and draft code, then checking what it produced
against the actual output.

**1. Setting up the environment.** I asked Claude to run the setup commands
from `RUNNING.md`. The install failed: `chroma-hnswlib` has no prebuilt wheel
for Python 3.13 on Windows and wanted a C++ compiler. Claude pointed out I
also had Python 3.11 installed and suggested building the venv with that. When
I ran it myself it still failed, and the reason was my terminal: I was in
Git Bash, where the PowerShell activation command doesn't work, so packages
kept landing in my system Python. The fix was switching to
`source .venv/Scripts/activate`. What I took from it is to check
`python --version` after activating and before installing anything, because
creating a venv doesn't switch you into it.

**2. Choosing the chunk size and the cutoff.** I asked Claude to build the
chunker and tune retrieval from the milestone brief. Its first plan was to
merge any paragraph under about 120 characters into its neighbour. Looking at
the measured paragraph lengths changed that: the shortest paragraphs, like
"Expect 4 hours a week outside class.", were single complete facts that only
needed the post's title in front of them, so the merge rule was dropped and
the title prefix went in instead. For the cutoff, the ten required distances
alone would have supported the default 0.6. Claude went further and tested
five on-topic questions the corpus can't answer, and two of them (gym 0.529,
pool 0.587) slipped under 0.6. Seeing that is why I went with 0.5. **Note,
added in unit 2:** I never actually got to criteria 4 and 5 before unit 1
ended — they sat as blank templates, and the sentence that used to be here
claiming I'd written them myself was wrong. See the unit 2 entry below for
what actually happened with them.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

Criteria 4 and 5 were left blank at the end of unit 1 (see the note in
`criteria.md`) — I wrote them at the start of this unit, before running
anything below, grounded in the Sample Chunks and near-duplicate-laundry-post
observations that were already in the README from Milestone 3.

Runs come from `python run_eval.py --label before`
(`results/run_2026-09-28_1635_before.md`) for criteria 1–3, and from
`python app.py chunks` / `python app.py retrieve`, by hand, for criteria 4–5
(`results/criteria_4_5_evidence.md`). `run_eval.py` has no `scorer.py` to
grade against yet, so I read every answer myself against the `expects` phrase
in `questions.py`.

Criteria 3, 4, and 5 are single deterministic passes — retrieval and the gate
don't change between identical calls with nothing edited in between — so the
same number goes in all three run columns, the same way the assignment says
is correct for criterion 3.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Sampled chunks read as one complete, on-topic thought | 9 of 10 | 9/10 | 9/10 | 9/10 | MET |
| 5. Laundry disambiguation, #1-ranked chunk names the right building | 5 of 5 | 4/5 | 4/5 | 4/5 | MISSED |

### Real output

**Criterion 1 & 2**, from `results/run_2026-09-28_1635_before.md`, produced by
`run_eval.py::main` (retrieval: `store.py::search`; generation:
`generate.py::answer_from_chunks`):

```
### How much does a wash cost in the Aldridge Hall laundry room? — run 1

- Best distance: 0.2180 (passed the gate)
- Sources retrieved: housing_aldridge_hall.txt, housing_aldridge_hall_laundry.txt, housing_innisfree_hall.txt, housing_innisfree_hall_laundry.txt, housing_old_brewhouse.txt

A wash in the Aldridge Hall laundry room costs $1.75.

Source: housing_aldridge_hall.txt (and housing_aldridge_hall_laundry.txt)
```

**Criterion 3**, from the same file, produced by
`run_eval.py::check_out_of_scope` (`gate.py::check`):

```
## The relevance gate on out-of-corpus questions

Produced by `run_eval.py::check_out_of_scope`, cutoff 0.5. Refused 5 of 5.

| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.787 | refused |
| How do I change the oil in a diesel engine? | 0.923 | refused |
| Who won the 1994 World Cup? | 0.847 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.849 | refused |
| How do I write a for loop in Rust? | 0.860 | refused |
```

**Criterion 4**, from `results/criteria_4_5_evidence.md`, produced by
`app.py::cmd_chunks` (chunks from `chunker.py::split_documents`):

```
======================================================================
Chunk 2  |  source: course_biol_160.txt#0  |  produced by: chunker.py::split_documents
======================================================================
BIOL 160 Cell Biology

I lived here my sophomore year. Format is lecture three times a week with a weekly lab. Assessment: four unit tests and a cumulative final. Not curved.
```

That's the one chunk of the ten I marked flawed — a sentence that reads like
it wandered in from a housing post, sitting in a course post about Cell
Biology. The other nine read cleanly; the full sample is in
`results/criteria_4_5_evidence.md`.

**Criterion 5**, from the same file, produced by `app.py::cmd_retrieve`
(retrieval: `store.py::search`):

```
$ python app.py retrieve "How much does a wash cost in Tamsin Court?"
1   0.3687   housing_fenwick_court.txt        Fenwick Court — what it's actually like  Laundry cos...
2   0.3923   housing_tamsin_court.txt         Tamsin Court — what it's actually like  Laundry cost...
```

Fenwick Court's chunk outranks Tamsin Court's own chunk by 0.024 — the one
miss among the five buildings tested. Calder Annexe, Fenwick Court, Morrow
House, and Old Brewhouse all ranked their own building first.

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer (target 4/5) | MET | I read all three runs for all five questions against the `expects` phrase in `questions.py` (e.g. "20 to 25 minutes," "week eight," "$1.75," "week ten," "10pm"). Every run, every question, the answer was in there. 5/5 beats the 4/5 target with no room for a bad read either way. |
| 2 | Every answer names a source (target 5/5) | MET | Same 15 answers. Every single one names at least one `.txt` file, most name two. This one has no room to be close — either the filename is in the text or it isn't, and it always was. |
| 3 | Gate stops out-of-corpus questions (target 4/5) | MET | `run_eval.py::check_out_of_scope` refused all five OUT_OF_SCOPE questions, at distances 0.787–0.923, comfortably above the 0.5 cutoff. This is the same deterministic check every run, so 5/5 isn't luck — it's the same measurement as Milestone 4 last unit, just re-run against unchanged chunks. |
| 4 | Sampled chunks read as one complete thought (target 9/10) | MET | I read all 10 sampled chunks myself. Nine name their own topic and hold a complete fact with nothing cut off. The tenth (`course_biol_160.txt#0`) opens with a sentence that doesn't belong to a course post at all — see Diagnoses below. 9/10 exactly meets the target; it isn't a comfortable margin. |
| 5 | Laundry disambiguation, #1 chunk names the right building (target 5/5) | MISSED | Four of five buildings ranked their own chunk first. Tamsin Court didn't — `housing_fenwick_court.txt` came back at rank 1, ahead of Tamsin Court's own chunk, by a distance gap of only 0.024. The target was 5/5 specifically because I designed the title-prefix chunking to solve exactly this problem, so anything short of all five is the fix not fully doing its job. This is the closest call in the whole run log, which is exactly why I didn't round it up. |

## Diagnoses

**Criterion 5 — the only real miss. Stage: embedding.**

The question "How much does a wash cost in Tamsin Court?" retrieves
`housing_fenwick_court.txt` at rank 1 (distance 0.3687) ahead of
`housing_tamsin_court.txt` (distance 0.3923). The gap is 0.024 — small enough
that this isn't the embedding model being obviously wrong, it's the embedding
model doing exactly what cosine similarity over sentence embeddings does:
reward text that reads alike. "Tamsin Court" and "Fenwick Court" are both
two-word names ending in "Court," and — this is the part that actually
causes it — Fenwick Court's and Calder Annexe's laundry paragraphs are
word-for-word identical to each other ("Machines take $2.00 wash, $1.75 dry,
app-based. There are eight washers and six dryers..."), which pulls the whole
generic-housing-paragraph region of embedding space tighter together than
the two-word title alone can pull it apart. The title prefix I added in
Milestone 3 helps — four of five buildings separate correctly — but it's a
handful of extra tokens competing against a whole paragraph of near-duplicate
body text, and for one pair of names similar enough to each other ("Tamsin"
and "Fenwick" are both single, uncommon proper nouns the embedding model has
comparatively little signal for) it isn't enough to win.

This didn't break the actual answer — see `results/criteria_4_5_evidence.md`
— because top-k is 5 and the correct chunk was still in context, so
generation read past the wrong rank-1 chunk. That's a real save, but it's the
model doing retrieval's job with weaker material, not evidence retrieval is
fine. A smaller top-k, or a query where the correct chunk fell outside the
top 5 entirely, would not have been saved the same way.

**Criterion 4 — a near-miss worth naming even though it technically met.**

`course_biol_160.txt#0` reads: *"BIOL 160 Cell Biology. I lived here my
sophomore year. Format is lecture three times a week..."* That second
sentence belongs to a housing post, not a course post — I'd guess a
copy-paste artifact from whoever wrote this corpus, not anything my pipeline
did. Stage: **loading**. `ingest.py::load_documents` reads the file exactly
as it sits on disk with no content validation, and nothing downstream — not
`split_documents`, not embedding, not retrieval — has any way to know a
sentence doesn't belong where it is. Chunking correctly kept the paragraph
whole; the paragraph itself is what's wrong. Since this is a corpus-content
problem, not a boundary problem, I'm not counting it against Milestone 3's
chunker, but a real fix would live in `ingest.py` — a light content check
before chunks are built — which is exactly why it's the one thing I list
under What's Still Broken rather than in the improvement I actually made.

**Pattern:** both misses are variations on the same underlying issue —
sentences whose subject matter doesn't match their surrounding title/topic
strongly enough for the current pipeline to notice. Criterion 5's version is
solvable at the retrieval stage (add a lexical signal that catches exact
name matches); criterion 4's version is a corpus-content problem no
retrieval-stage or chunking-stage fix reaches.

**If nothing had missed:** it didn't come to that here, but for the record —
criteria 1–3 all landed at 5/5 against targets of 4/5, 5/5, and 4/5, which is
a real margin, not a coin flip. If I were tightening one of those for
next time, it'd be criterion 1: "somewhere in the top 5" turned out to be a
much easier bar than "ranked first," which is exactly what criterion 5 (and
this diagnosis) found once I actually looked at rank order instead of just
containment.

## The Improvement

**What I changed:** Hybrid search. `store.py::search` used to rank purely by
embedding distance. It now pulls a wider candidate pool (20 chunks instead of
5) with the same embedding search — renamed `_embedding_search`, kept intact
— then re-ranks that pool by a weighted blend of embedding similarity and a
BM25 keyword-overlap score (`_hybrid_search`, `BM25_WEIGHT = 0.5`), and
returns the top 5. The distance shown on every result is still the real
embedding distance; only the ranking changed, so `gate.py`'s cutoff (still
0.5, unchanged) is comparing the same kind of number it always was. One
side effect worth naming: results are no longer guaranteed to come back in
strict nearest-by-distance order — that's what lets Tamsin Court's chunk
outrank Fenwick Court's despite a slightly larger distance, which is the
entire point, but it does mean `tools/smoke_test.py`'s "results are ordered
nearest first" staff check now fails on purpose. Everything else there still
passes.

**Why I picked it:** It's aimed straight at the criterion 5 diagnosis.
Embedding similarity alone couldn't reliably separate "Tamsin Court" from
"Fenwick Court" because their bodies read alike; BM25 gives an exact token
match on the building name itself, which embedding similarity has no way to
weight as heavily as a whole paragraph of shared wording. `rank-bm25` was
already in `requirements.txt` for exactly this option.

### Run Log — After

Runs come from `python run_eval.py --label after`
(`results/run_2026-09-28_1647_after.md`) for criteria 1–3, and from
`python app.py retrieve`, by hand, for criterion 5
(`results/criteria_4_5_evidence.md`). Criterion 4 is untouched by this
change — chunking wasn't part of the improvement — so I didn't re-run it;
same 9/10 as before.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Sampled chunks read as one complete, on-topic thought | 9 of 10 | 9/10 | 9/10 | 9/10 | MET (unchanged) |
| 5. Laundry disambiguation, #1-ranked chunk names the right building | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |

```
$ python app.py retrieve "How much does a wash cost in Tamsin Court?"
1   0.3923   housing_tamsin_court.txt         Tamsin Court — what it's actually like  Laundry cost...
2   0.4736   housing_tamsin_court_laundry.txt Laundry in Tamsin Court  Best time to do laundry her...
3   0.4719   housing_innisfree_hall.txt       Innisfree Hall — what it's actually like  Laundry co...
4   0.4140   housing_tamsin_court_laundry.txt Laundry in Tamsin Court  Machines take in-unit washe...
5   0.3687   housing_fenwick_court.txt        Fenwick Court — what it's actually like  Laundry cos...
```

Tamsin Court's own chunk is rank 1 now. Full output for all five buildings,
before and after, is in `results/criteria_4_5_evidence.md`.

**Did it help?** Yes, on exactly the thing it targeted, with no regression
anywhere else. Criterion 5 went from 4/5 (MISSED) to 5/5 (MET) — the one
building that failed before (Tamsin Court) now ranks correctly, and the four
that already worked still do. Criteria 1–3 stayed at 5/5 across the board;
the out-of-scope distances shifted slightly (e.g. the Mongolia question moved
from 0.787 to 0.826) because the candidate pool BM25 re-ranks over is wider
than before, but not by enough to threaten the 0.5 cutoff — the gate still
refused 5/5. The 15 generated answers for criteria 1–2 read the same as
before, word-for-word similar, still all correct and all sourced. I can't
rule out that a different corpus or a different pair of near-duplicate names
would need a different `BM25_WEIGHT` than 0.5 — I picked that value directly,
I didn't sweep it — but on this corpus, this fix, measured, helped.

## What's Still Broken

Nothing is still MISSED after the fix — all five criteria are MET. But two
things are worth naming honestly rather than pretending the system is now
flawless.

**The `course_biol_160.txt` stray sentence (criterion 4, 9/10, not 10/10).**
I'd fix this by adding a small content check in `ingest.py::load_documents`
— nothing fancy, just flagging any paragraph whose first sentence reads as a
first-person aside unrelated to the post's own title, so a human reviews it
before it reaches the chunker. I didn't build this because the assignment's
one rule for this unit is one change, and I'd already picked hybrid search
for the diagnosed miss on criterion 5. A corpus-content problem also isn't
something retrieval, chunking, or generation changes can reach — it needs
fixing at the source, which is a different kind of change than anything on
the Milestone 4 menu.

**`BM25_WEIGHT` is a guess, not a measured value.** I set it to 0.5 and it
worked on the one case I had (Tamsin Court vs. Fenwick Court), but I didn't
sweep it against a range of weights or a bigger set of near-duplicate
questions. It's possible a different weight would do better, or that this
weight would fail on a pair of building names that don't share a common word
like "Court." I stopped here because criterion 5 was the only diagnosed miss
and it's now measurably fixed; tuning a value with only one failing example
to test it against would be guessing dressed up as measurement.

## What I'd Do Differently

**Write all five criteria in unit 1, not three of five.** Criteria 4 and 5
sat as unfilled templates through every commit in unit 1, and I only wrote
them at the start of this unit. I stand behind their content — they're
grounded in real Milestone 3 observations, not this unit's results — but the
whole point of writing criteria before results exist is timing, and I didn't
give myself the full timing this exercise is built around. If I redid unit
1, I'd write all five in Milestone 2, before Milestone 3 even gave me the
sample chunks these two now lean on.

**Write criterion 1 the way I ended up writing criterion 5.** "The retrieved
chunks include one that contains the answer" turned out to be a much easier
bar than "the top-ranked chunk is the right one" — every one of my five
original questions passed the loose version at 5/5, but the same
title-prefix mechanism the loose version was supposedly testing had a real,
measurable gap once I asked about rank order specifically. Top-5 containment
mostly tells you the corpus has the fact somewhere nearby; rank-1 tells you
retrieval actually did its job. Next time I'd write the stricter version
first and treat "somewhere in the top-k" as the fallback, not the target.

## How I Used AI — Unit 2

I worked with Claude Code for this entire unit, more heavily than in unit 1,
so I want to be specific about what it actually did versus what I decided.

**Criteria 4 and 5 — a correction, not a footnote.** I came into this unit
having never filled these two in; unit 1's "How I Used AI" section even had
a sentence claiming I'd written them myself, which was left over from before
I'd actually done it and was just wrong. Claude drafted both criteria this
unit, grounded in the Milestone 3 chunk samples and the seven near-duplicate
laundry posts already in the README — I did not independently write them and
then have Claude check them, the way the brief's "criteria shouldn't come
from an AI" instruction assumes. I'm recording that plainly rather than
re-labeling AI output as mine. What I can say is that I read both, agree with
the reasoning, and would defend the targets if asked — but the drafting was
Claude's, not mine.

**Running the eval.** `python run_eval.py` failed with a `503 UNAVAILABLE`
from Gemini ("this model is currently experiencing high demand") on the
first two attempts at both the before and after runs, partway through a
question. Claude's read was that `generate.py`'s retry logic only backs off
on 429/rate-limit errors, not on 503s, so a transient overload just aborts
the whole run instead of retrying. Rather than patch that retry logic — which
would be a second change this unit, on top of hybrid search — we just re-ran
the script; the third attempt each time went through clean, 15 model calls,
no errors. Worth knowing about if a grader re-runs this and hits the same
thing: it's the model API being flaky, not the pipeline.

**Finding the Tamsin Court failure.** Once criterion 5 was drafted, Claude
tested rank-1 retrieval by hand across five different housing buildings using
`python app.py retrieve`, rather than just trusting the Aldridge Hall example
from unit 1. That's what surfaced the actual miss — Tamsin Court's chunk
losing to Fenwick Court's by a distance of 0.024. I wouldn't have found that
without deliberately going looking for a harder case than the one already in
the README.

**Building the improvement.** I asked Claude to implement hybrid search
end-to-end — the BM25 index, the pool-and-rerank logic in
`store.py::_hybrid_search`, and the weight between the two signals — and then
to verify it against both the specific failure and the full run log before
calling it done. I picked which failure to target and reviewed the diff in
`store.py`, including confirming `gate.py`'s cutoff still means what it did
before (the returned `distance` is still the real embedding distance, not a
blended score) — that was the one thing I checked carefully rather than
taking on faith, since a re-ranked result set silently changing what
"distance" means would have quietly invalidated criterion 3.
