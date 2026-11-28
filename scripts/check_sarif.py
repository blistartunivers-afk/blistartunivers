"""Resolve explicit and inherited SARIF levels; execution errors must fail CI."""
import json
import sys
from pathlib import Path


def count_errors(report: dict) -> int:
    runs = report.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("SARIF must contain at least one run")
    count = 0
    for run in runs:
        rules = run.get("tool", {}).get("driver", {}).get("rules", [])
        by_id = {r.get("id"): r for r in rules}
        for result in run.get("results", []):
            rule = by_id.get(result.get("ruleId"), {})
            index = result.get("ruleIndex")
            if isinstance(index, int) and 0 <= index < len(rules):
                rule = rules[index]
            level = result.get("level", rule.get("defaultConfiguration", {}).get("level", "warning"))
            if level not in ("none", "note", "warning", "error"):
                raise ValueError("Invalid SARIF level")
            count += level == "error"
    return count


if __name__ == "__main__":
    try:
        total = count_errors(json.loads(Path(sys.argv[1]).read_text()))
        print(f"SARIF error findings: {total}")
        sys.exit(1 if total else 0)
    except (OSError, ValueError, IndexError, TypeError) as exc:
        sys.exit(f"Invalid or missing SARIF: {exc}")
