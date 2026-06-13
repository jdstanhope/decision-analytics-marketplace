---
name: decision-review
description: >
  Close the loop on past decisions: record the assumptions, predicted ranges, and
  tripwires at decision time, then later review whether they held up and whether the
  reasoning was sound. Use this skill whenever someone wants to track a decision over
  time, journal a decision and its rationale, follow up on an earlier call, check whether
  forecasts or estimates came true, run a post-mortem or after-action review, separate a
  good decision from a lucky outcome, or measure how well-calibrated their predictions are.
  Trigger on phrases like "did my estimate hold up," "review that decision," "track this
  over time," "decision journal," "follow up in six months," "was I right," "post-mortem,"
  "after-action review," "calibration," "how good are my forecasts," or any request to
  capture a decision now for later scoring, or to score a decision made earlier — including
  the predictions, assumptions, and Monte Carlo / scenario outputs from the other toolkit
  skills.
---

# Decision Review & Calibration

Most decision tools stop at the moment of choice. This one covers what comes after: did
the estimates and assumptions actually hold, and — separately — was the *reasoning* sound?
That distinction is the whole point. A good decision can have a bad outcome (you took a
sensible bet and got unlucky) and a bad decision can have a good outcome (you got lucky).
Judging decisions only by results ("resulting") teaches the wrong lessons. Reviewing the
process, the assumptions, and the predicted ranges teaches the right ones — and tracked
across many decisions, it tells you whether your confidence is honest (calibration).

This skill closes the loop for the whole toolkit: the ranges from a Monte Carlo run, the
probabilities from a scenario analysis, the assumptions from a Key Assumptions Check, and
the tripwires from an Indicators & Warnings list all become things you can score later.

## The loop

1. **Capture** — at decision time, write a durable decision record: what you chose and
   why, the load-bearing assumptions, the predicted outcomes (as ranges or probabilities,
   not just point guesses), the tripwires you'll watch, and when to review.
2. **Schedule** — put the review date(s) somewhere they'll resurface: an automated
   in-app reminder and/or your real calendar (see "Scheduling reviews").
3. **Review** — at the review date, reopen the record, fill in what actually happened, and
   score it: did outcomes land in their intervals, did assumptions hold, did tripwires
   fire, was the process sound?
4. **Calibrate** — across many reviewed decisions, check whether your "80% confident"
   really comes true ~80% of the time, and adjust.

## Capturing a decision

Create a record with `scripts/decision_record.py --new --out <file>.json`, then fill it in
(or build it directly from another skill's output). Store records together in one folder
(e.g. `decisions/`) so calibration can aggregate them later.

What makes a record reviewable later is **falsifiable predictions and assumptions** — each
with a resolution date and a clear test for "did this hold?" Pull these straight from the
other skills:

- **From modeling-simulation:** record the P10/P50/P90 of the Monte Carlo output as a
  prediction interval, and any threshold probabilities (e.g. "83% chance of beating
  inflation") as probabilistic predictions.
- **From structured-analytic-techniques:** record the keystone assumptions (with their
  confidence and what would falsify each) and the Indicators & Warnings as tripwires.
- **From decision-analysis:** record the chosen option, the alternatives, the criteria
  weights, and the sensitivity flip-points (e.g. "C beats A as long as I weight downside
  ≥ 15%") — these are assumptions about your own priorities worth revisiting.

Good predictions are specific, measurable, and dated. "The market will do fine" can't be
scored; "10-year value between $61k and $129k (80% interval)" and "≥83% chance of beating
3% inflation by 2036" can. Validate a finished record with
`scripts/decision_record.py <file>.json`, which also lists which predictions are due.

## Scheduling reviews

The review dates live in the record's `review_schedule`. Resurface them two ways
(use either or both):

- **Automated reminder (in-app):** offer to create a scheduled task that re-opens the
  record and runs the review on the review date. This is the most reliable "follow up over
  time" mechanism because it actually re-runs the analysis, not just pings you.
- **Calendar event:** if a calendar connector is available (e.g. Google Calendar or
  Outlook/Microsoft 365), create a calendar event on each review date titled after the
  decision, with the record's location and the specific things to check in the event
  notes. Use the calendar's `find_free_time` / availability where useful so the review
  lands on a real working block. If no calendar is connected, suggest connecting one, or
  fall back to the in-app reminder.

When a decision has natural milestone dates (a contract renewal, a launch, a forecast
horizon), schedule reviews to those dates rather than arbitrary intervals — the record's
`resolves_on` fields are the natural anchors.

## Reviewing a decision

At the review date, fill the record's prediction `actual` values and add a review entry
(the script prints the template), then run
`scripts/score_review.py <file>.json`. It reports, for that decision:

- **Interval coverage** — did each actual land inside its 80% (P10–P90) interval? Outside
  is a signal your ranges were too narrow (overconfident) or biased.
- **Brier score** — for probabilistic predictions, how accurate and calibrated they were
  (0 = perfect, lower is better; 0.25 is the no-skill baseline of always saying 50%).
- **Assumption status** — which keystone assumptions held, broke, or are still open, and
  what the broken ones imply.
- **Tripwires** — which fired and when, and whether you acted on them.

Then do the judgment the script can't: **grade the process separately from the outcome.**
Ask "given only what I knew then, was this a reasonable choice?" Record that grade, the
lessons, and concrete actions (rebalance, revise a model input, change a weight, update a
belief). The aim is to improve future decisions, not to assign blame for variance.

## Calibration across decisions

Point `scripts/score_review.py --calibrate <folder>/` at a folder of reviewed records to
aggregate: overall interval hit-rate (is ~80% of reality landing in your 80% intervals?),
mean Brier score, and a calibration table bucketing your stated probabilities against how
often those predictions came true. The classic finding is overconfidence — intervals too
narrow, high-confidence calls missing more than they should. If you see it, widen your
ranges and discount your certainty; that single correction improves every future decision
the toolkit helps you make.

## Operating principles

**Resulting is the enemy.** Always separate decision quality from outcome quality. Reward
sound process even when the result disappointed; scrutinize lucky wins.

**Only falsifiable claims teach.** If a prediction or assumption can't be clearly judged
true or false later, rewrite it until it can, or drop it.

**Update, don't rationalize.** A broken assumption or a missed interval is information, not
failure. The value is in changing your model and your calibration, not in defending the
original call.

**Keep records together and revisit on cadence.** Calibration only emerges across many
decisions, so store records in one place and actually return to them.

## Output

For a capture, deliver the saved record and offer to schedule the review (reminder and/or
calendar event). For a review, deliver the scored results, the process-vs-outcome judgment,
and a short lessons-and-actions list — and offer to save it back into the record and to
update any downstream model (e.g. re-run the Monte Carlo with corrected assumptions). For a
calibration pass, deliver the aggregate hit-rate, Brier score, and calibration table with a
plain-language read of where confidence needs adjusting.
