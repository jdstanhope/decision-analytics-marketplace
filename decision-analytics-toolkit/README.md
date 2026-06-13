# Decision Analytics Toolkit

A set of four general-purpose skills that help individuals and small-to-medium teams
think more clearly and decide more rigorously. The skills are deliberately generic so
they apply across domains — business strategy, product, hiring, policy, personal
decisions, research, operations, and more.

| Skill | Use it when you need to… | Core methods |
|-------|--------------------------|--------------|
| **Structured Analytic Techniques** | Reduce bias and reason carefully under uncertainty | Analysis of Competing Hypotheses (ACH), Key Assumptions Check, Premortem, Devil's Advocacy / Red Team, Indicators & Warnings, Quadrant Crunching |
| **Decision Analysis** | Choose between defined options against multiple criteria | Weighted scoring (MCDA), Pugh matrix, decision trees, expected value, value of information |
| **Modeling & Simulation** | Quantify uncertainty and explore "what if" | Monte Carlo simulation, sensitivity / tornado analysis, scenario planning, simple forecasting |
| **Data Analysis** | Understand a dataset and test claims about it | Exploratory data analysis, hypothesis testing, correlation & regression, visualization |

## How the skills work together

These methods chain naturally. A typical end-to-end flow:

1. **Frame & de-bias** the problem with *Structured Analytic Techniques* — surface
   assumptions, lay out competing hypotheses, run a premortem.
2. **Quantify uncertainty** with *Modeling & Simulation* — build a Monte Carlo model of
   the outcomes you care about and find which variables matter most.
3. **Ground it in evidence** with *Data Analysis* — pull estimates and ranges from real
   data instead of guessing.
4. **Decide** with *Decision Analysis* — score the options against weighted criteria or
   compute the expected value of each path.

Each skill works standalone too — invoke whichever matches the problem in front of you.

## What's inside each skill

Every skill contains a `SKILL.md` (the framework and process Claude follows) plus
`scripts/` with reusable, dependency-light Python for the quantitative parts (Monte Carlo,
weighted scoring, decision-tree rollback, regression, EDA, and more). Scripts run with the
standard scientific Python stack (`numpy`, `pandas`, `scipy`, `matplotlib`).

## Design principles

- **Method-first, not tool-first.** Each skill picks the right technique for the problem
  and explains the reasoning, rather than reaching for one favorite hammer.
- **Show your work.** Outputs make assumptions, weights, and uncertainty explicit so a
  team can challenge and revise them.
- **Numbers and judgment together.** Quantitative scripts support human judgment; they
  don't replace it. Every quantitative result is paired with caveats and sensitivity checks.
