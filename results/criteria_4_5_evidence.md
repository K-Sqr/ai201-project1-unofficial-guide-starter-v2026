# Evidence for criteria 4 and 5

Criteria 1–3 are covered by `run_eval.py`'s output (the other files in this
folder). Criteria 4 and 5 aren't — they were written for this unit (see the
note in `criteria.md`) and there's no script for them, so this file is the
"run it by hand and save the real output" path the assignment explicitly
allows. Both checks are deterministic (chunking and retrieval don't change
between calls with no code change in between), so one pass is the whole
measurement, the same way `run_eval.py::check_out_of_scope` treats criterion 3.

---

## Criterion 4 — chunk quality

Produced by: `app.py::cmd_chunks`, chunks from `chunker.py::split_documents`.

```
$ python app.py chunks -n 10
183 chunks total. Showing 10, spread across the corpus.

======================================================================
Chunk 1  |  source: admin_add_drop_deadline.txt#0  |  produced by: chunker.py::split_documents
======================================================================
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.

======================================================================
Chunk 2  |  source: course_biol_160.txt#0  |  produced by: chunker.py::split_documents
======================================================================
BIOL 160 Cell Biology

I lived here my sophomore year. Format is lecture three times a week with a weekly lab. Assessment: four unit tests and a cumulative final. Not curved.

======================================================================
Chunk 3  |  source: course_cs_340_exams.txt#1  |  produced by: chunker.py::split_documents
======================================================================
CS 340 Databases — assessment

Start the term project in week three, not week eight; everyone learns this the hard way.

======================================================================
Chunk 4  |  source: course_hist_118.txt#1  |  produced by: chunker.py::split_documents
======================================================================
HIST 118 Modern World History

Expect a lot of reading, about 120 pages a week, but no problem sets.

======================================================================
Chunk 5  |  source: course_phys_130_workload.txt#0  |  produced by: chunker.py::split_documents
======================================================================
Workload for PHYS 130 Mechanics

People keep asking so: 7 hours a week, plus 3 on lab weeks. That's real time, not optimistic time.

======================================================================
Chunk 6  |  source: dining_north_kitchen.txt#1  |  produced by: chunker.py::split_documents
======================================================================
North Kitchen

Hours are 11:00am to 7:00pm weekdays. Costs one meal swipe, or $13.00 cash.

======================================================================
Chunk 7  |  source: dining_verrill_street_grill_followup.txt#1  |  produced by: chunker.py::split_documents
======================================================================
Re: Verrill Street Grill

Also worth saying: one register, so the queue is a single line no matter how busy. Nobody tells you this at orientation.

======================================================================
Chunk 8  |  source: housing_calder_annexe_noise.txt#1  |  produced by: chunker.py::split_documents
======================================================================
Noise levels in Calder Annexe

If you're someone who needs quiet to work, the library is open until 2am during term and that's what most people in this building end up doing.

======================================================================
Chunk 9  |  source: housing_morrow_house.txt#1  |  produced by: chunker.py::split_documents
======================================================================
Morrow House — what it's actually like

The good: cheapest housing tier by about $900 a year, and the singles are real singles.

======================================================================
Chunk 10  |  source: housing_tamsin_court.txt#3  |  produced by: chunker.py::split_documents
======================================================================
Tamsin Court — what it's actually like

Laundry costs in-unit washer-dryer. On noise: quiet, structurally — concrete floors between units.
```

**My read, chunk by chunk:** 1 clean, 2 **flawed** (see below), 3 clean, 4
clean, 5 clean, 6 clean, 7 clean, 8 clean, 9 clean, 10 clean. **9 of 10.**

Chunk 2 (`course_biol_160.txt#0`) opens with "I lived here my sophomore
year" — a sentence that belongs to a housing post, not a course post about
Cell Biology. The chunker didn't cut this one wrong; the paragraph came out
of `ingest.py::load_documents` already containing that sentence. No chunk
boundary would fix it, because the whole paragraph is already one block.
This is content in the source document, not a chunking bug — see the
Diagnoses section in the README for the stage this actually belongs to.

Chunk 8 is a genuine near-neighbor of the same problem (a noise-levels
paragraph naming when the library is open, in a housing post) but it does
name what it's about ("Noise levels in Calder Annexe") and answers a noise
question about that specific building on its own, so I counted it as clean.

---

## Criterion 5 — laundry building disambiguation, rank 1 only

Produced by: `app.py::cmd_retrieve`, retrieval from `store.py::search`.
Five housing buildings whose `housing_*_laundry.txt` posts share near-
identical body wording (two of the seven, Calder Annexe and Fenwick Court,
are word-for-word identical except the building name and the two dollar
figures).

```
$ python app.py retrieve "How much does a wash cost in Calder Annexe?"
1   0.1871   housing_calder_annexe.txt        Calder Annexe — what it's actually like  Laundry cos...

$ python app.py retrieve "How much does a wash cost in Fenwick Court?"
1   0.1522   housing_fenwick_court.txt        Fenwick Court — what it's actually like  Laundry cos...

$ python app.py retrieve "How much does a wash cost in Morrow House?"
1   0.1930   housing_morrow_house.txt         Morrow House — what it's actually like  Laundry cost...

$ python app.py retrieve "How much does a wash cost in Old Brewhouse?"
1   0.1636   housing_old_brewhouse.txt        Old Brewhouse — what it's actually like  Laundry cos...

$ python app.py retrieve "How much does a wash cost in Tamsin Court?"
1   0.3687   housing_fenwick_court.txt        Fenwick Court — what it's actually like  Laundry cos...
2   0.3923   housing_tamsin_court.txt         Tamsin Court — what it's actually like  Laundry cost...
```

Calder Annexe, Fenwick Court, Morrow House, and Old Brewhouse all rank their
own building's chunk first. Tamsin Court doesn't: `housing_fenwick_court.txt`
outranks `housing_tamsin_court.txt` by a distance gap of only 0.024. **4 of
5.**

The end-to-end answer for Tamsin Court still came out right despite the
rank-1 miss, because the correct chunk was still in the top-5 context handed
to the model:

```
$ python app.py ask "How much does a wash cost in Tamsin Court?"
  (best distance 0.369, cutoff 0.5)

Based on the provided documents, there is no mention of the cost of a wash
in Tamsin Court (the documents only state that Tamsin Court has an in-unit
washer-dryer). Therefore, I do not have enough information to answer the
question.

Sources retrieved: housing_calder_annexe.txt, housing_fenwick_court.txt,
housing_fenwick_court_laundry.txt, housing_tamsin_court.txt,
housing_tamsin_court_laundry.txt
```

That's correct — Tamsin Court really doesn't have a per-wash price, it's an
in-unit washer-dryer — but it's correct because top-k is generous (5) and
the model read past the wrongly-ranked chunk, not because retrieval got it
right. A question that only asked for the single best match, or a smaller
top-k, would have handed the model the wrong building's price with nothing
to override it.

<!-- The "after" section — post-improvement retrieval for the same five
     buildings — is added lower down once the hybrid-search change lands.
     See the README's "The Improvement" for that comparison. -->
