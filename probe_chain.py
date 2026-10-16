import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import unshorten as U

for url in sys.argv[1:]:
    r = U.http_lane(url)
    print(f"== {url}\n   final={r.final_url} method={r.method} prot={r.protection}")
    for h in r.chain:
        print(f"   [{h.status}] {h.type:11} {h.url[:70]} -> {str(h.location)[:60]} {(h.note or '')[:60]}")
