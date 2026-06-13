#!/usr/bin/env python3
"""
Create or validate a decision record — the durable journal entry that makes a decision
reviewable later.

A record captures, at decision time: the choice and rationale, the load-bearing
assumptions, falsifiable predictions (as ranges or probabilities, each with a resolution
date), tripwires to watch, and when to review. Later, actuals get filled in and
score_review.py grades it.

USAGE:
  python decision_record.py --new --out decisions/invest_50k.json   # scaffold a template
  python decision_record.py decisions/invest_50k.json               # validate + summarize
  python decision_record.py decisions/invest_50k.json --as-of 2027-06-13  # what's due then

Records are plain JSON — edit them by hand or generate them from another skill's output.
Keep all records in one folder so score_review.py --calibrate can aggregate them.
"""
import argparse
import datetime as dt
import json
import sys

TEMPLATE = {
    "id": "YYYY-MM-DD-short-slug",
    "title": "One-line description of the decision",
    "date_decided": "YYYY-MM-DD",
    "owner": "Your name",
    "decision": "The option you chose",
    "alternatives_considered": ["Option B", "Option C"],
    "rationale": "Why you chose it, in a sentence or two.",
    "predictions": [
        {
            "id": "p1",
            "claim": "What this predicts (e.g. portfolio value in 10 years)",
            "type": "interval",
            "unit": "USD",
            "p10": 0, "p50": 0, "p90": 0,
            "resolves_on": "YYYY-MM-DD",
            "actual": None
        },
        {
            "id": "p2",
            "claim": "A yes/no prediction (e.g. beats 3% inflation)",
            "type": "binary",
            "probability": 0.5,
            "resolves_on": "YYYY-MM-DD",
            "actual": None
        }
    ],
    "assumptions": [
        {
            "id": "a1",
            "text": "A load-bearing assumption the decision depends on",
            "confidence": "medium",
            "impact_if_false": "high",
            "falsifier": "What observation would prove this wrong",
            "status": "open"
        }
    ],
    "tripwires": [
        {
            "id": "t1",
            "indicator": "Something observable to watch",
            "threshold": "The level that signals a regime change",
            "signals": "What it would mean / what to do",
            "fired": None
        }
    ],
    "review_schedule": ["YYYY-MM-DD"],
    "reviews": []
}

VALID_CONF = {"high", "medium", "low"}
VALID_STATUS = {"open", "held", "broken", "uncertain"}


def parse_date(s):
    return dt.date.fromisoformat(s)


def validate(rec):
    errs, warns = [], []
    for f in ("id", "title", "date_decided", "decision"):
        if not rec.get(f) or str(rec[f]).startswith(("YYYY", "One-line", "The option")):
            errs.append(f"Missing/placeholder field: {f}")
    try:
        parse_date(rec["date_decided"])
    except Exception:
        errs.append("date_decided is not a valid YYYY-MM-DD date")

    for i, p in enumerate(rec.get("predictions", [])):
        tag = f"prediction {p.get('id', i)}"
        ptype = p.get("type", "interval")
        if ptype == "interval":
            if not all(k in p for k in ("p10", "p50", "p90")):
                errs.append(f"{tag}: interval needs p10, p50, p90")
            elif not (p["p10"] <= p["p50"] <= p["p90"]):
                errs.append(f"{tag}: require p10 <= p50 <= p90")
        elif ptype == "binary":
            pr = p.get("probability")
            if pr is None or not (0 <= pr <= 1):
                errs.append(f"{tag}: binary needs probability in [0,1]")
        else:
            errs.append(f"{tag}: unknown type '{ptype}' (use interval or binary)")
        if "resolves_on" not in p:
            warns.append(f"{tag}: no resolves_on date — it won't surface for review")
        else:
            try:
                parse_date(p["resolves_on"])
            except Exception:
                errs.append(f"{tag}: resolves_on not a valid date")

    for i, a in enumerate(rec.get("assumptions", [])):
        tag = f"assumption {a.get('id', i)}"
        if a.get("confidence") not in VALID_CONF:
            warns.append(f"{tag}: confidence should be high/medium/low")
        if a.get("status", "open") not in VALID_STATUS:
            errs.append(f"{tag}: status must be one of {sorted(VALID_STATUS)}")
        if not a.get("falsifier"):
            warns.append(f"{tag}: no falsifier — hard to judge later if it held")

    for d in rec.get("review_schedule", []):
        try:
            parse_date(d)
        except Exception:
            errs.append(f"review_schedule has invalid date: {d}")
    return errs, warns


