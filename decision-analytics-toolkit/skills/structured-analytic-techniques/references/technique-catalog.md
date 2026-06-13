# Structured Analytic Technique Catalog

Step-by-step protocols. Read the entry for whichever technique you're running so the
process follows the established structure. Techniques are grouped by purpose.

## Contents

- Diagnostic techniques: Analysis of Competing Hypotheses, Quality of Information Check,
  Key Assumptions Check
- Contrarian techniques: Premortem, Devil's Advocacy, Red Team, "What If?" Analysis,
  High-Impact/Low-Probability Analysis
- Imaginative techniques: Brainstorming (structured), Scenario Analysis, Quadrant
  Crunching, Indicators & Warnings

---

## Analysis of Competing Hypotheses (ACH)

**Purpose:** Evaluate multiple competing explanations even-handedly and avoid premature
closure on a favorite.

**Steps:**
1. **Enumerate hypotheses.** Brainstorm the full set of plausible explanations or
   outcomes. Make them mutually exclusive where possible. Include at least one you find
   unlikely — denial and deception live there. Aim for 3–7.
2. **List evidence and arguments.** Gather all relevant items: hard evidence, absence of
   evidence (a dog that didn't bark is data), assumptions, and logical arguments.
3. **Build the matrix.** Rows = evidence, columns = hypotheses. For each cell, judge
   whether the evidence is **C**onsistent, **I**nconsistent, or **N**eutral/not applicable
   with that hypothesis *if that hypothesis were true*.
4. **Refine.** Delete evidence with all-C or all-N rows — it doesn't discriminate, so it's
   not diagnostic. Keep the items that distinguish hypotheses.
5. **Score by inconsistency.** Tally inconsistencies per column. The hypothesis with the
   *fewest* inconsistencies is most likely. You're trying to *disprove*, not prove —
   evidence can be consistent with many hypotheses at once, so consistency is weak;
   inconsistency is what eliminates.
6. **Sensitivity check.** Identify the few pieces of evidence driving the conclusion. Ask:
   how solid is each? If the linchpin item were wrong or deception, which hypothesis wins?
7. **Report** the relative likelihood of all hypotheses (not just the winner), the most
   diagnostic evidence, and the linchpin assumptions to monitor.

Use `scripts/ach_score.py` for matrices large enough that hand-tallying is error-prone.

---

## Quality of Information Check

**Purpose:** Prevent confident conclusions from resting on weak sources.

**Steps:**
1. List the key evidence the conclusion depends on.
2. For each item rate: source reliability, recency, directness (first-hand vs. hearsay),
   and whether it could be deliberate deception or motivated reporting.
3. Flag conclusions that hinge on a single weak or uncorroborated item.
4. Distinguish "we know," "we assess," and "we assume." Re-label anything mis-filed.

---

## Key Assumptions Check

**Purpose:** Surface and test the load-bearing assumptions beneath an analysis or plan.

**Steps:**
1. Write down the judgment or plan in one sentence.
2. List every assumption it requires to be true. Push for the unstated ones: "we're
   assuming demand stays flat," "we're assuming the vendor delivers on time," "we're
   assuming our competitor won't respond."
3. For each assumption mark: confidence (high/medium/low) and impact-if-false
   (high/medium/low).
4. The **low-confidence + high-impact** assumptions are the keystones. For each, define a
   monitoring signal and, if possible, a contingency.
5. If a keystone collapses on inspection, the analysis must be reworked before proceeding.

---

## Premortem

**Purpose:** Use prospective hindsight to surface failure modes before committing.

**Steps:**
1. Fix a future date and assert: "It is [date]. We went ahead, and it failed — clearly and
   painfully."
2. Independently generate reasons why (silent written generation first avoids anchoring on
   the loudest voice).
3. Cluster the reasons into failure themes.
4. Rank by plausibility × severity.
5. For the top themes, define mitigations, owners, and tripwires (early-warning signals).
6. Decide what, if anything, changes about the plan before committing.

---

## Devil's Advocacy

**Purpose:** Stress-test a consensus by mounting the strongest case against it.

**Steps:**
1. State the prevailing view crisply.
2. Build the best genuine argument *against* it — strongest evidence, most plausible
   alternative reading, not a strawman.
3. Identify which supports for the prevailing view are assumptions vs. evidence.
4. Report what survived the challenge and what was weakened. Frame as "the case a sharp
   opponent would make," not a personal position.

---

## Red Team

**Purpose:** Reframe from an adversary's or outsider's perspective.

**Steps:**
1. Define the actor whose viewpoint to adopt (a competitor, an attacker, a regulator, a
   skeptical customer).
2. Step fully into their goals, constraints, and information.
3. From that seat, ask: how do they exploit, counter, or perceive our plan?
4. Translate findings back into risks and adjustments for the home team.

---

## "What If?" Analysis

**Purpose:** Loosen a fixed mindset by assuming a surprising event already happened.

**Steps:**
1. Assume a significant, off-trend event has occurred ("the deal fell through the day
   before signing").
2. Work backward to construct plausible chains that could have produced it.
3. Identify the early indicators those chains would have generated.
4. Decide which indicators are worth watching now.

---

## High-Impact / Low-Probability Analysis

**Purpose:** Give serious, structured attention to a consequential long-shot without
overweighting it.

**Steps:**
1. Define the high-impact event precisely.
2. Specify plausible pathways to it and the conditions each requires.
3. Identify observable indicators for each pathway.
4. Sketch consequences and no-regret hedges. Keep the low base rate explicit.

---

## Structured Brainstorming

**Purpose:** Generate a wide option/hypothesis set before converging.

**Steps:**
1. Silent individual idea generation (avoids dominance and anchoring).
2. Round-robin collection, no criticism, build on others' ideas.
3. Cluster into themes.
4. Only then evaluate and prioritize. Keep divergence and convergence as separate phases.

---

## Scenario Analysis / Quadrant Crunching

**Purpose:** Explore multiple plausible futures instead of planning for one.

**Steps:**
1. Identify the two most important and most uncertain driving forces.
2. Cross them into a 2×2 to define four distinct, internally consistent scenarios.
3. Name each scenario and write its short narrative.
4. For each, identify implications, opportunities, threats, and early indicators.
5. Find strategies that are robust across scenarios (no-regret moves) vs. bets specific to
   one. For quantitative / probabilistic scenarios, hand off to the modeling-simulation
   skill.

---

## Indicators & Warnings

**Purpose:** Detect which scenario or hypothesis is materializing, early.

**Steps:**
1. For each scenario/hypothesis, list concrete, observable things that would appear if it
   were coming true.
2. Make indicators specific and ideally measurable, not vague ("competitor cuts price
   below $X," not "competition heats up").
3. Assign where/how each would be observed and who watches it.
4. Review on a cadence; a cluster of one scenario's indicators lighting up is the warning.
