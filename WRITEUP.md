# Writeup

## 1. Approach & tradeoffs

The engine is a straight pipeline: the four CSVs are loaded into memory once,
at API startup, and never touched again per-request. For a given user, a
request runs through four stages — filter, score, weight, rank — and returns
the top N.

**Filter** is a sequence of hard eligibility gates in `engine/filters.py`:
drop anything already completed, drop anything whose prerequisite isn't
completed, drop anything whose level the user hasn't earned yet (either
through demonstrated topic history, or — for topics with no history at all —
a cap implied by their seniority). Nothing that fails a filter is ever seen
by the scoring stage; eligibility is decided once, cleanly, and the rest of
the pipeline never has to reconsider it.

**Score** runs three independent, pure functions in `engine/signals.py` —
one against the survey, one against usage history, one against work-info
fields — each producing a 0–1 score and a short reason fragment (or `None`
if that signal has nothing to say).

**Weight** blends those three into one score and one sentence, in
`engine/weighting.py`. This is the one function I'd point to first if asked
"what's the actual engineering judgment in this repo" — it's where the
cold-start policy and the final human-facing reason both get decided, in
code, not in comments.

I chose a hand-tuned weighted sum over a trained model (logistic regression,
a random forest, anything fit to data) for one reason: the case study's own
explainability requirement asks for a reason that's specific to *this course,
for this user, right now* — not a global feature-importance ranking. A
linear blend of three named, capped functions gives you that reason for
free, because you already know which signal fired and why. The real reason I
didn't fit weights statistically, though, isn't a modeling preference — it's
that there's no labeled outcome data. Nothing in this synthetic dataset
records "a recommendation was made and the user acted on it," because the
engine didn't exist when the data was generated. Regression needs
`(input, correct output)` pairs to learn from; there aren't any here. Section
4 below is the plan for what that data collection would need to look like.

**Where I deliberately kept it simple, and what that cost:** both filters use
hard blocks rather than soft penalties. A hard block is easier to defend
("why wasn't this shown?" has exactly one place to check) and structurally
guarantees an ineligible course can never slip through no matter how strong
its other signals are. The cost is flexibility — a near-miss (one prereq
short, one level over) has no way to surface even if everything else about
it is a great fit.

Two honest, verified limitations worth stating rather than hiding: first,
`apply_prerequisite_filter` and `apply_level_filter` overlap substantially in
this dataset, because every intermediate/advanced course's prerequisite is
itself a specific course one level down in the same topic — satisfying the
prerequisite usually already implies the level filter's behavioral check
would have passed anyway. The level filter's seniority-fallback path mostly
only does real work for cold-start users looking at beginner content; it's a
genuine safety net, not something currently carrying much independent
weight. Second, top-N results are frequently near-duplicate courses at the
same topic and level (e.g. "Intro to X" vs. "Fundamentals of X"), tied at
the same score — visible directly in `samples/sample_output.md`. The current
signals score at the topic/level granularity, not the individual-course
granularity, so courses that are interchangeable at that granularity come
out interchangeable in the ranking too.

**Where the LLM bonus fits, and why it's scoped the way it is.** I built two
distinct AI features, on purpose kept separate: a free-form Q&A assistant
(the "Ask a question" tab) that answers questions about a user's breakdown,
and a coaching-message rewriter (the "Coaching message" tab) that targets
the case study's bonus item directly — using an LLM to generate the
coaching-style text wrapping a recommendation. In both, Claude never touches
the score or the underlying reason. `engine/weighting.py` computes those
first, completely deterministically, and the LLM only receives that already-
decided output as fixed input — for the coaching feature, its system prompt
explicitly forbids inventing facts, numbers, or reasons beyond what it's
given, and only allows rephrasing the tone. The LLM earns its place here
specifically because it's *good at exactly one narrow thing plain logic
isn't*: turning a debug-log-flavored sentence ("Because you told us X is a
skill gap, and you did well in other X courses, we suggest this course.")
into something that reads like it was written by a person, without having
to hand-write a template for every combination of firing signals. It does
not earn a place inside the scoring loop — that decision needs to stay
traceable to a specific, named function, and an LLM call is neither
reproducible nor auditable in the way `weighting.py` is. This is also my
answer to "where would you keep the LLM out of the loop": out of scoring,
filtering, and ranking entirely; in, only at the last step, rewriting text
whose meaning was already fully decided before Claude ever saw it.

## 2. Signal weighting

`engine/weighting.py::DEFAULT_WEIGHTS` is `{survey: 0.4, usage: 0.4,
work_info: 0.2}`. Survey and usage are weighted equally as the two strongest
signals — both are rich, multi-tag data sources with real resolution.
`work_info` is five categorical fields (role, industry, company size,
seniority, stated goal) — much less resolution, explicitly a tie-breaker
per its own docstring, so it carries less weight than either of the other
two.