def summarize(rec, as_of):
    print(f"# Decision record: {rec.get('title','(untitled)')}")
    print(f"- id: {rec.get('id')}  |  decided: {rec.get('date_decided')}  |  "
          f"owner: {rec.get('owner')}")
    print(f"- choice: {rec.get('decision')}")
    preds = rec.get("predictions", [])
    open_preds = [p for p in preds if p.get("actual") in (None, "")]
    print(f"- predictions: {len(preds)} ({len(open_preds)} unresolved)")
    print(f"- assumptions: {len(rec.get('assumptions', []))}  |  "
          f"tripwires: {len(rec.get('tripwires', []))}  |  "
          f"reviews logged: {len(rec.get('reviews', []))}")

    due = []
    for p in preds:
        r = p.get("resolves_on")
        if r and p.get("actual") in (None, ""):
            try:
                if parse_date(r) <= as_of:
                    due.append(p)
            except Exception:
                pass
    upcoming_reviews = [d for d in rec.get("review_schedule", [])
                        if _safe_le(as_of, d)]
    print(f"\n## As of {as_of.isoformat()}")
    if due:
        print("Predictions DUE for resolution (fill in `actual`, then run score_review.py):")
        for p in due:
            print(f"  - [{p['id']}] {p['claim']}  (resolved {p['resolves_on']})")
    else:
        print("No predictions are due yet.")
    if upcoming_reviews:
        print("Upcoming scheduled reviews: " + ", ".join(sorted(upcoming_reviews)))


def _safe_le(a_date, d_str):
    try:
        return a_date <= parse_date(d_str)
    except Exception:
        return False


def review_template():
    """Print a review-entry template to paste into the record's `reviews` list."""
    entry = {
        "date": dt.date.today().isoformat(),
        "notes": "What happened and what you observed.",
        "assumption_updates": [{"id": "a1", "status": "held|broken|uncertain",
                                "note": "evidence"}],
        "tripwire_updates": [{"id": "t1", "fired": False, "date": None}],
        "process_grade": "sound|mixed|flawed",
        "lessons": ["What you learned"],
        "actions": ["Concrete next step (rebalance, revise input, update belief)"]
    }
    print("\n## Review-entry template (add to the record's \"reviews\" list, and fill each "
          "prediction's \"actual\"):")
    print(json.dumps(entry, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Create or validate a decision record.")
    ap.add_argument("record", nargs="?", help="Path to record JSON (omit with --new)")
    ap.add_argument("--new", action="store_true", help="Write a blank template")
    ap.add_argument("--out", help="Output path for --new")
    ap.add_argument("--as-of", help="Date (YYYY-MM-DD) to evaluate what's due; default today")
    ap.add_argument("--review-template", action="store_true",
                    help="Print a review-entry template")
    args = ap.parse_args()

    if args.new:
        out = args.out or "decision_record.json"
        with open(out, "w") as f:
            json.dump(TEMPLATE, f, indent=2)
        print(f"Wrote template to {out}. Fill it in, then validate with:\n"
              f"  python decision_record.py {out}")
        return

    if not args.record:
        sys.exit("Provide a record path, or use --new --out <file>.")
    with open(args.record) as f:
        rec = json.load(f)
    errs, warns = validate(rec)
    as_of = parse_date(args.as_of) if args.as_of else dt.date.today()
    summarize(rec, as_of)
    if warns:
        print("\n## Warnings")
        for w in warns:
            print(f"  ⚠ {w}")
    if errs:
        print("\n## Errors (fix before relying on this record)")
        for e in errs:
            print(f"  ✗ {e}")
    else:
        print("\n✓ Record structure is valid.")
    if args.review_template:
        review_template()


if __name__ == "__main__":
    main()
