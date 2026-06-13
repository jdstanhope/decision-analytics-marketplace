#!/usr/bin/env python3
"""
Decision-tree roll-back (fold-back) with expected value and expected value of perfect
information (EVPI).

Roll back the tree from leaves to root: at a CHANCE node, value = sum(prob * child value);
at a DECISION node, value = best child, and that child is the recommended choice.

INPUT JSON schema (recursive nodes):

A node is one of:
  Leaf:     {"name": "...", "type": "leaf", "value": 1200}
  Chance:   {"name": "...", "type": "chance",
             "branches": [{"prob": 0.6, "node": <node>}, {"prob": 0.4, "node": <node>}]}
  Decision: {"name": "...", "type": "decision",
             "branches": [{"label": "Launch", "node": <node>},
                          {"label": "Test first", "node": <node>}]}

Top level:
  {"tree": <root node>,
   "maximize": true,           # optional, default true (set false to minimize, e.g. cost)
   "evpi_over": "Demand"}      # optional: name of a chance node to compute EVPI for

Probabilities at each chance node should sum to 1 (a warning prints otherwise).

USAGE:
  python decision_tree.py tree.json
  python decision_tree.py tree.json --out report.md
"""
import argparse
import json
import sys

BETTER = max  # replaced at runtime based on "maximize"


def rollback(node, maximize, path_log, depth=0):
    """Return (value, annotated_choice_text). Logs decision recommendations into path_log."""
    t = node["type"]
    if t == "leaf":
        return node["value"], None
    if t == "chance":
        total_p = sum(b["prob"] for b in node["branches"])
        if abs(total_p - 1.0) > 1e-6:
            print(f"  [warn] chance node '{node.get('name','?')}' probs sum to {total_p:.3f}",
                  file=sys.stderr)
        ev = 0.0
        for b in node["branches"]:
            v, _ = rollback(b["node"], maximize, path_log, depth + 1)
            ev += b["prob"] * v
        return ev, None
    if t == "decision":
        choose = max if maximize else min
        best_val = None
        best_label = None
        options = []
        for b in node["branches"]:
            v, _ = rollback(b["node"], maximize, path_log, depth + 1)
            options.append((b["label"], v))
            if best_val is None or (v > best_val if maximize else v < best_val):
                best_val, best_label = v, b["label"]
        path_log.append({
            "decision": node.get("name", "Decision"),
            "choose": best_label,
            "value": best_val,
            "options": options,
        })
        return best_val, best_label
    sys.exit(f"Unknown node type: {t}")


def find_node(node, name):
    if node.get("name") == name:
        return node
    for b in node.get("branches", []):
        found = find_node(b["node"], name)
        if found:
            return found
    return None


def force_outcome(node, name, branch_index):
    """Return a copy of the tree with EVERY chance node named `name` collapsed to its
    branch at `branch_index` (i.e. that uncertainty is known to have that outcome).
    This 'pushes' the uncertainty ahead of the decisions, which is what perfect
    information means: you learn the outcome, then choose optimally."""
    if node["type"] == "leaf":
        return dict(node)
    if node["type"] == "chance" and node.get("name") == name:
        # resolve this uncertainty to the chosen outcome
        return force_outcome(node["branches"][branch_index]["node"], name, branch_index)
    new = {k: v for k, v in node.items() if k != "branches"}
    new["branches"] = []
    for b in node["branches"]:
        nb = {k: v for k, v in b.items() if k != "node"}
        nb["node"] = force_outcome(b["node"], name, branch_index)
        new["branches"].append(nb)
    return new


def evpi(data, maximize):
    """Expected value of perfect information about a single named chance node.

    EVPI = E_outcome[ value of the tree if that outcome were known before deciding ]
           - value of the tree without that information.

    For each possible outcome of the named uncertainty, we force it everywhere it
    appears, roll back the whole tree (decisions now optimize *knowing* the outcome),
    and weight the resulting root values by the outcome probabilities.
    """
    name = data.get("evpi_over")
    if not name:
        return None
    cn = find_node(data["tree"], name)
    if not cn or cn["type"] != "chance":
        return None
    base_val, _ = rollback(data["tree"], maximize, [], 0)
    ev_with = 0.0
    for i, b in enumerate(cn["branches"]):
        forced = force_outcome(data["tree"], name, i)
        v, _ = rollback(forced, maximize, [], 0)
        ev_with += b["prob"] * v
    # With perfect info you can never do worse, so EVPI is non-negative by construction.
    return abs(ev_with - base_val)


def render(data, out):
    maximize = data.get("maximize", True)
    log = []
    root_val, _ = rollback(data["tree"], maximize, log)
    L = []
    L.append("# Decision Tree Results\n")
    L.append(f"Objective: **{'maximize' if maximize else 'minimize'}** value.\n")
    L.append(f"## Expected value at the root: {root_val:.2f}\n")
    L.append("## Recommended policy (optimal choice at each decision node)\n")
    for d in log:
        opts = ", ".join(f"{lbl}: {val:.2f}" for lbl, val in d["options"])
        L.append(f"- At **{d['decision']}** → choose **{d['choose']}** "
                 f"(value {d['value']:.2f}).  _Options: {opts}_")
    ev = evpi(data, maximize)
    if ev is not None:
        L.append(f"\n## Value of information\n")
        L.append(f"Expected value of perfect information about **{data['evpi_over']}**: "
                 f"**{ev:.2f}**.")
        L.append(f"\nThat is the most it would be rational to pay to resolve "
                 f"'{data['evpi_over']}' *before* deciding. If a test/study that reduces "
                 f"this uncertainty costs less than {ev:.2f}, it is worth running; if it "
                 f"costs more, decide without it.")
    L.append("\n## Caveats")
    L.append("- Expected value assumes risk-neutrality. If a branch has high variance and "
             "the downside is large relative to your resources, weigh the downside "
             "directly, not just the average.")
    L.append("- Re-run with plausible alternative probabilities to find the thresholds at "
             "which the recommended choice changes — report those, not just the point EV.")
    text = "\n".join(L)
    if out:
        with open(out, "w") as f:
            f.write(text)
        print(f"Wrote {out}")
    else:
        print(text)


def main():
    ap = argparse.ArgumentParser(description="Roll back a decision tree.")
    ap.add_argument("tree", help="Path to tree JSON")
    ap.add_argument("--out", help="Write Markdown report to this path")
    args = ap.parse_args()
    with open(args.tree) as f:
        data = json.load(f)
    render(data, args.out)


if __name__ == "__main__":
    main()
