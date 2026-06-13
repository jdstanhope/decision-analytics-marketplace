# Decision Analytics Marketplace

A Claude plugin marketplace distributing the **Decision Analytics Toolkit** — four
general-purpose skills that help individuals and small-to-medium teams think more clearly
and decide more rigorously:

- **Structured Analytic Techniques** — Analysis of Competing Hypotheses, Key Assumptions
  Check, Premortem, Devil's Advocacy / Red Team, Indicators & Warnings.
- **Decision Analysis** — weighted scoring (MCDA), Pugh matrices, decision trees,
  expected value, value of information.
- **Modeling & Simulation** — Monte Carlo simulation, sensitivity / tornado analysis,
  scenario planning, forecasting.
- **Data Analysis** — exploratory data analysis, hypothesis testing, correlation &
  regression, visualization.

## Install

In Claude Code or Cowork, add this marketplace once, then install the plugin:

```
/plugin marketplace add YOUR_GITHUB_USERNAME/decision-analytics-marketplace
/plugin install decision-analytics-toolkit@decision-analytics
```

Replace `YOUR_GITHUB_USERNAME` with the account hosting this repo.

To get updates after the author pushes changes:

```
/plugin marketplace update decision-analytics
```

## Requirements

The skills' computational scripts use the standard scientific Python stack:
`numpy`, `pandas`, `scipy`, `matplotlib`, and `statsmodels` (the last is needed only for
regression inference). Install with:

```
pip install numpy pandas scipy matplotlib statsmodels tabulate
```

## What's in the repo

```
decision-analytics-marketplace/
├── .claude-plugin/
│   └── marketplace.json          # the catalog Claude reads
└── decision-analytics-toolkit/   # the plugin itself
    ├── .claude-plugin/plugin.json
    ├── README.md
    └── skills/
        ├── structured-analytic-techniques/
        ├── decision-analysis/
        ├── modeling-simulation/
        └── data-analysis/
```

## License

Released under the [MIT License](./LICENSE) — permissive, BSD-like: anyone may use,
modify, and redistribute it, with attribution and no warranty.
