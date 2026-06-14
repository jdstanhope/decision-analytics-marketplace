---
name: decision-analysis
description: >
  Help choose among defined options using decision analysis: multi-criteria scoring
  (MCDA), weighted decision matrices, Pugh matrices, decision trees, expected value, and
  value of information. Use this skill whenever someone is comparing options or
  alternatives against several factors, trying to make a choice "more objective," weighing
  trade-offs, building a decision under uncertainty with branching outcomes, or asking
  which choice has the best expected payoff. Trigger on phrases like "which option should
  we pick," "compare these alternatives," "weigh the pros and cons," "decision matrix,"
  "scoring model," "expected value," "decision tree," "is it worth it," or any request to
  structure a choice between concrete options — even when no specific method is named.
---

# Decision Analysis

Decision analysis turns a fuzzy "which should we choose?" into an explicit model: what the
options are, what we care about, how each option performs, and — when outcomes are
uncertain — what each path is worth on average. The point isn't to let a number make the
decision. It's to make the reasoning explicit so a person or team can see the trade-offs,
challenge the inputs, and decide with their eyes open.

Two families of method, picked by whether outcomes are certain:

- **Multi-criteria choice** (options × criteria are knowable now): weighted scoring,
  Pugh matrix. *"Which laptop / vendor / candidate / city is best for us?"*
- **Choice under uncertainty** (outcomes branch on chance): decision trees, expected
  value, value of information. *"Should we launch now or run a test first? Build or buy?"*

> **Coaching mode.** When the user wants to be facilitated through the decision rather than
> handed an answer, the criteria, weights, and options are *theirs* — elicit them, don't
> impose them. Use the decision-coach skill to run that staged, user-led process; this
> skill then provides the scoring engine at the choice stage.

## How to use this skill

1. **Frame the decision** before scoring anything. Nail down: the actual decision being
   made, the realistic options (including "do nothing" and any hybrids), and what
   genuinely matters about the outcome. A clean frame prevents a precise answer to the
   wrong question.
2. **Pick the method** from the guide below.
3. **Build the model with the user**, making weights, scores, and probabilities explicit
   and sourced. Where inputs are guesses, say so.
4. **Run sensitivity analysis** — never present a ranking without testing how fragile it
   is. A decision that flips when a weight moves 10% isn't really decided by the model.
5. **Report the recommendation with its drivers and its fragility**, not just a winner.

The quantitative steps have scripts so the math is reliable and reproducible. Use
`scripts/weighted_score.py` for multi-criteria choice and `scripts/decision_tree.py` for
trees / expected value.

## Choosing a method

| Situation | Method | Script |
|-----------|--------|--------|
| Compare options against multiple weighted factors | **Weighted scoring (MCDA)** | `weighted_score.py` |
| Quick screen of options vs. a baseline, minimal numbers | **Pugh matrix** | `weighted_score.py` (Pugh mode) |
| Outcomes branch on chance events; want best expected payoff | **Decision tree / expected value** | `decision_tree.py` |
| Deciding whether to pay for more information/testing first | **Value of information** | `decision_tree.py` |
| One overwhelming must-have requirement | **Screen first**, then score the survivors | — |

## Weighted scoring (multi-criteria decision analysis)

Use when several factors matter and they're not equally important. Process:

1. **List criteria** that distinguish the options and matter to the decision. Drop any
   that all options satisfy equally — they don't discriminate. Separate hard constraints
   (pass/fail screens) from scored criteria.
2. **Weight the criteria.** Assign weights summing to 100% (or rank-then-convert). Make
   the weights reflect real priorities; this is where values enter, so make them explicit
   and get buy-in. If a group disagrees on weights, that disagreement is the real decision
   — surface it.
3. **Score each option on each criterion** on a consistent scale (e.g. 1–5 or 0–10). Use
   the same anchored definitions for every option. Pull scores from data where possible
   rather than gut feel; note the source.
4. **Compute weighted totals**, but treat the ranking as the start of a conversation, not
   the verdict.
5. **Sensitivity analysis (required).** Identify the closest pairs and find how small a
   change in weights or a single score would flip them. Report which inputs the decision
   actually hinges on. `weighted_score.py` does this automatically.

Watch for: criteria that secretly measure the same thing (double-counting), scales that
aren't truly comparable across criteria, and reverse-engineering weights to justify a
pre-chosen answer. Name these risks when you see them.

### Pugh matrix (lightweight variant)

When you want a fast, low-precision screen: pick a baseline option, then rate every other
option on each criterion as better (+1), same (0), or worse (−1) than the baseline. Sum
per option. Great for early winnowing and for surfacing where options differ before
investing in precise scoring. `weighted_score.py --mode pugh` supports this.

## Decision trees & expected value

Use when the outcome depends on uncertain events, not just on which option you pick.

1. **Map the tree** left to right in time: square = decision node (you choose), circle =
   chance node (nature chooses). Branches off a chance node need probabilities that sum to
   1. Leaves carry payoffs (money, utility, time — one consistent unit).
2. **Estimate probabilities and payoffs.** Source them; flag the soft ones.
3. **Roll back (fold back) the tree** right to left: at a chance node, expected value =
   Σ(probability × branch value); at a decision node, take the best branch. The value at
   the root is the decision's expected value, and the chosen branches are the recommended
   policy.
4. **Account for risk attitude.** Expected value assumes risk-neutrality. For decisions
   large relative to the decider's resources, a high-variance option with the best EV may
   still be wrong. Flag variance and downside, not just the mean.
5. **Value of information.** Compare the expected value *with* perfect (or sample)
   information against the value *without* it. The difference is the most you'd rationally
   pay to learn the uncertain factor before deciding — directly answering "is it worth
   running the test / pilot / study first?"
6. **Sensitivity.** Find the probability or payoff thresholds at which the recommended
   decision changes. "Launch beats test as long as P(success) > 0.4" is far more useful
   than a single EV number.

`scripts/decision_tree.py` rolls back a tree from a JSON description, reports the optimal
policy and EV, and computes expected value of perfect information. See its header for the
schema.

## Operating principles

**The model serves the conversation.** Its job is to make trade-offs and assumptions
visible and arguable, not to hand down a verdict. If the user's gut rebels against the
model's answer, that's a prompt to examine which input is wrong — sometimes the model,
sometimes the gut.

**Garbage weights, garbage ranking.** Most of the real content lives in the weights and
probabilities. Spend effort there, source them, and test them. Precision in arithmetic
can't rescue arbitrary inputs.

**Always show fragility.** A ranking without sensitivity analysis is overconfident. The
most valuable output is often "this is close, and it turns on X" rather than a clean
winner.

**Right-size the rigor.** A two-option, low-stakes call may need only a Pugh matrix or a
back-of-envelope EV. Reserve full models for decisions where the stakes justify the effort.

## Output

Deliver a clear recommendation, the matrix or tree that produced it, the two or three
inputs it depends on most, and what would change the answer. For decisions the user will
present to others, offer a written brief (docx skill) or a scored matrix as a spreadsheet
(xlsx skill) so stakeholders can adjust weights themselves.
