#!/usr/bin/env python3
"""
Weighted multi-criteria decision scoring (MCDA) with built-in sensitivity analysis.
Also supports Pugh-matrix mode.

INPUT JSON schema:

{
  "criteria": [
    {"name": "Cost",        "weight": 30, "benefit": false},
    {"name": "Performance", "weight": 40, "benefit": true},
    {"name": "Support",     "weight": 30, "benefit": true}
  ],
  "options": [
    {"name": "Vendor A", "scores": {"Cost": 4, "Performance": 3, "Support": 5}},
    {"name": "Vendor B", "scores": {"Cost": 2, "Performance": 5, "Support": 4}}
  ],
  "scale_max": 5            # optional, default 5; used only for reporting
}

- weight: any positive numbers; they are normalized to sum to 1.
- benefit: true (default) if a higher raw score is better. Set false when a higher raw
  score is WORSE (e.g. Cost rated where 5 = most expensive); the script then inverts it
  within the scale so it counts against the option.
  SIMPLEST APPROACH: score every criterion so that higher = better (e.g. Cost as a
  "value for money" rating where 5 = cheapest) and omit "benefit" entirely.

USAGE:
  python weighted_score.py model.json
  python weighted_score.py model.json --mode pugh --baseline "Vendor A"
  python weighted_score.py model.json --out report.md
"""
import argparse
import json
import sys
from itertools import combinations


def normalize_weights(criteria):
    total = sum(c["weight"] for c in criteria)
    if total <= 0:
        sys.exit("Weights must sum to a positive number.")
    return {c["name"]: c["weight"] / total for c in criteria}


def oriented(score, benefit, scale_max):
    """Higher-is-better orientation. If benefit is False, invert within the scale."""
    if benefit:
        return score
    return (scale_max + 1) - score  # invert on a 1..scale_max scale


def weighted_totals(data):
    scale_max = data.get("scale_max", 5)
    w = normalize_weights(data["criteria"])
    benefit = {c["name"]: c.get("benefit", True) for c in data["criteria"]}
    totals = {}
    breakdown = {}
    for opt in data["options"]:
        t = 0.0
        bd = {}
        for c in data["criteria"]:
            name = c["name"]
            raw = opt["scores"][name]
            contrib = w[name] * oriented(raw, benefit[name], scale_max)
            bd[name] = contrib
            t += contrib
        totals[opt["name"]] = t
        breakdown[opt["name"]] = bd
    return totals, breakdown, w


def pugh(data, baseline):
    names = [o["name"] for o in data["options"]]
    if baseline not in names:
        sys.exit(f"Baseline '{baseline}' not among options: {names}")
    base = next(o for o in data["options"] if o["name"] == baseline)
    scale_max = data.get("scale_max", 5)
    benefit = {c["name"]: c.get("benefit", True) for c in data["criteria"]}
    results = {}
    for opt in data["options"]:
        plus = minus = same = 0
        for c in data["criteria"]:
            name = c["name"]
            a = oriented(opt["scores"][name], benefit[name], scale_max)
            b = oriented(base["scores"][name], benefit[name], scale_max)
            if a > b:
                plus += 1
            elif a < b:
                minus += 1
            else:
                same += 1
        results[opt["name"]] = {"+": plus, "-": minus, "0": same, "net": plus - minus}
    return results


def sensitivity(data):
    """For each close pair, report how much total weight shift would flip the ranking,
    and which single criterion most drives the gap."""
    totals, breakdown, w = weighted_totals(data)
    ranked = sorted(totals, key=totals.get, reverse=True)
    notes = []
    for a, b in combinations(ranked, 2):
        gap = totals[a] - totals[b]
        if abs(gap) < 0.15:  # close enough to be worth a flag (on 0..scale_max-ish range)
            # which criterion contributes most to a's lead?
            diffs = {c["name"]: breakdown[a][c["name"]] - breakdown[b][c["name"]]
                     for c in data["criteria"]}
            driver = max(diffs, key=lambda k: abs(diffs[k]))
            notes.append(
                f"- **{a}** vs **{b}** are close (gap {gap:+.3f}). The decisive criterion "
                f"is **{driver}** (contributes {diffs[driver]:+.3f} to the gap). A modest "
                f"change in its weight or in either option's {driver} score could flip them.")
    if not notes:
        notes.append("- No pairs are within a close margin; the ranking is fairly robust "
                     "to small input changes.")
    return ranked, notes


def render(data, mode, baseline, out):
    L = []
    if mode == "pugh":
        L.append("# Pugh Matrix Results\n")
        L.append(f"Baseline: **{baseline}**  (+ = better than baseline, - = worse)\n")
        res = pugh(data, baseline)
        ranked = sorted(res, key=lambda n: res[n]["net"], reverse=True)
        L.append("| Option | + | 0 | - | Net |")
        L.append("|---|---|---|---|---|")
        for n in ranked:
            r = res[n]
            L.append(f"| {n} | {r['+']} | {r['0']} | {r['-']} | {r['net']:+d} |")
        L.append(f"\n**Leader: {ranked[0]}** (net {res[ranked[0]]['net']:+d}). Pugh is a "
                 "coarse screen — confirm the top contenders with weighted scoring.")
    else:
        totals, breakdown, w = weighted_totals(data)
        ranked, notes = sensitivity(data)
        L.append("# Weighted Scoring Results\n")
        L.append("## Normalized weights")
        for c in data["criteria"]:
            L.append(f"- {c['name']}: {w[c['name']]*100:.1f}%"
                     + ("" if c.get("benefit", True) else "  (lower raw score is better)"))
        L.append("\n## Ranking")
        L.append("| Rank | Option | Weighted score |")
        L.append("|---|---|---|")
        for i, n in enumerate(ranked, 1):
            L.append(f"| {i} | {n} | {totals[n]:.3f} |")
        L.append(f"\n**Recommended: {ranked[0]}** (score {totals[ranked[0]]:.3f}).")
        L.append("\n## Contribution breakdown")
        crit_names = [c["name"] for c in data["criteria"]]
        L.append("| Option | " + " | ".join(crit_names) + " | Total |")
        L.append("|---|" + "|".join(["---"] * (len(crit_names) + 1)) + "|")
        for n in ranked:
            cells = " | ".join(f"{breakdown[n][c]:.3f}" for c in crit_names)
            L.append(f"| {n} | {cells} | {totals[n]:.3f} |")
        L.append("\n## Sensitivity")
        L.extend(notes)
        L.append("\n_Weights encode priorities and are the main lever. If a flip-driver "
                 "above matters, revisit that weight with stakeholders before deciding._")
    text = "\n".join(L)
    if out:
        with open(out, "w") as f:
            f.write(text)
        print(f"Wrote {out}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description="Weighted / Pugh multi-criteria scoring.")
    ap.add_argument("model", help="Path to model JSON")
    ap.add_argument("--mode", choices=["weighted", "pugh"], default="weighted")
    ap.add_argument("--baseline", help="Baseline option name (pugh mode)")
    ap.add_argument("--out", help="Write Markdown report to this path")
    args = ap.parse_args()
    with open(args.model) as f:
        data = json.load(f)
    if args.mode == "pugh" and not args.baseline:
        args.baseline = data["options"][0]["name"]
    render(data, args.mode, args.baseline, args.out)


if __name__ == "__main__":
    main()
