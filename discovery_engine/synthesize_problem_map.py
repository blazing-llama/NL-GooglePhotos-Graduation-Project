"""
Turns ollama_problem_map.json (per-review structured extractions from
llm_analyzer.py) into a single readable Problem Map document: counted,
ranked, with real evidence quotes -- not a hand-written narrative.

Run after llm_analyzer.py has produced at least a partial checkpoint.
"""

import json
from collections import Counter


def load(path="ollama_problem_map.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def top_n(counter, n=8):
    return counter.most_common(n)


def build_report(records, out_path="Advanced_Problem_Map.md"):
    n = len(records)
    failure_points = Counter(r.get("Failure_point", "Unspecified") for r in records)
    opportunities = Counter(r.get("Opportunity", "Unspecified") for r in records)
    sizes = Counter(r.get("Opportunity_size", "Unspecified") for r in records)
    segments = Counter(r.get("User_segment", "Unspecified") for r in records)

    lines = []
    lines.append("# Advanced Problem Map — Google Photos Retrieval Failures")
    lines.append("")
    lines.append(f"Generated from {n} real Play Store reviews, structured via a local "
                  f"Ollama LLM (no API cost) against a 7-stage retrieval-journey schema. "
                  f"Every finding below is grounded in an actual review quote, not a summary.")
    lines.append("")

    lines.append("## Opportunity size distribution")
    lines.append("")
    for size, count in sizes.most_common():
        pct = 100 * count / n if n else 0
        lines.append(f"- **{size}**: {count} reviews ({pct:.0f}%)")
    lines.append("")

    lines.append("## Where the retrieval journey breaks (Failure_point)")
    lines.append("")
    lines.append("| Failure point | Count | Share |")
    lines.append("|---|---|---|")
    for fp, count in top_n(failure_points, 10):
        pct = 100 * count / n if n else 0
        lines.append(f"| {fp} | {count} | {pct:.0f}% |")
    lines.append("")

    lines.append("## Top opportunities users are trying to accomplish")
    lines.append("")
    for opp, count in top_n(opportunities, 8):
        lines.append(f"- **{opp}** — {count} mentions")
    lines.append("")

    lines.append("## Who experiences this (User_segment)")
    lines.append("")
    for seg, count in top_n(segments, 6):
        lines.append(f"- {seg}: {count}")
    lines.append("")

    lines.append("## Evidence — representative quotes")
    lines.append("")
    seen_failure_points = set()
    for r in records:
        fp = r.get("Failure_point", "Unspecified")
        if fp in seen_failure_points:
            continue
        seen_failure_points.add(fp)
        evidence = r.get("Evidence") or r.get("_source_review", "")
        lines.append(f"**{fp}**")
        lines.append(f"> {evidence}")
        lines.append(f"- Workaround: {r.get('Workaround', 'n/a')}")
        lines.append(f"- Impact: {r.get('Impact', 'n/a')}")
        lines.append("")
        if len(seen_failure_points) >= 8:
            break

    report = "\n".join(lines)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Wrote {out_path} ({n} records analyzed)")


if __name__ == "__main__":
    build_report(load())
