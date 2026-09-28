# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
Four of my five questions each have one document that answers them. The
Aldridge Hall laundry question doesn't work that way: campus_life has seven
`housing_*_laundry.txt` posts written almost word for word the same ("Machines
take $X wash, $Y dry..."), so retrieval can easily bring back another building's
laundry post instead. I expect that one to fail sometimes. That's why the
target is 4 of 5 rather than 5 of 5.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
All five, not four. `generate.py::build_prompt` puts `[from <filename>]` in
front of every excerpt, and `GROUNDING_INSTRUCTION` tells the model to name the
file. So every answer that gets past the gate has the filenames right there in
its prompt. The only way to miss is for the model to ignore an instruction it
was given directly. If that happens even once, the pipeline has a real problem,
so I'm not allowing for one miss.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**
In Milestone 4 the five OUT_OF_SCOPE questions had best distances of
0.787–0.923, and my cutoff is 0.5. There's a clean gap, so I expect 5 of 5. The
target is 4 of 5 rather than 5 of 5 because I lowered the cutoff from 0.6 to
0.5 to catch on-topic near misses. If I change the chunker in unit 2, the
distances move, and I'm allowing for one question to shift. For even one to
slip through, its best distance would have to drop from at least 0.787 to below
0.5. If two slipped through, the gate would be broken, not just unlucky.

---

## 4. Something about your chunks

> **Note on criteria 4 and 5:** I left these two as unfilled templates at the
> end of unit 1 — I wrote 1–3 and never came back to finish the other two.
> I'm completing them now, before touching `run_eval.py`'s output for this
> unit, using only what Milestone 3 already established: the Sample Chunks
> section of the README (five chunks, all clean) and the fact that
> `campus_life` has seven near-identical `housing_*_laundry.txt` posts,
> both written and committed before this unit started. I did look at a couple
> of extra retrieval examples while shaping criterion 5's wording below, so
> I'm not claiming these are blind the way 1–3 were — just that they're
> grounded in old evidence, not this unit's QUESTIONS run.

For at least 9 of 10 chunks sampled with `python app.py chunks -n 10`, the
chunk reads as one complete, on-topic thought — no sentence cut in half at a
chunk boundary, and no sentence that belongs to a different topic than the
one the title names.

**Why this target:**
The five chunks I sampled and pasted into the README in Milestone 3 all read
cleanly — that's what made me confident in the title-prefix, one-paragraph
strategy in the first place. I'm allowing exactly one exception in a bigger
sample of 10, because `campus_life`'s posts are informal, first-person
student writing, and a paragraph occasionally drifts into an aside that
doesn't belong to its own heading. That's a content property, not something
my chunker controls — see criterion 5 in `chunker.py`'s docstring about what
Milestone 3 does and doesn't fix.

---

## 5. Your choice

For laundry-cost questions naming five different housing buildings whose
posts share near-identical body wording (Calder Annexe, Fenwick Court,
Morrow House, Old Brewhouse, Tamsin Court), the #1-ranked retrieved chunk
names the correct building, in 5 of 5.

**Why this target:**
This is deliberately stricter than criterion 1's "somewhere in the top
results" — I'm testing whether the fix I actually built in Milestone 3 (the
title prefix on every chunk) does what I designed it to do: let retrieval
tell seven near-identical buildings apart. If the title prefix works as
intended, every one of these five should rank its own building first,
because each title names one specific, unambiguous building — there's no
reason to allow a miss the way I do in criterion 1, where the ambiguity is
inherent to the corpus rather than something my own design was supposed to
fix. Two of the seven laundry posts (Calder Annexe and Fenwick Court) are
word-for-word identical in their bodies, so this is the sharpest test I have
of whether the title prefix is actually carrying the weight I think it is.

---

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
