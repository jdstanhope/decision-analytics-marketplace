#!/usr/bin/env python3
"""
Hypothesis tests for comparing groups and testing associations, with assumption checks,
effect sizes, and confidence intervals — reported in plain language.

Supports:
  ttest        two-group difference in means (Welch) + Mann-Whitney fallback
  anova        3+ group difference in means + Kruskal-Wallis fallback
  chisquare    association between two categorical variables
  correlation  Pearson + Spearman between two numerics

USAGE:
  python stats_test.py data.csv --test ttest      --value conv --group variant
  python stats_test.py data.csv --test anova      --value score --group segment
  python stats_test.py data.csv --test chisquare  --col1 channel --col2 converted
  python stats_test.py data.csv --test correlation --col1 spend --col2 signups
  (add --out report.md to save)
"""
import argparse
import sys

import numpy as np
import pandas as pd
from scipy import stats


def cohens_d(a, b):
    na, nb = len(a), len(b)
    sp = np.sqrt(((na - 1) * np.var(a, ddof=1) + (nb - 1) * np.var(b, ddof=1)) /
                 (na + nb - 2))
    return (np.mean(a) - np.mean(b)) / sp if sp > 0 else 0.0


def mean_diff_ci(a, b, conf=0.95):
    na, nb = len(a), len(b)
    diff = np.mean(a) - np.mean(b)
    se = np.sqrt(np.var(a, ddof=1) / na + np.var(b, ddof=1) / nb)
    dfree = (np.var(a, ddof=1)/na + np.var(b, ddof=1)/nb) ** 2 / (
        (np.var(a, ddof=1)/na) ** 2 / (na - 1) + (np.var(b, ddof=1)/nb) ** 2 / (nb - 1))
    t = stats.t.ppf((1 + conf) / 2, dfree)
    return diff, diff - t * se, diff + t * se


def interpret_d(d):
    ad = abs(d)
    return ("negligible" if ad < 0.2 else "small" if ad < 0.5 else
            "medium" if ad < 0.8 else "large")


def ttest(df, value, group, L):
    groups = df[group].dropna().unique()
    if len(groups) != 2:
        sys.exit(f"ttest needs exactly 2 groups; '{group}' has {len(groups)}.")
    a = df[df[group] == groups[0]][value].dropna().values
    b = df[df[group] == groups[1]][value].dropna().values
    L.append(f"# Two-group comparison: {value} by {group}\n")
    L.append(f"- {groups[0]}: n={len(a)}, mean={np.mean(a):.4g}, sd={np.std(a, ddof=1):.4g}")
    L.append(f"- {groups[1]}: n={len(b)}, mean={np.mean(b):.4g}, sd={np.std(b, ddof=1):.4g}")
    # normality (Shapiro) on each group if small-ish
    norm_ok = True
    for name, g in [(groups[0], a), (groups[1], b)]:
        if 3 <= len(g) <= 5000:
            p = stats.shapiro(g).pvalue
            if p < 0.05:
                norm_ok = False
    t, p = stats.ttest_ind(a, b, equal_var=False)
    diff, lo, hi = mean_diff_ci(a, b)
    d = cohens_d(a, b)
    L.append(f"\n**Welch t-test:** t={t:.3f}, p={p:.4f}")
    L.append(f"**Difference in means ({groups[0]} − {groups[1]}):** {diff:+.4g} "
             f"(95% CI {lo:+.4g} to {hi:+.4g})")
    L.append(f"**Effect size (Cohen's d):** {d:+.2f} ({interpret_d(d)})")
    u, pu = stats.mannwhitneyu(a, b, alternative="two-sided")
    L.append(f"**Mann–Whitney U (rank-based, robust):** U={u:.0f}, p={pu:.4f}")
    if not norm_ok:
        L.append("\n> ⚠ A group departs from normality (Shapiro p<0.05). With moderate n "
                 "the t-test is fairly robust, but prefer the Mann–Whitney result if n is "
                 "small or the data is heavily skewed.")
    verdict = "a statistically detectable" if p < 0.05 else "no statistically detectable"
    L.append(f"\n**Plain-language read:** There is {verdict} difference at α=0.05. The best "
             f"estimate of the gap is {diff:+.4g} ({groups[0]} minus {groups[1]}); the "
             f"true gap is plausibly between {lo:+.4g} and {hi:+.4g}. Judge whether that "
             f"range is practically meaningful, not just whether p<0.05.")


