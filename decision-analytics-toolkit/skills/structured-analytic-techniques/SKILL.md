---
name: structured-analytic-techniques
description: >
  Apply structured analytic techniques (SATs) to reason carefully under uncertainty and
  reduce cognitive bias. Use this skill whenever someone needs to weigh competing
  explanations or hypotheses, surface and test hidden assumptions, stress-test a plan or
  belief, figure out why something happened, anticipate how a situation could evolve, or
  guard against groupthink and overconfidence. Trigger on phrases like "competing
  hypotheses," "what are we assuming," "premortem," "red team," "devil's advocate,"
  "what could go wrong," "how do we know," "challenge this thinking," "what would change
  my mind," or any request to analyze an ambiguous, contested, or high-stakes situation
  rigorously — even when the user does not name a specific technique.
---

# Structured Analytic Techniques

Structured analytic techniques (SATs) are step-by-step methods that externalize reasoning
so it can be inspected, shared, and challenged. They come from intelligence analysis,
where being wrong is expensive and the mind's shortcuts (confirmation bias, anchoring,
premature closure, groupthink) are the main enemy. They apply just as well to business,
product, policy, research, and personal decisions.

The core idea: **don't trust a conclusion that lives only in someone's head.** Lay the
reasoning out on the table — the hypotheses, the evidence, the assumptions, the ways it
could fail — so that flaws become visible.

> When facilitating a user-led decision (see the decision-coach skill), these techniques
> are the coach's toolkit: premortem and devil's advocacy to stress-test the user's
> options, and Indicators & Warnings to define the signposts they will watch before
> choosing — the same signposts that evaluate the choice later.

## How to use this skill

1. **Diagnose what kind of thinking trap the user is in**, then pick the matching
   technique from the selection guide below. Don't default to one favorite — the value of
   SATs comes from matching the method to the failure mode.
2. **Run the technique as a structured process**, doing the analytical work yourself
   where you can and drawing the user in where their judgment or private knowledge is
   needed. Externalize everything: write out the matrix, the list, the table.
3. **State the conclusion together with its fragility** — what would change it, how
   confident the analysis supports being, and what to monitor.

Most techniques here are reasoning processes you run in the conversation or capture in a
document. One (Analysis of Competing Hypotheses) benefits from a scoring script; use it
when the hypothesis/evidence matrix gets large.

## Choosing a technique

| If the situation is… | The trap is usually… | Use |
|----------------------|----------------------|-----|
| Several explanations compete for the same evidence | Latching onto the first/favorite explanation | **Analysis of Competing Hypotheses** |
| A plan or forecast rests on things taken for granted | Unexamined assumptions that quietly drive the conclusion | **Key Assumptions Check** |
| A decision is made and you're about to commit | Overconfidence, planning fallacy | **Premortem** |
| A view has hardened and everyone agrees | Groupthink, confirmation bias | **Devil's Advocacy / Red Team** |
| You need to detect a change early | Missing slow-building signals | **Indicators & Warnings** |
| The future is wide open and could break several ways | False precision, single-track planning | **Scenario / Quadrant Crunching** (see modeling-simulation skill for quantitative scenarios) |
| A claim is offered as fact | Accepting assertions without testing | **Quality of Information Check** |

When a problem has several of these features, chain the techniques: a Key Assumptions
Check often feeds an ACH matrix; a Premortem often surfaces indicators worth monitoring.

Full step-by-step protocols for every technique are in
`references/technique-catalog.md` — read it when running any technique below so you follow
the established structure rather than improvising.

## The four workhorse techniques

These cover the large majority of cases. Lead with them.

### Analysis of Competing Hypotheses (ACH)

Use when multiple explanations or predictions are in play and the temptation is to build a
case for the favored one. ACH inverts the usual habit: instead of looking for evidence
that *confirms* a hypothesis, you look for evidence that *refutes* each one. The hypothesis
left with the least disconfirming evidence is the most likely — and crucially, ACH
exposes which single piece of evidence, if wrong, would flip the conclusion.

Process: enumerate mutually exclusive hypotheses → list all relevant evidence and
arguments → in a matrix, rate how *consistent* each piece of evidence is with each
hypothesis (Consistent / Inconsistent / Neutral) → focus on inconsistencies, because
hypotheses with few inconsistencies survive → identify the most diagnostic evidence (the
items that discriminate between hypotheses) → report the conclusion plus its sensitivity.

For matrices beyond ~3 hypotheses × ~6 evidence items, use
`scripts/ach_score.py`, which tallies a weighted inconsistency score per hypothesis and
flags the most diagnostic evidence. See the script's header for the input format.

### Key Assumptions Check

Use before committing to any analysis, plan, or forecast. List every assumption the
conclusion depends on — especially the ones nobody is saying out loud because they feel
obvious. For each, ask: *How confident am I this holds? What happens to the conclusion if
it's false? What would tell me it's breaking?* Sort assumptions into solid, uncertain, and
load-bearing-but-shaky. The shaky load-bearing ones are where to focus attention,
contingency planning, and monitoring.

### Premortem

Use just before a decision is finalized. Imagine it's some months later and the decision
failed badly. Working backward from that failure, generate concrete reasons *why*. The
prospective-hindsight framing gives people permission to voice doubts that loyalty or
optimism would otherwise suppress, and it reliably surfaces risks a "what could go wrong?"
question misses. Convert the top failure modes into mitigations, owners, and tripwires.

### Devil's Advocacy / Red Team

Use when a position has consensus and you want to know if it's actually robust or just
unchallenged. Deliberately build the strongest possible case *against* the prevailing view
— not a strawman, the best real argument an intelligent opponent would make. Then see what
survives. Frame this explicitly as "the case others would make," so it's understood as a
stress test, not your own position.

## Operating principles

**Externalize, always.** The technique's power is in writing things down where they can be
seen and argued with. A matrix or a labeled list of assumptions beats a paragraph of prose
every time.

**Disconfirmation over confirmation.** Across nearly every technique, the move that adds
value is hunting for what would prove the favored idea *wrong*. Lean into that discomfort;
it's the whole point.

**Separate evidence from inference.** Keep "what we observed" distinct from "what we
concluded." Many bad analyses are confident inferences resting on thin or assumed
evidence. The Quality of Information Check (in the catalog) makes this explicit.

**Calibrate and caveat.** End with how much confidence the analysis supports and what
would change it. Avoid both false certainty and uselessly mushy hedging — say what you'd
bet on and what you wouldn't.

**Don't let the structure become theater.** If a technique isn't earning its keep for the
problem at hand, switch or stop. The goal is better thinking, not completed templates.

## Output

For a quick application, deliver the result inline: the matrix or assumption table, the key
finding, and what would change it. For a substantial analysis the user will keep or share,
offer to produce a written brief (use the docx skill) structured as: question →
hypotheses/assumptions considered → analysis (with the matrix or table) → finding and
confidence → what to monitor / what would change the assessment.
