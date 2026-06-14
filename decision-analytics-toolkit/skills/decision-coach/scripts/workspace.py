#!/usr/bin/env python3
"""
Decision workspace: a living Markdown brief for a facilitated, multi-session decision, with
an embedded machine-readable data block. Handles the whole coach-driven lifecycle —
framing, criteria, options, indicators, a monitoring log over time, and the decision — and
exports a decision-review record so the same indicators that supported the choice can later
evaluate it.

The human-readable sections are RENDERED from the embedded data block (kept inside an HTML
comment so it stays invisible in Markdown viewers). Always edit via this script, not by hand.

COMMANDS
  Create a new workspace:
    python workspace.py --new --title "Pick a CRM" --owner John --out decisions/crm.md

  Log an indicator reading during the monitoring window:
    python workspace.py decisions/crm.md --log --indicator i1 --reading "trial NPS 42" --favors o2

  Summarize where the indicators currently point (decision support, not the decision):
    python workspace.py decisions/crm.md --status

  Export a decision-review record (after a decision is recorded in the data block):
    python workspace.py decisions/crm.md --to-record --out decisions/crm.record.json

EDITING CONTENT
  Problem, criteria, options, indicators, and the decision live in the embedded data block.
  Use --set-json to replace the whole block from a JSON file you prepared while coaching:
    python workspace.py decisions/crm.md --set-json filled.json
  (Run --new first to see the schema, fill it in collaboratively with the user, then set it.)

Pure standard library.
"""
import argparse
import datetime as dt
import json
import re
import sys

MARK_START = "<!-- decision-data"
MARK_END = "-->"

SCHEMA = {
    "id": "", "title": "", "owner": "", "status": "framing",
    "stage": "1. frame", "created": "", "updated": "",
    "problem": "",
    "success_criteria": [
        {"id": "c1", "name": "", "measure": "how it will be judged", "weight": 0}
    ],
    "options": [{"id": "o1", "name": "", "notes": ""}],
    "indicators": [
        {"id": "i1", "watch": "", "threshold": "", "favors_option": "o1",
         "source": "", "cadence": "weekly"}
    ],
    "monitoring_log": [],  # {date, indicator, reading, favors_option}
    "decision": None,      # {chosen_option, date, rationale}
    "review_schedule": []
}

STAGES = ["1. frame", "2. success criteria", "3. options", "4. indicators",
          "5. monitor", "6. decide", "7. review"]


def today():
    return dt.date.today().isoformat()


def load(path):
    text = open(path).read()
    m = re.search(re.escape(MARK_START) + r"\s*(\{.*?\})\s*" + re.escape(MARK_END),
                  text, re.DOTALL)
    if not m:
        sys.exit("No embedded decision-data block found. Was this made with --new?")
    return json.loads(m.group(1)), text


def opt_name(data, oid):
    for o in data["options"]:
        if o["id"] == oid:
            return o["name"] or oid
    return oid or "(unassigned)"


