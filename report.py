"""Turn batch_results.jsonl into a readable report: solved list + skip reasons.

    python report.py            # writes report.md and prints a summary
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RESULTS = "batch_results.jsonl"

# protection / error -> why we gave up, in plain words
REASON = {
    "dead-link": "link does not exist (HTTP 404/410)",
    "server-error": "the shortener's own server is down (5xx)",
    "unreachable": "domain does not resolve / host unreachable",
    "captcha": "captcha or bot wall - needs a human",
    "cloudflare": "Cloudflare challenge - needs a human",
    "safelink": "safe-link wall that did not release",
    "shortener-wall": "wall page never released the link",
    "unresolved": "walk ended without a destination",
}


def reason(row: dict) -> str:
    if row.get("bypassed"):
        return "solved"
    prot = row.get("protection") or ""
    if prot in REASON:
        return REASON[prot]
    err = row.get("error") or ""
    if "does not resolve" in err:
        return REASON["unreachable"]
    if "Timeout" in err or "timed out" in err.lower():
        return "network timed out"
    if "SSLError" in err or "Certificate" in err:
        return "TLS/certificate problem"
    if err:
        return err[:60]
    return "no destination released"


def main() -> None:
    if not os.path.exists(RESULTS):
        sys.exit(f"{RESULTS} not found - run test_batch.py first")
    latest: dict[str, dict] = {}
    order: list[str] = []
    for line in open(RESULTS, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        url = row.get("url") or row.get("input_url")
        if url not in latest:
            order.append(url)
        latest[url] = row

    solved = [u for u in order if latest[u].get("bypassed")]
    failed = [u for u in order if not latest[u].get("bypassed")]
    counts = Counter(reason(latest[u]) for u in failed)

    lines = ["# Short link bypass report", "",
             f"- links tested: **{len(order)}**",
             f"- solved: **{len(solved)}**",
             f"- skipped: **{len(failed)}**", ""]

    lines += ["## Solved", "", "| link | destination |", "|---|---|"]
    for url in sorted(solved):
        dest = (latest[url].get("destination") or "").replace("|", "\\|")
        lines.append(f"| {url} | {dest[:90]} |")

    lines += ["", "## Skipped", "", "| link | why |", "|---|---|"]
    for url in sorted(failed):
        lines.append(f"| {url} | {reason(latest[url])} |")

    lines += ["", "## Reasons", ""]
    for why, n in counts.most_common():
        lines.append(f"- {n:3}  {why}")

    open("report.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"{len(solved)}/{len(order)} solved -> report.md\n")
    print("== skip reasons ==")
    for why, n in counts.most_common():
        print(f"{n:4}  {why}")


if __name__ == "__main__":
    main()
