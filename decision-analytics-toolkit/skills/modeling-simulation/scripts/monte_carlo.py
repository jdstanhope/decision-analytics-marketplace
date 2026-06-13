#!/usr/bin/env python3
"""
Monte Carlo simulation with percentiles, threshold probabilities, a one-at-a-time tornado,
and driver ranking (rank correlation).

INPUT JSON schema:

{
  "inputs": {
    "units":      {"dist": "triangular", "args": [800, 1000, 1400]},
    "price":      {"dist": "normal",     "args": [50, 5]},
    "unit_cost":  {"dist": "pert",       "args": [18, 22, 30]},
    "fixed_cost": {"dist": "const",      "args": [15000]}
  },
  "output": "units * price - units * unit_cost - fixed_cost",
  "thresholds": [{"label": "loss", "expr": "output < 0"},
                 {"label": "above 100k", "expr": "output > 100000"}],
  "iterations": 20000,        # optional, default 20000
  "seed": 42                  # optional
}

Supported dists (args):
  const(value) | uniform(low, high) | normal(mean, sd) | lognormal(mean, sd of underlying normal)
  triangular(low, mode, high) | pert(low, mode, high) | bernoulli(p) | poisson(lam)
  beta(a, b) | binomial(n, p)

The "output" expression and threshold "expr" may use any input name plus the word
"output" (in thresholds). Only arithmetic and comparison operators are allowed.

USAGE:
  python monte_carlo.py model.json
  python monte_carlo.py model.json --out report.md --hist hist.png --tornado tornado.png
"""
import argparse
import ast
import json
import operator
import sys

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAVE_PLT = True
except Exception:
    HAVE_PLT = False

# ---- safe expression evaluation -------------------------------------------------
_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod}
_CMP = {ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt,
        ast.GtE: operator.ge, ast.Eq: operator.eq, ast.NotEq: operator.ne}
_BOOL = {ast.And: np.logical_and, ast.Or: np.logical_or}


def _eval(node, env):
    if isinstance(node, ast.Expression):
        return _eval(node.body, env)
    if isinstance(node, ast.BinOp):
        return _BINOPS[type(node.op)](_eval(node.left, env), _eval(node.right, env))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval(node.operand, env)
    if isinstance(node, ast.Compare):
        left = _eval(node.left, env)
        result = None
        for op, comp in zip(node.ops, node.comparators):
            r = _CMP[type(op)](left, _eval(comp, env))
            result = r if result is None else np.logical_and(result, r)
            left = _eval(comp, env)
        return result
    if isinstance(node, ast.BoolOp):
        vals = [_eval(v, env) for v in node.values]
        out = vals[0]
        for v in vals[1:]:
            out = _BOOL[type(node.op)](out, v)
        return out
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise ValueError(f"Unknown name in expression: {node.id}")
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn = {"min": np.minimum, "max": np.maximum, "abs": np.abs}.get(node.func.id)
        if fn:
            return fn(*[_eval(a, env) for a in node.args])
    raise ValueError(f"Unsupported expression element: {ast.dump(node)}")


def evaluate(expr, env):
    return _eval(ast.parse(expr, mode="eval"), env)


# ---- sampling -------------------------------------------------------------------
def sample(spec, n, rng):
    d = spec["dist"].lower()
    a = spec.get("args", [])
    if d == "const":
        return np.full(n, a[0], dtype=float)
    if d == "uniform":
        return rng.uniform(a[0], a[1], n)
    if d == "normal":
        return rng.normal(a[0], a[1], n)
    if d == "lognormal":
        return rng.lognormal(a[0], a[1], n)
    if d == "triangular":
        return rng.triangular(a[0], a[1], a[2], n)
    if d == "pert":
        lo, mode, hi = a
        if hi == lo:
            return np.full(n, lo, dtype=float)
        alpha = 1 + 4 * (mode - lo) / (hi - lo)
        beta_ = 1 + 4 * (hi - mode) / (hi - lo)
        return lo + rng.beta(alpha, beta_, n) * (hi - lo)
    if d == "bernoulli":
        return (rng.random(n) < a[0]).astype(float)
    if d == "poisson":
        return rng.poisson(a[0], n).astype(float)
    if d == "beta":
        return rng.beta(a[0], a[1], n)
    if d == "binomial":
        return rng.binomial(a[0], a[1], n).astype(float)
    sys.exit(f"Unknown distribution: {d}")


def baseline_value(spec):
    """Representative central value of an input, for the tornado."""
    d = spec["dist"].lower()
    a = spec.get("args", [])
    if d == "const":
        return a[0]
    if d in ("uniform",):
        return (a[0] + a[1]) / 2
    if d == "normal":
        return a[0]
    if d == "lognormal":
        return float(np.exp(a[0] + a[1] ** 2 / 2))
    if d in ("triangular", "pert"):
        return a[1]
    if d == "bernoulli":
        return a[0]
    if d == "poisson":
        return a[0]
    if d == "beta":
        return a[0] / (a[0] + a[1])
    if d == "binomial":
        return a[0] * a[1]
    return 0.0


def low_high(spec, lo_q=0.10, hi_q=0.90, rng=None):
    """P10/P90 of an input for the tornado swing."""
    s = sample(spec, 20000, rng or np.random.default_rng(0))
    return np.quantile(s, lo_q), np.quantile(s, hi_q)


