"""Try specific links, browser lane, with the engine's debug log on."""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("LB_DEBUG", "")

import unshorten as U

for url in sys.argv[1:]:
    r = U.bypass(url, mode="browser")
    print(f"\n### {url}")
    print(f"   bypassed={r.bypassed} prot={r.protection} method={r.method} "
          f"{r.elapsed_ms // 1000}s -> {r.destination or r.error}")
    print(f"   note: {r.note}")
    print(f"   warnings: {r.warnings[:3]}")
    for hop in r.chain:
        print(f"   {hop.index:2}. [{hop.status}] {hop.type:11} {str(hop.url)[:80]}"
              f"{(hop.note and '  (' + hop.note + ')') or ''}")
