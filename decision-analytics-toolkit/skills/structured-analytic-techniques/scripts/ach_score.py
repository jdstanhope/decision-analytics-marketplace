#!/usr/bin/env python3
"""
Analysis of Competing Hypotheses (ACH) scorer.

ACH ranks hypotheses by *inconsistency*, not consistency: the most likely hypothesis is
the one with the least evidence arguing against it. This script tallies a weighted
inconsistency score per hypothesis and flags which evidence is most diagnostic (i.e. does
the most to discriminate between hypotheses).

INPUT: a JSON file describing the matrix. Schema:

{
  "hypotheses": ["H1: ...", "H2: ...", "H3: ..."],
  "evidence": [
    {
      "text": "Evidence/argument item",
      "credibility": "high",          # high | medium | low  (weights the item; default medium)
      "ratings": ["C", "I", "N"]      # one rating per hypothesis, same order as "hypotheses"
    }
  ]
}

Ratings:  C = Consistent,  I = Inconsistent,  N = Neutral/Not applicable.
You may also use "II"/"CC" for strongly inconsistent/consistent (double weight).

USAGE:
  python ach_score.py matrix.json
  python ach_score.py matrix.json --out report.md

The lowest inconsistency score = the hypothesis best supported by the evidence.
"""
import argparse
import json
import sys

CRED_WEIGHT = {"high": 1.5, "medium": 1.0, "low": 0.5}
# Inconsistency contributes to the score (higher = worse for that hypothesis).
RATING_VALUE = {
    "I": 1.0, "II": 2.0,    # inconsistent counts against
    "C": 0.0, "CC": 0.0,    # consistency does not earn credit (ACH principle)
    "N": 0.0,
}


def load_matrix(path):
    with open(path) as f:
        data = json.load(f)
    hyps = data["hypotheses"]
    n = len(hyps)
    for i, ev in enumerate(data["evidence"]):
        if len(ev["ratings"]) != n:
            sys.exit(f"Evidence #{i+1} has {len(ev['ratings'])} ratings; expected {n}.")
    return data


def diagnosticity(ratings):
    """How much an evidence item discriminates among hypotheses.
    All-same ratings = not diagnostic (0). A mix of C and I = highly diagnostic."""
    simplified = []
    for r in ratings:
        r = r.upper()
        if r in ("C", "CC"):
            simplified.append("C")
        elif r in ("I", "II"):
            simplified.append("I")
        else:
            simplified.append("N")
    if len(set(simplified)) <= 1:
        return 0.0
    # diagnostic if it has both consistent and inconsistent verdicts
    span = 0.0
    if "C" in simplified and "I" in simplified:
        span = 1.0
    elif "N" in simplified and ("C" in simplified or "I" in simplified):
        span = 0.5
    return span


def score(data):
    hyps = data["hypotheses"]
    n = len(hyps)
    inconsistency = [0.0] * n
    rows = []
    for ev in data["evidence"]:
        w = CRED_WEIGHT.get(ev.get("credibility", "medium").lower(), 1.0)
        for j, r in enumerate(ev["ratings"]):
            inconsistency[j] += w * RATING_VALUE.get(r.upper(), 0.0)
        rows.append({
            "text": ev["text"],
            "credibility": ev.get("credibility", "medium"),
            "diagnosticity": round(w * diagnosticity(ev["ratings"]), 2),
            "ratings": [r.upper() for r in ev["ratings"]],
        })
    ranked = sorted(range(n), key=lambda j: inconsistency[j])
    return hyps, inconsistency, rows, ranked


def render(data, out=None):
    hyps, inconsistency, rows, ranked = score(data)
    L = []
    L.append("# ACH Results\n")
    L.append("## Hypotheses ranked by weighted inconsistency (lower = more likely)\n")
    for rank, j in enumerate(ranked, 1):
        L.append(f"{rank}. **{hyps[j]}** — inconsistency score {inconsistency[j]:.2f}")
    L.append("\n> The best-supported hypothesis is the one the evidence argues against "
             "least. Consistency earns no credit — only inconsistency eliminates.\n")

    L.append("\n## Most diagnostic evidence (drives the conclusion — scrutinize these)\n")
    diag = sorted(rows, key=lambda r: r["diagnosticity"], reverse=True)
    for r in diag:
        if r["diagnosticity"] > 0:
            L.append(f"- ({r['diagnosticity']:.2f}) {r['text']}  "
                     f"[credibility: {r['credibility']}]")
    non_diag = [r for r in rows if r["diagnosticity"] == 0]
    if non_diag:
        L.append("\n_Non-diagnostic items (consistent or neutral across all hypotheses; "
                 "consider removing):_")
        for r in non_diag:
            L.append(f"- {r['text']}")

    L.append("\n## Full matrix\n")
    header = "| Evidence | Cred | " + " | ".join(
        h.split(":")[0].strip() for h in hyps) + " |"
    sep = "|---|---|" + "|".join(["---"] * len(hyps)) + "|"
    L.append(header)
    L.append(sep)
    for r in rows:
        L.append(f"| {r['text']} | {r['credibility']} | " +
                 " | ".join(r["ratings"]) + " |")

    L.append("\n## Next steps")
    L.append("- Pressure-test the top diagnostic items: how solid is each source? Could "
             "any be deception or motivated reporting?")
    L.append("- If the single most diagnostic item were wrong, re-run and see whether the "
             "ranking flips. If it does, that item is the linchpin to verify.")
    text = "\n".join(L)
    if out:
        with open(out, "w") as f:
            f.write(text)
        print(f"Wrote {out}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description="Score an ACH matrix.")
    ap.add_argument("matrix", help="Path to matrix JSON file")
    ap.add_argument("--out", help="Write Markdown report to this path")
    args = ap.parse_args()
    data = load_matrix(args.matrix)
    render(data, args.out)


if __name__ == "__main__":
    main()
