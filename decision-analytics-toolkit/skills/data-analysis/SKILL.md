---
name: data-analysis
description: >
  Analyze a dataset to understand it and test claims about it: exploratory data analysis
  (EDA), summary statistics, distributions, correlation, hypothesis testing, and
  regression, with clear visualizations. Use this skill whenever someone has a CSV /
  spreadsheet / table of data and wants to understand it, find patterns or relationships,
  compare groups, test whether a difference is real or noise, quantify how one variable
  relates to another, check a hypothesis, or spot data-quality problems. Trigger on phrases
  like "analyze this data," "what's in this dataset," "is the difference significant," "A/B
  test," "correlation between," "what predicts," "run a regression," "explore this CSV,"
  "summary stats," or any request to draw evidence-based conclusions from tabular data —
  even when no specific statistical method is named.
---

# Data Analysis

Turn a table of data into understanding and defensible conclusions. This skill covers the
analytical arc: get to know the data (EDA), then answer specific questions about it
(comparisons, relationships, predictions) with the right statistical tool and honest
uncertainty.

The cardinal rule: **look before you leap.** Most analytical mistakes come from running a
test or model before understanding the data's shape, quality, and quirks. Always do
exploratory analysis first.

## Workflow

1. **Understand the goal.** What question is the data meant to answer? A decision, a claim
   to test, a relationship to quantify, or open-ended exploration? The goal determines the
   method.
2. **Explore first (EDA).** Run `scripts/eda.py` to profile the dataset: shape, types,
   missingness, summary stats, distributions, outliers, and correlations. Read the profile
   before any modeling. This catches the problems that silently invalidate analyses —
   missing data, wrong types, duplicates, impossible values, severe skew.
3. **Pick the method** from the guide below, matching it to the question and the data
   types involved.
4. **Run the analysis**, checking the assumptions the method requires.
5. **Interpret honestly** — effect size and uncertainty, not just a p-value; correlation
   vs. causation; and the limits of what this data can support.
6. **Visualize** the finding so it's legible to a non-statistician.

## Exploratory data analysis

EDA is non-negotiable and comes first. `scripts/eda.py` takes a CSV and produces a profile:
per-column type, missing %, unique counts, summary statistics for numerics, top categories
for categoricals, outlier flags (IQR rule), and a correlation matrix for numeric columns,
plus optional distribution and correlation plots. Use it to:

- **Assess quality:** missingness, duplicates, constant columns, impossible/extreme values,
  inconsistent categories. Decide how to handle each *and say what you did* — dropping or
  imputing data changes conclusions.
- **Understand shape:** Is a variable skewed? Bimodal? Does it need a transform? Are there
  outliers that will dominate a mean or a regression?
- **Spot relationships** worth testing, from the correlation matrix and scatterplots — as
  hypotheses to confirm, not conclusions.

Never skip to a test or model without reading the EDA profile first.

## Choosing a method

| Question | Data | Method |
|----------|------|--------|
| "What's typical / how spread out / what shape?" | one variable | Summary stats + histogram |
| "Are these two groups really different?" | numeric outcome, 2 groups | **t-test** (or Mann–Whitney if non-normal) |
| "Do these several groups differ?" | numeric outcome, 3+ groups | **ANOVA** (or Kruskal–Wallis) |
| "Are these two categories associated?" | two categoricals | **Chi-square test** |
| "How do two numeric variables move together?" | two numerics | **Correlation** (Pearson / Spearman) |
| "How does X (and others) relate to / predict Y?" | numeric outcome + predictors | **Linear regression** |
| "What drives a yes/no outcome?" | binary outcome + predictors | **Logistic regression** |
| "Did the change cause the lift?" (A/B test) | outcome by variant | **Two-group test** + effect size + interval |

`scripts/stats_test.py` runs the comparison and association tests (t-test, Mann–Whitney,
ANOVA, Kruskal–Wallis, chi-square, correlation) with assumption checks and effect sizes.
`scripts/regression.py` fits and diagnoses linear and logistic regression.

## Hypothesis testing — interpret it honestly

A statistical test answers a narrow question: *if there were truly no effect, how
surprising is data like this?* (the p-value). It does **not** tell you the size or
importance of an effect, or that an effect is real. Guard against the usual misreadings:

- **Report effect size and a confidence interval, always** — not just "p < 0.05." "Group A
  converts 3.1 points higher (95% CI 0.8–5.4)" is decision-useful; "significant (p=0.03)"
  is not. A tiny, useless difference can be "significant" with enough data; a large,
  important one can be "non-significant" with too little.
- **Non-significant ≠ no effect.** It means this data didn't establish one — often a power
  problem. Say so rather than declaring equivalence.
- **Check assumptions** (normality, equal variance, independence). The scripts flag
  violations and suggest the robust alternative.
- **Multiple comparisons inflate false positives.** Testing many things, expect some to
  look "significant" by chance; note it and correct (e.g. Bonferroni) when relevant.
- **State the practical conclusion**, in the units the user cares about, with its
  uncertainty — then what action it supports.

## Regression — relationships and prediction

Regression quantifies how an outcome relates to one or more predictors.
`scripts/regression.py` fits linear (continuous outcome) or logistic (binary outcome)
models and reports coefficients with confidence intervals, fit (R²/pseudo-R²), and
diagnostics (residual checks, influential points, multicollinearity via VIF). When
interpreting:

- A coefficient is the association with the outcome *holding the other predictors fixed* —
  state it in plain units ("each extra $1k of ad spend is associated with ~14 more
  signups, 95% CI 6–22").
- **Correlation is not causation.** Observational regression shows association; causal
  claims need a design (experiment, natural experiment) or strong assumptions. Flag
  confounders and don't let the user over-read coefficients as levers.
- Check the diagnostics the script reports — a good R² with patterned residuals or one
  dominant influential point is not trustworthy.
- Resist overfitting: with many predictors and little data, models memorize noise. Prefer
  fewer, motivated predictors and, where it matters, hold out data or cross-validate.

## Operating principles

**Garbage in, garbage out — so audit the data first.** The EDA step protects every
conclusion downstream. Most "surprising findings" are data errors.

**Quantify uncertainty; never imply false precision.** Every estimate gets an interval.
A point estimate with no error bar invites overconfidence.

**Distinguish exploration from confirmation.** Patterns found by trawling the data are
hypotheses, not results. Finding *and* "confirming" a pattern in the same dataset overstates
certainty — note when a finding is exploratory.

**Causation needs more than correlation.** Be explicit about what the data design can and
can't support. Most datasets license association, not cause.

**Make it legible.** A clear chart and a plain-language sentence beat a table of
coefficients for communicating to a decision-maker. Provide both.

## Output

Lead with the answer to the user's question in plain language, with the effect size and its
uncertainty, then the supporting detail and a chart. Save figures as files and offer them.
For deliverables, offer a written brief (docx) or, when the work is about cleaning/shaping/
summarizing a table, an analyzed spreadsheet (xlsx skill). Always state what was done to the
data and the main caveats so the conclusion can be trusted and reproduced.
