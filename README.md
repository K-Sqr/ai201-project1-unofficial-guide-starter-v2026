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

I used Claude Code (Claude Opus 5.5) in my terminal for most of this unit.

**1. Getting the environment to install.** I pasted the Windows setup commands
from `RUNNING.md` and asked Claude to run them. `pip install` failed:
`chroma-hnswlib` has no prebuilt wheel for Python 3.13 on Windows, so pip tried
to compile it and needed Microsoft C++ Build Tools. Claude found that I also
had Python 3.11 installed and told me to create the venv with
`py -3.11 -m venv .venv`. I asked it to stop and undo everything, then ran the
commands myself. That failed again, because I was in Git Bash, where
`.venv\Scripts\Activate.ps1` loses its backslashes and can't run a PowerShell
script anyway. So every `pip install` kept going into my system Python 3.13.
Claude gave me the bash version (`source .venv/Scripts/activate`). The last
thing I changed was running that on its own and checking `python --version`
before installing. That's how I found out that creating the venv hadn't
activated it.

**2. Building milestones 3 and 4.** I gave Claude the milestone brief and the
grading page and asked it to finish the build. It read the documents, measured
paragraph lengths, and wrote `split_documents`. Its first plan was to merge any
paragraph under ~120 characters into its neighbour. It dropped that after
finding that the shortest paragraphs ("Expect 4 hours a week outside class.")
were single facts that only needed the title line in front of them. It then
measured the ten distances and, beyond the brief, the five near-miss
questions. That's why the cutoff is 0.5 and not 0.6. It would not write
criteria 4 and 5, because the brief says not to have an AI write them, so
those were left to me. I also changed how it committed: I asked for a commit and push
after each milestone rather than one push at the end, and I had it take the
AI co-author line out of the commit messages. That's why the AI use is
described here instead of in the commits.

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

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