def render(data):
    """Build the full Markdown document from the data block."""
    L = []
    L.append(f"# Decision Workspace: {data['title'] or '(untitled)'}\n")
    L.append(f"*Owner:* {data['owner'] or '—'}  |  *Status:* {data['status']}  |  "
             f"*Current stage:* {data['stage']}  |  *Updated:* {data['updated']}\n")
    L.append("> This is a facilitated, user-owned decision. Claude coaches; the problem, "
             "criteria, options, and choice belong to the owner.\n")

    L.append("\n## 1. Problem")
    L.append(data["problem"].strip() or "_To be defined with the owner._")

    L.append("\n## 2. What success looks like (criteria)")
    if any(c.get("name") for c in data["success_criteria"]):
        L.append("| Criterion | How it will be measured | Weight |")
        L.append("|---|---|---|")
        for c in data["success_criteria"]:
            L.append(f"| {c.get('name','')} | {c.get('measure','')} | "
                     f"{c.get('weight','')} |")
    else:
        L.append("_To be defined — each criterion must be measurable enough to judge later._")

    L.append("\n## 3. Options")
    if any(o.get("name") for o in data["options"]):
        for o in data["options"]:
            note = f" — {o['notes']}" if o.get("notes") else ""
            L.append(f"- **{o.get('name','')}** ({o['id']}){note}")
    else:
        L.append("_To be generated — include the status quo / do-nothing option._")

    L.append("\n## 4. Indicators to watch (signposts before choosing)")
    if any(i.get("watch") for i in data["indicators"]):
        L.append("| Indicator | Threshold | Favors | Source | Cadence |")
        L.append("|---|---|---|---|---|")
        for i in data["indicators"]:
            L.append(f"| {i.get('watch','')} | {i.get('threshold','')} | "
                     f"{opt_name(data, i.get('favors_option'))} | "
                     f"{i.get('source','')} | {i.get('cadence','')} |")
        L.append("\n_These same indicators will evaluate the chosen option later (stage 7)._")
    else:
        L.append("_To be defined — observable signals that discriminate between options._")

    L.append("\n## 5. Monitoring log")
    if data["monitoring_log"]:
        L.append("| Date | Indicator | Reading | Currently favors |")
        L.append("|---|---|---|---|")
        for r in data["monitoring_log"]:
            ind = next((i for i in data["indicators"]
                        if i["id"] == r["indicator"]), {})
            L.append(f"| {r['date']} | {ind.get('watch', r['indicator'])} | "
                     f"{r['reading']} | {opt_name(data, r.get('favors_option'))} |")
    else:
        L.append("_No readings yet. Give the decision room; log signals as they appear._")

    L.append("\n## 6. Decision")
    if data["decision"]:
        d = data["decision"]
        L.append(f"**Chosen:** {opt_name(data, d['chosen_option'])} "
                 f"(on {d.get('date','')})")
        L.append(f"\n**Rationale:** {d.get('rationale','')}")
    else:
        L.append("_Not yet decided. Decide when the indicators have spoken or the deadline "
                 "arrives — then run a final premortem / key-assumptions check._")

    L.append("\n## 7. Review plan")
    if data["review_schedule"]:
        L.append("Scheduled reviews: " + ", ".join(data["review_schedule"]))
    L.append("The indicators above (plus outcome metrics) become the yardstick. Export a "
             "decision-review record with `workspace.py --to-record`.\n")

    block = MARK_START + "\n" + json.dumps(data, indent=2) + "\n" + MARK_END + "\n"
    return "\n".join(L) + "\n\n" + block


def write(path, data):
    data["updated"] = today()
    open(path, "w").write(render(data))


def cmd_new(args):
    data = json.loads(json.dumps(SCHEMA))  # deep copy
    data["title"] = args.title or ""
    data["owner"] = args.owner or ""
    data["id"] = (today() + "-" + re.sub(r"[^a-z0-9]+", "-",
                  (args.title or "decision").lower())).strip("-")
    data["created"] = today()
    out = args.out or "decision_workspace.md"
    write(out, data)
    print(f"Created workspace at {out}.")
    print("Next: coach the owner through stages 1–4, then fill the data block "
          "(--set-json) or edit collaboratively. Schema keys: problem, success_criteria, "
          "options, indicators.")


def cmd_set_json(args):
    data, _ = load(args.record)
    new = json.load(open(args.set_json))
    data.update(new)
    write(args.record, data)
    print(f"Updated data block in {args.record} and re-rendered.")


def cmd_log(args):
    data, _ = load(args.record)
    if not any(i["id"] == args.indicator for i in data["indicators"]):
        sys.exit(f"Unknown indicator id '{args.indicator}'. "
                 f"Known: {[i['id'] for i in data['indicators']]}")
    data["monitoring_log"].append({
        "date": args.date or today(),
        "indicator": args.indicator,
        "reading": args.reading,
        "favors_option": args.favors
    })
    if data["stage"] in ("1. frame", "2. success criteria", "3. options", "4. indicators"):
        data["stage"] = "5. monitor"
        data["status"] = "monitoring"
    write(args.record, data)
    print(f"Logged reading for {args.indicator}. Run --status to see where things point.")


