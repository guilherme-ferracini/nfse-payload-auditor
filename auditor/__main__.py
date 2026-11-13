"""python -m auditor samples/client_profile.json samples/payloads/*.json [--out out/audit.md]"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

from .rules import RULES, Finding

ORDER = {"high": 0, "medium": 1, "low": 2}


def audit(payload: Dict, profile: Dict) -> List[Finding]:
    findings = [f for rule in RULES for f in rule(payload, profile)]
    return sorted(findings, key=lambda f: ORDER[f.severity])


def report(results: List[Tuple[Dict, List[Finding]]], profile: Dict) -> str:
    lines = [f"# NFS-e audit: {profile['company']}", "",
             "| Invoice | Value (R$) | High | Medium | Low | Status |", "|---|---:|---:|---:|---:|---|"]
    for p, fs in results:
        count = {s: sum(f.severity == s for f in fs) for s in ORDER}
        status = "BLOCK" if count["high"] else ("REVIEW" if count["medium"] else "OK")
        lines.append(f"| {p['number']} | {p['amounts']['service_value']:,.2f} | {count['high']} | "
                     f"{count['medium']} | {count['low']} | {status} |")
    for p, fs in results:
        lines += ["", f"## Invoice {p['number']} ({p['issue_date']})"]
        lines += [f"- **{f.severity.upper()}** `{f.rule}`: {f.message}" for f in fs] or ["- No findings."]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit NFS-e payloads against a company's tax profile")
    ap.add_argument("profile", type=Path)
    ap.add_argument("payloads", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    profile = json.loads(a.profile.read_text(encoding="utf-8"))
    results = []
    for path in a.payloads:
        payload = json.loads(path.read_text(encoding="utf-8"))
        results.append((payload, audit(payload, profile)))
    text = report(results, profile)
    print(text)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