These numbers are asserted, not fit — there is no historical "this
recommendation worked" outcome in a cold synthetic dataset to fit them
against. If real usage data existed, the honest next step would be to log
which recommendations led to a `started` or `completed` event within some
fixed window, then fit weights (most naturally a logistic regression predicting
that binary outcome from the three signal scores) against that. That
wouldn't cost the explainability requirement anything — a fitted linear
model's coefficients are just as inspectable as a hand-picked one; the
label is the missing ingredient, not the model family.

Cold-start handling is where the weighting logic does its most important
work, covered in full in section 3.

## 3. Cold-start

The policy is renormalization, not treat-as-zero. A signal returning
`reason=None` means, by construction in `engine/signals.py`, that it has
nothing to contribute — either there's no data (no survey response, no
usage history) or there is data but it found zero overlap. Both collapse to
the same "abstain" marker on purpose, because neither should be treated as
a real, penalizing zero. When a signal abstains, its weight is dropped
entirely and redistributed proportionally across whichever signals did
fire, rather than counted as a genuine bad score that drags the blend down.

The alternative — treating a missing signal as a real zero — double-punishes
cold-start users: once for having no data, and again because that absence
mathematically drags their score toward zero regardless of how good their
other signals are. I verified the renormalization policy directly rather
than just arguing for it: `U00005`, a user with zero usage events and no
survey response at all, still receives a real, explainable top
recommendation (score `0.6`, driven entirely by the `work_info` signal's
match on `stated_goal`) instead of a degenerate near-zero score. That
example is captured in `samples/sample_output.md`.

The transition from cold-start to behavior-driven is gradual and automatic,
with no explicit threshold logic anywhere. The moment `usage_signal` or
`survey_signal` has something to say — the user fills in a survey, or
completes a course — its weight re-enters the blend on its own, in
proportion to how much other data is or isn't present. There's no special
"now treat this user as warmed up" branch to maintain or get wrong.

The strategy's real limit: a user whose only firing signal is `work_info`
gets recommendations based purely on demographic and self-reported data.
If their `stated_goal` doesn't actually reflect what they want, the
recommendation will feel generic or simply wrong — the same failure mode
any survey/demographic-based cold-start approach has. There's no usage
history yet to correct against.

## 4. Measuring success

**Hypothesis:** recommendations backed by agreement across two or more
signals (e.g. survey and usage both pointing at the same topic) convert to
a course-start within 7 days at a higher rate than recommendations backed
by only one firing signal — which, in practice, is disproportionately the
cold-start population relying on `work_info` alone.

**Metric:** 7-day course-start rate on the top-ranked recommendation,
segmented by how many signals fired for it (1, 2, or 3). Completion rate as
a secondary metric over a longer window (2–4 weeks), since starting and
finishing are different behaviors and a good recommendation should move
both.

**How I'd run it:** log, for every recommendation actually shown, the
`user_id`, `course_id`, `score`, and which signals fired — the exact shape
`engine/recommend.py::get_recommendation_breakdown` already produces, just
persisted instead of thrown away after the response. Join that against
`usage_events` after the fact to see whether a `started` event for that
`course_id` appears within 7 days. No A/B split is strictly required for
this first pass — the "1 vs. 2 vs. 3 signals" segmentation is a natural
experiment already present in the population, since how many signals fire
depends on how much survey/usage data a user happens to have, not on
anything the system controls. A true A/B test (varying `DEFAULT_WEIGHTS`
itself, or renormalize-vs-treat-as-zero) would be the natural follow-up
once there's enough logged outcome data to know the segmentation result
first.

One confound to control for explicitly: cold-start users' recommendations
are structurally different (`work_info`-only), so pooling all users
together would conflate "fewer signals fired" with "this user happens to be
new" — segment by usage tier as well as signal count, not signal count
alone.

## 5. Scaling to 10k+ users and a growing catalog

What's fine as-is: the in-memory CSV load. Even at 10k users × 2k courses,
that's still a small table by pandas standards — it isn't the bottleneck,
and swapping it for a real database wouldn't change the actual cost driver
below.

What breaks first: the O(candidates) work done on every single request,
multiplied by concurrent traffic. All three signal functions, plus
`apply_level_filter`'s `candidates.apply(is_allowed, axis=1)`, run fresh
per request — `.apply(axis=1)` in particular is a row-by-row Python loop
under the hood, not a vectorized pandas operation, so it's the single
slowest piece of the pipeline and the first thing that would show up in a
profile at 10x scale.

What I'd change: vectorize `apply_level_filter`'s row check — map each
row's `topic` to its `max_rank` as a column operation instead of an
`.apply()` call, which is a mechanical rewrite of the same logic, not a
design change. I'd also cache the filtered candidate set per user for a
short TTL if the same `user_id` hits the endpoint repeatedly in a short
window, since filtering doesn't change between two requests seconds apart
for the same user.

What I'd leave alone: the overall filter → score → rank architecture and
the CSV-as-source-of-truth pattern. A bigger catalog and more users make
the per-request computation cost more visible, but they don't change what
that cost actually is — the storage layer was never the bottleneck, so
migrating it first would be solving the wrong problem.
