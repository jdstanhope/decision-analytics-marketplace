---
name: modeling-simulation
description: >
  Build quantitative models that handle uncertainty: Monte Carlo simulation, sensitivity /
  tornado analysis, scenario planning, and simple forecasting. Use this skill whenever
  someone wants to estimate a range of outcomes rather than a single number, ask "what if"
  questions, find out which assumptions drive a result, stress-test a budget / projection /
  plan, model risk, combine uncertain inputs, or project a trend forward. Trigger on
  phrases like "Monte Carlo," "simulate," "what's the range," "best/worst case,"
  "sensitivity analysis," "what drives the outcome," "model the uncertainty," "scenario,"
  "probability of hitting," "forecast," or any request to put numbers and uncertainty
  around a projection or plan — even when no specific method is named.
---

# Modeling & Simulation

A single-number estimate ("revenue will be $2.4M") hides everything that matters: how wrong
it could be, what it depends on, and how likely the bad cases are. This skill replaces
point estimates with models that carry uncertainty through to the answer — so you get a
*distribution* of outcomes, know which inputs drive it, and can quantify the chance of
hitting or missing a target.

Four complementary methods:

- **Monte Carlo simulation** — when a result combines several uncertain inputs and you
  want the full distribution of outcomes, not just a midpoint.
- **Sensitivity / tornado analysis** — when you want to know *which* inputs actually move
  the result, so you can focus estimation effort and management attention.
- **Scenario planning** — when uncertainty is structural (a few big unknowns break the
  future into distinct worlds) rather than a smooth statistical spread.
- **Forecasting** — when you have a history and want a projection with an honest
  uncertainty band.

## How to use this skill

1. **Write the model explicitly first.** State the output you care about and the formula or
   logic linking inputs to it (e.g. `profit = units × price − units × unit_cost − fixed`).
   A model you can't write down, you can't simulate. Keep it as simple as captures the real
   drivers.
2. **Characterize each uncertain input as a distribution, not a number.** Pick a
   distribution that matches what's known (see the cheat-sheet below). Where the user only
   has low/likely/high, a triangular or PERT distribution turns that directly into a model
   input.
3. **Run the simulation / analysis** with the bundled scripts so the math is correct and
   reproducible.
4. **Report the distribution and its drivers** — central estimate, range (e.g. P10–P90),
   probability of key thresholds, and the tornado of what matters most. Never collapse it
   back to a single number without the band.
5. **Sanity-check the model** against known cases and common sense before trusting it.

## Choosing a distribution for an uncertain input

| What you know about the input | Use | 
|-------------------------------|-----|
| A low, most-likely, and high guess | **Triangular** (or **PERT** for a smoother, less extreme shape) |
| A mean and a symmetric ± spread | **Normal** |
| A quantity that can't go negative and is right-skewed (durations, costs) | **Lognormal** |
| Equally likely anywhere in a range | **Uniform** |
| A yes/no event with probability p | **Bernoulli** |
| A rate / count of independent events | **Poisson** |
| Genuinely unsure of shape, only bounds and a middle | **Triangular** — transparent and defensible |

Be honest about correlation: if two inputs move together (high demand *and* high price),
modeling them as independent understates the variance. Note correlations and, when they
matter, build them in.

## Monte Carlo simulation

The workhorse. Draw thousands of random samples for each input, compute the output for each
draw, and read off the resulting distribution.

`scripts/monte_carlo.py` runs a simulation from a JSON model: it defines the output as an
expression over named inputs, each input given a distribution. It returns the mean, median,
standard deviation, key percentiles (P5/P10/P50/P90/P95), the probability of user-specified
thresholds (e.g. P(profit < 0)), and saves a histogram. See the script header for the
schema — typical use:

- Define inputs like `units: triangular(800, 1000, 1400)`, `price: normal(50, 5)`.
- Define the output expression: `units * price - units * unit_cost - fixed_cost`.
- Ask for `P(output < 0)` and `P(output > 100000)`.

Run enough iterations for stable tails (10,000+ is usually fine; the script reports a
convergence check). Report results as a range and probabilities, e.g. "median profit
$320k, 80% interval $90k–$560k, and an 18% chance of a loss" — far more decision-useful
than a single expected value.

## Sensitivity / tornado analysis

Tells you which inputs the answer actually hinges on. Two flavors, both in
`scripts/monte_carlo.py`:

- **One-at-a-time tornado:** swing each input from its low to its high (holding others at
  baseline) and measure the output swing. Plotted as a tornado chart, the widest bars are
  the inputs worth pinning down. Use this to decide where more research is worth it.
- **Driver ranking from the simulation:** rank-correlate each sampled input with the
  output across the Monte Carlo run, showing which inputs explain the spread when
  everything varies together.

Lead almost every modeling exercise with sensitivity analysis: it focuses effort, exposes
which assumptions are load-bearing (link back to the Key Assumptions Check in the
structured-analytic-techniques skill), and often shows that most inputs barely matter.

## Scenario planning

When the future hinges on a couple of big, discontinuous unknowns (a regulation passes or
not; a key partnership holds or breaks), a smooth distribution misleads. Instead:

1. Identify the two most important and most uncertain driving forces.
2. Cross them into a 2×2 of four distinct, internally coherent scenarios; name and narrate
   each.
3. Run the quantitative model (Monte Carlo or a simple calc) *within* each scenario, since
   inputs differ by world.
4. Identify robust strategies (good across scenarios) vs. scenario-specific bets, and the
   early indicators that signal which world is arriving. (The SAT skill's Indicators &
   Warnings pairs directly with this.)

## Forecasting

For a time series with history, project forward with an honest uncertainty band rather than
a single line. `scripts/forecast.py` provides transparent baselines — linear/loglinear
trend, moving average, and simple exponential smoothing — with prediction intervals, and
reports which baseline best fits the recent history. These are deliberately simple and
explainable; for strong seasonality or many series, say so and recommend a dedicated
forecasting approach rather than overfitting a toy model. Always show the interval, and
never extrapolate far beyond the data without flagging that uncertainty grows with horizon.

## Operating principles

**A model is a tool for thinking, not an oracle.** Its outputs are exactly as good as its
structure and inputs. State both plainly so they can be challenged. "All models are wrong;
some are useful" — aim for useful and honest about the wrongness.

**Carry uncertainty all the way through.** The entire point is to avoid false precision.
Resist the pull to report one number; report the range and the odds.

**Find the drivers before polishing the estimate.** Sensitivity analysis usually reveals
that two or three inputs dominate. Refine those; don't waste effort on inputs that don't
move the answer.

**Validate.** Check the model on a case where you know the answer, confirm units and edge
behavior, and watch for nonsense (negative counts, probabilities outside the model). Show
the validation so the user can trust the result.

## Output

Report the central estimate with its interval, the probability of the thresholds the user
cares about, and a tornado of the top drivers. Save charts (histogram, tornado, forecast
fan) and offer them as files. For results the user will share, offer a written brief (docx)
or a model workbook (xlsx) so others can vary the inputs themselves.
