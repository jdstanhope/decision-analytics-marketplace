#!/usr/bin/env python3
"""
Score a decision record against what actually happened, and track calibration across many
records.

Single decision:  did each predicted interval contain the actual? how accurate were the
probabilistic calls (Brier score)? which assumptions held and which tripwires fired?

Calibration (across a folder of records): is ~80% of reality landing inside your 80%
intervals, and do your stated probabilities match reality? The usual failure is
overconfidence — intervals too narrow, high-confidence calls missing too often.

USAGE:
  python score_review.py decisions/invest_50k.json          # score one decision
  python score_review.py --calibrate decisions/             # aggregate across records
  (add --out report.md to save)

To score, fill each prediction's "actual" value (a number for interval predictions; 1/0 or
true/false for binary predictions). Unresolved predictions (actual = null) are skipped.
Pure standard library — no dependencies.
"""
import argparse
import glob
import json
import os
import sys


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _bool(x):
    if isinstance(x, bool):
        return 1 if x else 0
    if isinstance(x, (int, float)):
        return 1 if x else 0
    if isinstance(x, str):
        if x.lower() in ("true", "yes", "y", "1"):
            return 1
        if x.lower() in ("false", "no", "n", "0"):
            return 0
    return None


def score_predictions(rec):
    """Return per-prediction results plus running tallies."""
    rows = []
    interval_hits = interval_total = 0
    brier_sum = brier_n = 0.0
    for p in rec.get("predictions", []):
        ptype = p.get("type", "interval")
        actual_raw = p.get("actual", None)
        if actual_raw in (None, ""):
            rows.append((p, "unresolved", None))
            continue
        if ptype == "interval":
            a = _num(actual_raw)
            if a is None:
                rows.append((p, "bad-actual", None))
                continue
            inside = p["p10"] <= a <= p["p90"]
            interval_total += 1
            interval_hits += 1 if inside else 0
            # signed error vs median, in interval-half-widths
            half = (p["p90"] - p["p10"]) / 2 or 1
            z = (a - p["p50"]) / half
            rows.append((p, "in-interval" if inside else "OUTSIDE", z))
        elif ptype == "binary":
            o = _bool(actual_raw)
            pr = p.get("probability", 0.5)
            if o is None:
                rows.append((p, "bad-actual", None))
                continue
            brier_sum += (pr - o) ** 2
            brier_n += 1
            # "right side of 50%?"
            correct = (pr >= 0.5) == (o == 1)
            rows.append((p, "correct" if correct else "wrong", (pr, o)))
    return rows, interval_hits, interval_total, brier_sum, brier_n


def score_one(rec, out=None, quiet=False):
    rows, ih, it, bs, bn = score_predictions(rec)
    L = []
    L.append(f"# Review: {rec.get('title','(untitled)')}")
    L.append(f"Decided {rec.get('date_decided')} — chose: {rec.get('decision')}\n")

    L.append("## Predictions vs. actuals")
    for p, verdict, extra in rows:
        if verdict == "unresolved":
            L.append(f"- [{p['id']}] {p['claim']}: _not yet resolved_")
        elif p.get("type", "interval") == "interval":
            mark = "✓" if verdict == "in-interval" else "✗"
            ztxt = f", {extra:+.2f} half-widths from median" if extra is not None else ""
            L.append(f"- {mark} [{p['id']}] {p['claim']}: actual {p['actual']} vs "
                     f"P10–P90 [{p['p10']}, {p['p90']}] — **{verdict}**{ztxt}")
        else:
            mark = "✓" if verdict == "correct" else "✗"
            pr, o = extra
            L.append(f"- {mark} [{p['id']}] {p['claim']}: said {pr:.0%}, outcome "
                     f"{'YES' if o else 'NO'} — **{verdict}**")
    if it:
        L.append(f"\n**Interval coverage:** {ih}/{it} actuals fell inside their 80% "
                 f"intervals ({ih/it:.0%}). Near 80% is well-calibrated; far below means "
                 f"your ranges were too narrow (overconfident).")
    if bn:
        brier = bs / bn
        L.append(f"\n**Brier score:** {brier:.3f} over {int(bn)} probabilistic "
                 f"prediction(s) (0 = perfect, 0.25 = no-skill baseline of always saying "
                 f"50%). Lower is better.")

    # assumptions (use latest review's updates if present, else recorded status)
    L.append("\n## Assumptions")
    latest = rec.get("reviews", [])[-1] if rec.get("reviews") else {}
    upd = {u["id"]: u for u in latest.get("assumption_updates", [])}
    for a in rec.get("assumptions", []):
        st = upd.get(a["id"], {}).get("status", a.get("status", "open"))
        note = upd.get(a["id"], {}).get("note", "")
        flag = {"held": "✓", "broken": "✗", "uncertain": "?", "open": "·"}.get(st, "·")
        extra = f" — {note}" if note else ""
        L.append(f"- {flag} [{a['id']}] {a['text']}  (**{st}**; impact-if-false "
                 f"{a.get('impact_if_false','?')}){extra}")
    broken = [a for a in rec.get("assumptions", [])
              if upd.get(a["id"], {}).get("status", a.get("status")) == "broken"]
    if broken:
        L.append("\n> A load-bearing assumption broke. Re-run the affected model with "
                 "corrected inputs before trusting the original conclusion.")

    # tripwires
    tw = rec.get("tripwires", [])
    if tw:
        L.append("\n## Tripwires")
        twupd = {u["id"]: u for u in latest.get("tripwire_updates", [])}
        for t in tw:
            fired = twupd.get(t["id"], {}).get("fired", t.get("fired"))
            mark = "🔔 FIRED" if fired else "—"
            L.append(f"- {mark} [{t['id']}] {t['indicator']} {t.get('threshold','')}: "
                     f"{t.get('signals','')}")

    # process vs outcome
    if latest:
        L.append("\n## Process vs. outcome")
        L.append(f"- Process grade: **{latest.get('process_grade','(not set)')}** "
                 f"(judge the decision on what was knowable *then*, not on the result).")
        if latest.get("lessons"):
            L.append("- Lessons: " + "; ".join(latest["lessons"]))
        if latest.get("actions"):
            L.append("- Actions: " + "; ".join(latest["actions"]))
    else:
        L.append("\n## Process vs. outcome")
        L.append("- No review entry yet. Add one (decision_record.py --review-template) to "
                 "record whether the *reasoning* was sound regardless of the outcome, plus "
                 "lessons and actions.")

    text = "\n".join(L)
    if not quiet:
        if out:
            open(out, "w").write(text)
            print(f"Wrote {out}")
        else:
            print(text)
    return ih, it, bs, bn


