#!/usr/bin/env python3
"""
Simple, explainable time-series forecasting with prediction intervals.

Fits three transparent baselines and reports which best fits recent history (via one-step
backtest error), then forecasts forward with an uncertainty band that widens with horizon:
  - linear trend (optionally log-linear for growth that compounds)
  - moving average (flat)
  - simple exponential smoothing

This is intentionally a baseline toolkit, not a heavy forecaster. For strong seasonality or
many related series, recommend a dedicated method instead of overfitting these.

INPUT: a CSV with a value column (one row per period, oldest first), OR a JSON list of
numbers. Period labels optional.

USAGE:
  python forecast.py history.csv --value-col revenue --horizon 6
  python forecast.py series.json --horizon 12 --log --out report.md --plot fan.png
"""
import argparse
import json
import sys

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAVE_PLT = True
except Exception:
    HAVE_PLT = False


def load_series(path, value_col):
    if path.lower().endswith(".json"):
        with open(path) as f:
            data = json.load(f)
        return np.asarray(data, dtype=float)
    import csv
    vals = []
    with open(path) as f:
        reader = csv.DictReader(f)
        col = value_col or reader.fieldnames[-1]
        for row in reader:
            vals.append(float(row[col]))
    return np.asarray(vals, dtype=float)


def linear_fit(y, log=False):
    x = np.arange(len(y))
    yy = np.log(y) if log else y
    a, b = np.polyfit(x, yy, 1)  # slope, intercept
    fit = a * x + b
    resid = yy - fit
    return a, b, resid


def forecast_linear(y, h, log=False):
    a, b, resid = linear_fit(y, log)
    n = len(y)
    fx = np.arange(n, n + h)
    fc = a * fx + b
    sd = np.std(resid, ddof=2) if len(resid) > 2 else np.std(resid)
    # widen interval with horizon
    widen = np.sqrt(1 + np.arange(1, h + 1) / max(n, 1))
    lo, hi = fc - 1.28 * sd * widen, fc + 1.28 * sd * widen  # ~80% interval
    if log:
        return np.exp(fc), np.exp(lo), np.exp(hi)
    return fc, lo, hi


def forecast_ma(y, h, window=3):
    w = min(window, len(y))
    level = np.mean(y[-w:])
    resid = y[w:] - np.array([np.mean(y[i - w:i]) for i in range(w, len(y))]) \
        if len(y) > w else np.array([np.std(y)])
    sd = np.std(resid) if len(resid) else np.std(y)
    fc = np.full(h, level)
    widen = np.sqrt(1 + np.arange(1, h + 1))
    return fc, fc - 1.28 * sd * widen, fc + 1.28 * sd * widen


def forecast_ses(y, h, alpha=0.4):
    level = y[0]
    fitted = [level]
    for t in range(1, len(y)):
        level = alpha * y[t] + (1 - alpha) * level
        fitted.append(level)
    resid = y - np.array(fitted)
    sd = np.std(resid, ddof=1) if len(y) > 1 else 0.0
    fc = np.full(h, level)
    widen = np.sqrt(1 + np.arange(1, h + 1))
    return fc, fc - 1.28 * sd * widen, fc + 1.28 * sd * widen


def backtest_mae(y, method, **kw):
    """One-step-ahead backtest mean absolute error over the last min(len/3, 8) points."""
    n = len(y)
    k = max(2, min(n // 3, 8))
    errs = []
    for i in range(n - k, n):
        train = y[:i]
        if len(train) < 3:
            continue
        fc, _, _ = method(train, 1, **kw)
        errs.append(abs(fc[0] - y[i]))
    return float(np.mean(errs)) if errs else float("nan")


def render(y, h, log, out_path, plot_path):
    methods = {
        "linear": (forecast_linear, {"log": log}),
        "moving_average": (forecast_ma, {}),
        "exp_smoothing": (forecast_ses, {}),
    }
    scores = {name: backtest_mae(y, fn, **kw) for name, (fn, kw) in methods.items()}
    best = min(scores, key=lambda k: (np.inf if np.isnan(scores[k]) else scores[k]))
    fn, kw = methods[best]
    fc, lo, hi = fn(y, h, **kw)

    L = []
    L.append("# Forecast Results\n")
    L.append(f"History points: {len(y)}  |  Horizon: {h} periods\n")
    L.append("## Backtest (one-step mean absolute error — lower is better)")
    for name, s in sorted(scores.items(), key=lambda kv: kv[1]):
        mark = "  ← selected" if name == best else ""
        L.append(f"- {name}: {s:.3f}{mark}")
    L.append(f"\n## Forecast using **{best}** (≈80% interval)\n")
    L.append("| Period ahead | Forecast | Low | High |")
    L.append("|---|---|---|---|")
    for i in range(h):
        L.append(f"| +{i+1} | {fc[i]:.2f} | {lo[i]:.2f} | {hi[i]:.2f} |")
    L.append("\n## Caveats")
    L.append("- The interval widens with horizon; treat far-out points as indicative only.")
    L.append("- These baselines assume no seasonality. If the data has a weekly/quarterly "
             "cycle, these will miss it — use a seasonal method instead.")
    L.append("- A trend continuing is an assumption, not a fact. Pair with the "
             "structured-analytic-techniques Key Assumptions Check for anything important.")

    if HAVE_PLT and plot_path:
        plt.figure(figsize=(8, 4))
        hx = np.arange(len(y))
        fx = np.arange(len(y), len(y) + h)
        plt.plot(hx, y, "-o", color="#4C72B0", label="history")
        plt.plot(fx, fc, "-o", color="#C44E52", label=f"forecast ({best})")
        plt.fill_between(fx, lo, hi, color="#C44E52", alpha=0.2, label="80% interval")
        plt.legend(); plt.title("Forecast"); plt.tight_layout()
        plt.savefig(plot_path, dpi=120); plt.close()
        L.append(f"\nFan chart saved to `{plot_path}`.")

    text = "\n".join(L)
    if out_path:
        with open(out_path, "w") as f:
            f.write(text)
        print(f"Wrote {out_path}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description="Simple time-series forecasting.")
    ap.add_argument("data", help="CSV or JSON history (oldest first)")
    ap.add_argument("--value-col", help="Value column name (CSV)")
    ap.add_argument("--horizon", type=int, default=6)
    ap.add_argument("--log", action="store_true", help="Log-linear trend (compounding growth)")
    ap.add_argument("--out", help="Write Markdown report")
    ap.add_argument("--plot", help="Save fan chart PNG")
    args = ap.parse_args()
    y = load_series(args.data, args.value_col)
    if len(y) < 4:
        sys.exit("Need at least 4 history points.")
    render(y, args.horizon, args.log, args.out, args.plot)


if __name__ == "__main__":
    main()