def cmd_status(args):
    data, _ = load(args.record)
    print(f"# Indicator status — {data['title']}  (as of {today()})\n")
    if not data["monitoring_log"]:
        print("No readings logged yet. The decision is still gathering signal — that's "
              "fine; resist deciding prematurely.")
        return
    # latest reading per indicator
    latest = {}
    for r in data["monitoring_log"]:
        latest[r["indicator"]] = r
    tally = {}
    print("## Latest signal per indicator")
    for i in data["indicators"]:
        r = latest.get(i["id"])
        if not r:
            print(f"- {i['watch']}: _no reading yet_")
            continue
        fav = r.get("favors_option") or i.get("favors_option")
        tally[fav] = tally.get(fav, 0) + 1
        print(f"- {i['watch']}: {r['reading']}  → favors **{opt_name(data, fav)}** "
              f"(as of {r['date']})")
    if tally:
        print("\n## Current lean (count of indicators favoring each option)")
        for oid, n in sorted(tally.items(), key=lambda kv: kv[1], reverse=True):
            print(f"- {opt_name(data, oid)}: {n}")
        print("\n> This is decision *support*, not the decision. Weigh indicators by "
              "importance, not just count, and check whether enough signal has accumulated "
              "before committing.")


def cmd_to_record(args):
    data, _ = load(args.record)
    if not data.get("decision"):
        print("Warning: no decision recorded yet; exporting an open record.", file=sys.stderr)
    rec = {
        "id": data["id"],
        "title": data["title"],
        "date_decided": (data.get("decision") or {}).get("date", today()),
        "owner": data["owner"],
        "decision": opt_name(data, (data.get("decision") or {}).get("chosen_option", "")),
        "alternatives_considered": [o["name"] for o in data["options"]
                                    if o["id"] != (data.get("decision") or {}).get("chosen_option")],
        "rationale": (data.get("decision") or {}).get("rationale", ""),
        # success criteria -> predictions/targets (interval placeholders to fill at decision)
        "predictions": [
            {"id": c["id"], "claim": f"{c['name']} — {c['measure']}", "type": "binary",
             "probability": 0.5, "resolves_on": "", "actual": None}
            for c in data["success_criteria"] if c.get("name")
        ],
        # criteria also recorded as assumptions about what matters
        "assumptions": [
            {"id": "a-" + c["id"], "text": f"{c['name']} is the right thing to optimize "
             f"(weight {c.get('weight','?')})", "confidence": "medium",
             "impact_if_false": "medium", "falsifier": "", "status": "open"}
            for c in data["success_criteria"] if c.get("name")
        ],
        # indicators -> tripwires (the dual-purpose bridge)
        "tripwires": [
            {"id": i["id"], "indicator": i["watch"], "threshold": i.get("threshold", ""),
             "signals": f"favored {opt_name(data, i.get('favors_option'))} at selection; "
                        f"now an evaluation metric", "fired": None}
            for i in data["indicators"] if i.get("watch")
        ],
        "review_schedule": data.get("review_schedule", []),
        "reviews": []
    }
    out = args.out or (args.record.rsplit(".", 1)[0] + ".record.json")
    json.dump(rec, open(out, "w"), indent=2)
    print(f"Wrote decision-review record to {out}. The stage-4 indicators are now tripwires "
          f"/ evaluation metrics — score later with the decision-review skill.")


def main():
    ap = argparse.ArgumentParser(description="Decision workspace for coach-driven decisions.")
    ap.add_argument("record", nargs="?", help="Path to workspace .md (omit with --new)")
    ap.add_argument("--new", action="store_true")
    ap.add_argument("--title"); ap.add_argument("--owner"); ap.add_argument("--out")
    ap.add_argument("--set-json", help="Replace the data block from this JSON file")
    ap.add_argument("--log", action="store_true")
    ap.add_argument("--indicator"); ap.add_argument("--reading"); ap.add_argument("--favors")
    ap.add_argument("--date")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--to-record", action="store_true")
    args = ap.parse_args()

    if args.new:
        return cmd_new(args)
    if not args.record:
        sys.exit("Provide a workspace path, or use --new.")
    if args.set_json:
        return cmd_set_json(args)
    if args.log:
        if not (args.indicator and args.reading):
            sys.exit("--log needs --indicator and --reading (optionally --favors, --date).")
        return cmd_log(args)
    if args.status:
        return cmd_status(args)
    if args.to_record:
        return cmd_to_record(args)
    # default: just re-render / validate
    data, _ = load(args.record)
    write(args.record, data)
    print(f"Re-rendered {args.record} (stage: {data['stage']}, status: {data['status']}).")


if __name__ == "__main__":
    main()