def calibrate(folder, out=None):
    files = sorted(glob.glob(os.path.join(folder, "*.json")))
    if not files:
        sys.exit(f"No .json records found in {folder}")
    tot_ih = tot_it = 0
    tot_bs = tot_bn = 0.0
    # calibration buckets for binary predictions
    buckets = {b: [0, 0] for b in (0.1, 0.3, 0.5, 0.7, 0.9)}  # prob -> [yes, total]
    n_records = 0
    for fp in files:
        try:
            rec = json.load(open(fp))
        except Exception:
            continue
        n_records += 1
        ih, it, bs, bn = score_one(rec, quiet=True)
        tot_ih += ih; tot_it += it; tot_bs += bs; tot_bn += bn
        for p in rec.get("predictions", []):
            if p.get("type") == "binary" and p.get("actual") not in (None, ""):
                o = _bool(p["actual"])
                pr = p.get("probability", 0.5)
                nearest = min(buckets, key=lambda b: abs(b - pr))
                buckets[nearest][1] += 1
                buckets[nearest][0] += 1 if o else 0

    L = []
    L.append("# Calibration across decisions\n")
    L.append(f"Records scored: {n_records}\n")
    if tot_it:
        cov = tot_ih / tot_it
        L.append(f"**Interval coverage:** {tot_ih}/{tot_it} = {cov:.0%} of actuals fell "
                 f"inside their 80% intervals.")
        if cov < 0.65:
            L.append("> Well below 80% — you are **overconfident**; your ranges are too "
                     "narrow. Widen future intervals.")
        elif cov > 0.92:
            L.append("> Above 80% — your ranges may be **too wide** (underconfident); you "
                     "can tighten them.")
        else:
            L.append("> Close to 80% — your intervals are reasonably calibrated.")
    if tot_bn:
        L.append(f"\n**Mean Brier score:** {tot_bs/tot_bn:.3f} over {int(tot_bn)} "
                 f"probabilistic predictions (0 = perfect, 0.25 = no skill).")
    has_bins = any(v[1] for v in buckets.values())
    if has_bins:
        L.append("\n## Calibration table (probabilistic predictions)")
        L.append("| You said | Actually happened | Count |")
        L.append("|---|---|---|")
        for b in sorted(buckets):
            yes, n = buckets[b]
            if n:
                L.append(f"| ~{b:.0%} | {yes/n:.0%} | {n} |")
        L.append("\nIf 'actually happened' tracks 'you said' down the table, you're "
                 "calibrated. If your high-confidence rows come true less often than you "
                 "claimed, discount your certainty.")
    text = "\n".join(L)
    if out:
        open(out, "w").write(text)
        print(f"Wrote {out}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description="Score decision records and track calibration.")
    ap.add_argument("target", help="A record JSON, or a folder with --calibrate")
    ap.add_argument("--calibrate", action="store_true",
                    help="Aggregate calibration across a folder of records")
    ap.add_argument("--out", help="Write Markdown report to this path")
    args = ap.parse_args()
    if args.calibrate:
        calibrate(args.target, args.out)
    else:
        rec = json.load(open(args.target))
        score_one(rec, args.out)


if __name__ == "__main__":
    main()
