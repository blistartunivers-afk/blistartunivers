"""Bandit findings are advisory; scan/parse failures are not."""
import json
import sys
from pathlib import Path
report = json.loads(Path(sys.argv[1]).read_text())
if report.get("errors"):
    raise SystemExit(f"Bandit failed to analyze {len(report['errors'])} file(s)")
if not isinstance(report.get("results"), list):
    raise SystemExit("Bandit report is incomplete")
print(f"Bandit findings retained for review: {len(report['results'])}")