def anova(df, value, group, L):
    groups = [g for g in df[group].dropna().unique()]
    samples = [df[df[group] == g][value].dropna().values for g in groups]
    L.append(f"# Multi-group comparison: {value} across {group}\n")
    for g, s in zip(groups, samples):
        L.append(f"- {g}: n={len(s)}, mean={np.mean(s):.4g}, sd={np.std(s, ddof=1):.4g}")
    f, p = stats.f_oneway(*samples)
    h, ph = stats.kruskal(*samples)
    # eta-squared effect size
    grand = np.concatenate(samples)
    ss_between = sum(len(s) * (np.mean(s) - np.mean(grand)) ** 2 for s in samples)
    ss_total = np.sum((grand - np.mean(grand)) ** 2)
    eta2 = ss_between / ss_total if ss_total > 0 else 0
    L.append(f"\n**One-way ANOVA:** F={f:.3f}, p={p:.4f}")
    L.append(f"**Kruskal–Wallis (robust):** H={h:.3f}, p={ph:.4f}")
    L.append(f"**Effect size (η²):** {eta2:.3f} "
             f"({'large' if eta2>0.14 else 'medium' if eta2>0.06 else 'small'} share of "
             f"variance explained by group)")
    verdict = "at least one group differs" if p < 0.05 else "no detectable difference"
    L.append(f"\n**Plain-language read:** {verdict} at α=0.05. ANOVA only says *some* group "
             f"differs — follow up with pairwise comparisons (and correct for multiple "
             f"tests) to see which.")


def chisquare(df, col1, col2, L):
    table = pd.crosstab(df[col1], df[col2])
    chi2, p, dof, exp = stats.chi2_contingency(table)
    n = table.values.sum()
    k = min(table.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * k)) if k > 0 else 0
    L.append(f"# Association: {col1} vs {col2}\n")
    L.append("Contingency table:\n")
    L.append(table.to_markdown())
    L.append(f"\n**Chi-square:** χ²={chi2:.3f}, dof={dof}, p={p:.4f}")
    L.append(f"**Effect size (Cramér's V):** {cramers_v:.3f} "
             f"({'strong' if cramers_v>0.5 else 'moderate' if cramers_v>0.3 else 'weak'})")
    if (exp < 5).any():
        L.append("\n> ⚠ Some expected cell counts < 5; chi-square may be unreliable. "
                 "Consider Fisher's exact test (2×2) or combining sparse categories.")
    verdict = "are associated" if p < 0.05 else "show no detectable association"
    L.append(f"\n**Plain-language read:** {col1} and {col2} {verdict} at α=0.05. "
             f"Association is not causation — a lurking variable could drive both.")


def correlation(df, col1, col2, L):
    sub = df[[col1, col2]].dropna()
    x, y = sub[col1].values, sub[col2].values
    r, pr = stats.pearsonr(x, y)
    rho, prho = stats.spearmanr(x, y)
    # CI for pearson r via Fisher z
    n = len(x)
    z = np.arctanh(r)
    se = 1 / np.sqrt(n - 3)
    lo, hi = np.tanh(z - 1.96 * se), np.tanh(z + 1.96 * se)
    L.append(f"# Correlation: {col1} vs {col2}\n")
    L.append(f"n = {n}")
    L.append(f"\n**Pearson r:** {r:+.3f} (95% CI {lo:+.3f} to {hi:+.3f}), p={pr:.4f}")
    L.append(f"**Spearman ρ (rank-based, robust to outliers/nonlinearity):** {rho:+.3f}, "
             f"p={prho:.4f}")
    L.append(f"**Shared variance (r²):** {r**2*100:.1f}%")
    strength = ("negligible" if abs(r) < 0.1 else "weak" if abs(r) < 0.3 else
                "moderate" if abs(r) < 0.5 else "strong")
    L.append(f"\n**Plain-language read:** a {strength} "
             f"{'positive' if r>0 else 'negative'} linear relationship. If Pearson and "
             f"Spearman disagree, the relationship is likely nonlinear or outlier-driven — "
             f"plot it. Correlation does not imply causation.")


def main():
    ap = argparse.ArgumentParser(description="Hypothesis tests with effect sizes.")
    ap.add_argument("csv")
    ap.add_argument("--test", required=True,
                    choices=["ttest", "anova", "chisquare", "correlation"])
    ap.add_argument("--value"); ap.add_argument("--group")
    ap.add_argument("--col1"); ap.add_argument("--col2")
    ap.add_argument("--out")
    args = ap.parse_args()
    df = pd.read_csv(args.csv)
    L = []
    if args.test == "ttest":
        ttest(df, args.value, args.group, L)
    elif args.test == "anova":
        anova(df, args.value, args.group, L)
    elif args.test == "chisquare":
        chisquare(df, args.col1, args.col2, L)
    elif args.test == "correlation":
        correlation(df, args.col1, args.col2, L)
    text = "\n".join(L)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"Wrote {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
