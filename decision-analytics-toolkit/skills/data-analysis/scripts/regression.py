#!/usr/bin/env python3
"""
Linear and logistic regression with coefficients, confidence intervals, fit, and
diagnostics — interpreted in plain language.

  linear    continuous outcome; reports coefficients (with 95% CI), R²/adjusted R²,
            residual diagnostics, and VIF multicollinearity check.
  logistic  binary outcome; reports coefficients as odds ratios (with 95% CI), pseudo-R²,
            and accuracy.

Uses statsmodels if available (for proper inference); otherwise falls back to numpy/scipy
for linear regression.

USAGE:
  python regression.py data.csv --type linear   --y signups --x spend channel_score
  python regression.py data.csv --type logistic --y converted --x spend visits
  (add --out report.md to save)
"""
import argparse
import sys

import numpy as np
import pandas as pd

try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    HAVE_SM = True
except Exception:
    HAVE_SM = False

from scipy import stats


def build(df, y, xs):
    sub = df[[y] + xs].dropna().copy()
    if len(sub) <= len(xs) + 1:
        sys.exit("Not enough complete rows for the number of predictors.")
    return sub


def vif_report(sub, xs, L):
    """Variance inflation factors — flag multicollinearity (numeric predictors only)."""
    num_xs = [x for x in xs if np.issubdtype(sub[x].dropna().dtype, np.number)]
    if len(num_xs) < 2:
        return
    L.append("\n**Multicollinearity (VIF; >5 is concerning, >10 serious):**")
    X = sub[num_xs].values
    for i, name in enumerate(num_xs):
        others = np.delete(X, i, axis=1)
        others = np.column_stack([np.ones(len(others)), others])
        coef, *_ = np.linalg.lstsq(others, X[:, i], rcond=None)
        pred = others @ coef
        ss_res = np.sum((X[:, i] - pred) ** 2)
        ss_tot = np.sum((X[:, i] - np.mean(X[:, i])) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        vif = 1 / (1 - r2) if r2 < 1 else float("inf")
        flag = "  ⚠" if vif > 5 else ""
        L.append(f"- {name}: VIF={vif:.2f}{flag}")


def linear(sub, y, xs, L):
    L.append(f"# Linear regression: {y} ~ {' + '.join(xs)}\n")
    L.append(f"Observations: {len(sub)}\n")
    if HAVE_SM:
        formula = f"Q('{y}') ~ " + " + ".join(f"Q('{x}')" for x in xs)
        model = smf.ols(formula, data=sub).fit()
        L.append(f"**R²:** {model.rsquared:.3f}  |  **Adjusted R²:** "
                 f"{model.rsquared_adj:.3f}  |  **F p-value:** {model.f_pvalue:.4g}\n")
        ci = model.conf_int()
        L.append("| Term | Coef | 95% CI | p-value |")
        L.append("|---|---|---|---|")
        for term in model.params.index:
            lo, hi = ci.loc[term]
            L.append(f"| {term} | {model.params[term]:+.4g} | "
                     f"[{lo:+.4g}, {hi:+.4g}] | {model.pvalues[term]:.4f} |")
        resid = model.resid
        # diagnostics
        L.append("\n**Diagnostics:**")
        if 3 <= len(resid) <= 5000:
            sp = stats.shapiro(resid).pvalue
            L.append(f"- Residual normality (Shapiro p={sp:.3f}): "
                     f"{'ok' if sp>0.05 else '⚠ non-normal residuals'}")
        # Breusch-Pagan-ish: correlation of |resid| with fitted
        bp = np.corrcoef(np.abs(resid), model.fittedvalues)[0, 1]
        L.append(f"- Heteroscedasticity (|resid| vs fitted r={bp:+.2f}): "
                 f"{'ok' if abs(bp)<0.3 else '⚠ variance may grow with fitted value'}")
        infl = model.get_influence().cooks_distance[0]
        n_inf = int((infl > 4 / len(sub)).sum())
        L.append(f"- Influential points (Cook's distance): {n_inf} flagged "
                 f"{'(check these rows)' if n_inf else ''}")
        vif_report(sub, xs, L)
        L.append(f"\n**Plain-language read:** the model explains "
                 f"{model.rsquared*100:.0f}% of the variation in {y}. Each coefficient is "
                 f"the change in {y} per one-unit increase in that predictor, holding the "
                 f"others fixed. Trust coefficients whose CI excludes 0; treat the rest as "
                 f"unestablished. This is association, not proven causation.")
    else:
        # numpy fallback (numeric predictors only)
        num_xs = [x for x in xs if np.issubdtype(sub[x].dropna().dtype, np.number)]
        X = np.column_stack([np.ones(len(sub))] + [sub[x].values for x in num_xs])
        yv = sub[y].values
        beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
        pred = X @ beta
        ss_res = np.sum((yv - pred) ** 2)
        ss_tot = np.sum((yv - np.mean(yv)) ** 2)
        r2 = 1 - ss_res / ss_tot
        L.append(f"**R²:** {r2:.3f}  _(statsmodels not installed; basic fit, no p-values)_\n")
        L.append("| Term | Coef |")
        L.append("|---|---|")
        L.append(f"| intercept | {beta[0]:+.4g} |")
        for name, b in zip(num_xs, beta[1:]):
            L.append(f"| {name} | {b:+.4g} |")
        L.append("\n_Install statsmodels for confidence intervals and diagnostics._")


def logistic(sub, y, xs, L):
    L.append(f"# Logistic regression: {y} ~ {' + '.join(xs)}\n")
    L.append(f"Observations: {len(sub)}\n")
    if not HAVE_SM:
        sys.exit("Logistic regression requires statsmodels. Install it and retry.")
    formula = f"Q('{y}') ~ " + " + ".join(f"Q('{x}')" for x in xs)
    model = smf.logit(formula, data=sub).fit(disp=False)
    ci = model.conf_int()
    L.append(f"**Pseudo-R² (McFadden):** {model.prsquared:.3f}\n")
    L.append("| Term | Coef | Odds ratio | OR 95% CI | p-value |")
    L.append("|---|---|---|---|---|")
    for term in model.params.index:
        lo, hi = ci.loc[term]
        L.append(f"| {term} | {model.params[term]:+.3g} | {np.exp(model.params[term]):.3f} "
                 f"| [{np.exp(lo):.3f}, {np.exp(hi):.3f}] | {model.pvalues[term]:.4f} |")
    pred = (model.predict(sub) > 0.5).astype(int)
    acc = (pred == sub[y].astype(int)).mean()
    L.append(f"\n**In-sample accuracy:** {acc*100:.1f}% "
             f"(optimistic — validate on held-out data for a real estimate).")
    L.append(f"\n**Plain-language read:** an odds ratio >1 means the predictor raises the "
             f"odds of {y}=1; <1 lowers it, holding others fixed. Trust ORs whose CI "
             f"excludes 1. Association, not proven causation.")


def main():
    ap = argparse.ArgumentParser(description="Linear/logistic regression with diagnostics.")
    ap.add_argument("csv")
    ap.add_argument("--type", choices=["linear", "logistic"], default="linear")
    ap.add_argument("--y", required=True)
    ap.add_argument("--x", nargs="+", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    df = pd.read_csv(args.csv)
    sub = build(df, args.y, args.x)
    L = []
    if args.type == "linear":
        linear(sub, args.y, args.x, L)
    else:
        logistic(sub, args.y, args.x, L)
    text = "\n".join(L)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"Wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
