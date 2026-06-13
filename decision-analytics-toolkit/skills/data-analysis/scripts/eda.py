#!/usr/bin/env python3
"""
Exploratory data analysis profiler. Run this FIRST on any dataset.

Profiles a CSV: shape, per-column type, missingness, unique counts, summary stats for
numerics, top categories for categoricals, outlier flags (IQR rule), duplicate rows,
constant columns, and a correlation matrix for numeric columns. Optionally saves
distribution and correlation plots.

USAGE:
  python eda.py data.csv
  python eda.py data.csv --out profile.md --plots-dir ./plots
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAVE_PLT = True
except Exception:
    HAVE_PLT = False


def outlier_count(s):
    s = s.dropna()
    if len(s) < 4:
        return 0, None, None
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((s < lo) | (s > hi)).sum()), lo, hi


def profile(df, out_path, plots_dir):
    L = []
    L.append("# EDA Profile\n")
    L.append(f"Rows: {len(df)}  |  Columns: {df.shape[1]}\n")

    dups = int(df.duplicated().sum())
    if dups:
        L.append(f"> ⚠ {dups} duplicate rows ({dups/len(df)*100:.1f}%).")
    const_cols = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
    if const_cols:
        L.append(f"> ⚠ Constant/near-constant columns: {', '.join(const_cols)}.")

    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in df.columns if c not in num_cols]

    L.append("\n## Columns overview")
    L.append("| Column | Type | Missing % | Unique |")
    L.append("|---|---|---|---|")
    for c in df.columns:
        miss = df[c].isna().mean() * 100
        kind = "numeric" if c in num_cols else "categorical/text"
        L.append(f"| {c} | {kind} | {miss:.1f}% | {df[c].nunique(dropna=True)} |")

    if num_cols:
        L.append("\n## Numeric summary")
        L.append("| Column | mean | std | min | P25 | median | P75 | max | outliers (IQR) |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for c in num_cols:
            s = df[c]
            n_out, _, _ = outlier_count(s)
            L.append(f"| {c} | {s.mean():.3g} | {s.std():.3g} | {s.min():.3g} | "
                     f"{s.quantile(.25):.3g} | {s.median():.3g} | {s.quantile(.75):.3g} | "
                     f"{s.max():.3g} | {n_out} |")
        # skew flags
        skewed = []
        for c in num_cols:
            s = df[c].dropna()
            if len(s) > 8 and s.std() > 0:
                sk = float(((s - s.mean()) ** 3).mean() / (s.std() ** 3))
                if abs(sk) > 1:
                    skewed.append(f"{c} (skew {sk:+.1f})")
        if skewed:
            L.append(f"\n_Notably skewed (consider a transform or robust method): "
                     f"{', '.join(skewed)}._")

    if cat_cols:
        L.append("\n## Categorical / text columns (top values)")
        for c in cat_cols:
            vc = df[c].value_counts(dropna=False).head(5)
            tops = "; ".join(f"{idx!r}: {cnt}" for idx, cnt in vc.items())
            L.append(f"- **{c}** ({df[c].nunique()} unique): {tops}")

    if len(num_cols) >= 2:
        corr = df[num_cols].corr(numeric_only=True)
        L.append("\n## Correlation matrix (Pearson)")
        L.append("| | " + " | ".join(num_cols) + " |")
        L.append("|---|" + "|".join(["---"] * len(num_cols)) + "|")
        for c in num_cols:
            row = " | ".join(f"{corr.loc[c, d]:.2f}" for d in num_cols)
            L.append(f"| **{c}** | {row} |")
        # strongest off-diagonal pairs
        pairs = []
        for i, a in enumerate(num_cols):
            for b in num_cols[i + 1:]:
                pairs.append((a, b, corr.loc[a, b]))
        pairs.sort(key=lambda t: abs(t[2]), reverse=True)
        L.append("\n_Strongest relationships (worth testing, not yet conclusions):_")
        for a, b, r in pairs[:5]:
            L.append(f"- {a} ↔ {b}: r = {r:+.2f}")

    if HAVE_PLT and plots_dir:
        os.makedirs(plots_dir, exist_ok=True)
        for c in num_cols:
            s = df[c].dropna()
            if len(s) < 3:
                continue
            plt.figure(figsize=(5, 3))
            plt.hist(s, bins=min(40, max(10, len(s) // 5)), color="#4C72B0",
                     edgecolor="white")
            plt.title(f"Distribution: {c}"); plt.tight_layout()
            p = os.path.join(plots_dir, f"dist_{c}.png")
            plt.savefig(p, dpi=110); plt.close()
        if len(num_cols) >= 2:
            corr = df[num_cols].corr(numeric_only=True)
            plt.figure(figsize=(1 + len(num_cols), 1 + len(num_cols)))
            plt.imshow(corr, cmap="RdBu", vmin=-1, vmax=1)
            plt.xticks(range(len(num_cols)), num_cols, rotation=45, ha="right")
            plt.yticks(range(len(num_cols)), num_cols)
            plt.colorbar(label="r"); plt.title("Correlation"); plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, "correlation.png"), dpi=110); plt.close()
        L.append(f"\nPlots saved to `{plots_dir}/`.")

    L.append("\n## Suggested next steps")
    L.append("- Resolve any quality flags above (missingness, duplicates, outliers) and "
             "record what you did.")
    L.append("- Treat strong correlations as hypotheses; confirm with an appropriate test "
             "or model (see stats_test.py / regression.py).")
    text = "\n".join(L)
    if out_path:
        with open(out_path, "w") as f:
            f.write(text)
        print(f"Wrote {out_path}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description="Exploratory data analysis profiler.")
    ap.add_argument("csv", help="Path to CSV")
    ap.add_argument("--out", help="Write Markdown profile to this path")
    ap.add_argument("--plots-dir", help="Directory to save distribution/correlation plots")
    args = ap.parse_args()
    try:
        df = pd.read_csv(args.csv)
    except Exception as e:
        sys.exit(f"Could not read CSV: {e}")
    profile(df, args.out, args.plots_dir)


if __name__ == "__main__":
    main()