def run(data, hist_path=None, tornado_path=None):
    rng = np.random.default_rng(data.get("seed"))
    n = int(data.get("iterations", 20000))
    names = list(data["inputs"].keys())
    samples = {k: sample(v, n, rng) for k, v in data["inputs"].items()}
    out = evaluate(data["output"], dict(samples))
    out = np.asarray(out, dtype=float)

    pct = {q: float(np.percentile(out, q)) for q in (5, 10, 25, 50, 75, 90, 95)}
    summary = {
        "mean": float(np.mean(out)), "std": float(np.std(out)),
        "min": float(np.min(out)), "max": float(np.max(out)), "percentiles": pct,
    }
    # convergence: split-half mean stability
    half = n // 2
    conv = abs(np.mean(out[:half]) - np.mean(out[half:])) / (abs(np.mean(out)) + 1e-9)

    thresholds = []
    for t in data.get("thresholds", []):
        env = dict(samples)
        env["output"] = out
        prob = float(np.mean(evaluate(t["expr"], env)))
        thresholds.append((t["label"], t["expr"], prob))

    # driver ranking: spearman-ish rank correlation of each input with output
    def rankcorr(x, y):
        rx = np.argsort(np.argsort(x))
        ry = np.argsort(np.argsort(y))
        return float(np.corrcoef(rx, ry)[0, 1])
    drivers = sorted(((k, rankcorr(samples[k], out)) for k in names),
                     key=lambda kv: abs(kv[1]), reverse=True)

    # tornado: swing each input low->high holding others at baseline
    base_env = {k: baseline_value(v) for k, v in data["inputs"].items()}
    base_out = float(evaluate(data["output"], dict(base_env)))
    tornado = []
    for k, spec in data["inputs"].items():
        lo, hi = low_high(spec, rng=rng)
        e_lo = dict(base_env); e_lo[k] = lo
        e_hi = dict(base_env); e_hi[k] = hi
        v_lo = float(evaluate(data["output"], e_lo))
        v_hi = float(evaluate(data["output"], e_hi))
        tornado.append((k, v_lo, v_hi, abs(v_hi - v_lo)))
    tornado.sort(key=lambda r: r[3], reverse=True)

    if HAVE_PLT and hist_path:
        plt.figure(figsize=(7, 4))
        plt.hist(out, bins=60, color="#4C72B0", edgecolor="white")
        plt.axvline(pct[50], color="k", ls="--", label=f"median {pct[50]:.0f}")
        plt.axvline(pct[10], color="#C44E52", ls=":", label=f"P10 {pct[10]:.0f}")
        plt.axvline(pct[90], color="#C44E52", ls=":", label=f"P90 {pct[90]:.0f}")
        plt.title("Monte Carlo outcome distribution"); plt.legend(); plt.tight_layout()
        plt.savefig(hist_path, dpi=120); plt.close()
    if HAVE_PLT and tornado_path:
        plt.figure(figsize=(7, 0.5 * len(tornado) + 1.5))
        labels = [t[0] for t in tornado][::-1]
        widths = [t[3] for t in tornado][::-1]
        plt.barh(labels, widths, color="#55A868")
        plt.xlabel("Output swing (P10→P90 of input)")
        plt.title("Tornado: sensitivity to each input"); plt.tight_layout()
        plt.savefig(tornado_path, dpi=120); plt.close()

    return summary, conv, thresholds, drivers, tornado, base_out


def render(data, out_path, hist_path, tornado_path):
    summary, conv, thresholds, drivers, tornado, base_out = run(
        data, hist_path, tornado_path)
    p = summary["percentiles"]
    L = []
    L.append("# Monte Carlo Results\n")
    L.append(f"Iterations: {data.get('iterations', 20000)}  |  "
             f"Output: `{data['output']}`\n")
    L.append("## Outcome distribution")
    L.append(f"- Mean: {summary['mean']:.2f}")
    L.append(f"- Median (P50): {p[50]:.2f}")
    L.append(f"- 80% interval (P10–P90): {p[10]:.2f} to {p[90]:.2f}")
    L.append(f"- 90% interval (P5–P95): {p[5]:.2f} to {p[95]:.2f}")
    L.append(f"- Std dev: {summary['std']:.2f}  |  Range: {summary['min']:.2f} to "
             f"{summary['max']:.2f}")
    flag = "OK" if conv < 0.01 else "consider more iterations"
    L.append(f"- Convergence (split-half mean drift): {conv*100:.2f}%  ({flag})")
    if thresholds:
        L.append("\n## Threshold probabilities")
        for label, expr, prob in thresholds:
            L.append(f"- P({label}) = **{prob*100:.1f}%**  _(`{expr}`)_")
    L.append("\n## Drivers (rank correlation of input with output — what creates the spread)")
    for k, c in drivers:
        L.append(f"- {k}: {c:+.2f}")
    L.append("\n## Tornado (one-at-a-time swing, P10→P90 of each input)")
    L.append(f"_Baseline output at central inputs: {base_out:.2f}_\n")
    L.append("| Input | output @ low | output @ high | swing |")
    L.append("|---|---|---|---|")
    for k, lo, hi, w in tornado:
        L.append(f"| {k} | {lo:.2f} | {hi:.2f} | {w:.2f} |")
    L.append("\nThe widest swings are where pinning down the estimate pays off most.")
    if hist_path:
        L.append(f"\nHistogram saved to `{hist_path}`.")
    if tornado_path:
        L.append(f"Tornado chart saved to `{tornado_path}`.")
    text = "\n".join(L)
    if out_path:
        with open(out_path, "w") as f:
            f.write(text)
        print(f"Wrote {out_path}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description="Monte Carlo simulation.")
    ap.add_argument("model", help="Path to model JSON")
    ap.add_argument("--out", help="Write Markdown report to this path")
    ap.add_argument("--hist", help="Save histogram PNG to this path")
    ap.add_argument("--tornado", help="Save tornado chart PNG to this path")
    args = ap.parse_args()
    with open(args.model) as f:
        data = json.load(f)
    render(data, args.out, args.hist, args.tornado)


if __name__ == "__main__":
    main()
