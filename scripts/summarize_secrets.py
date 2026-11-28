"""Print detector counts only, never Raw/RawV2 or source content."""
from collections import Counter
import json
from pathlib import Path
import sys
counts = Counter()
for line in Path(sys.argv[1]).read_text().splitlines():
    if line.strip():
        result = json.loads(line)
        counts[str(result.get("DetectorName", "unknown"))] += 1
print(f"Secret candidates requiring review: {sum(counts.values())}")
for name, count in sorted(counts.items()):
    # Avoid log-control characters even in detector names.
    print(f"{name.encode('unicode_escape').decode()}: {count}")
