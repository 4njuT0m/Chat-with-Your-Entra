"""Stage 3 - Run all security checks without the AI and print the results.

Run from the repo folder:
    python src\\run_checks.py
"""

import json
from pathlib import Path

from checks import run_checks

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

findings = run_checks()
OUTPUT_DIR.mkdir(exist_ok=True)
(OUTPUT_DIR / "findings.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")

print(f"===== {len(findings)} findings =====")
for f in findings:
    techniques = ", ".join(t["id"] for t in f.get("mitre_attack", []))
    print(f"[{f['status']:<5}] [{f['severity']:<6}] {f['check']:<22} {f['title']}")
    if techniques:
        print(f"{'':<39}MITRE ATT&CK: {techniques}")
print("\nFull evidence saved to output/findings.json")
