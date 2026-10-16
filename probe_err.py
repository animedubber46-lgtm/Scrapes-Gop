import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import unshorten as U

for url in ["https://kogap.xyz/demo", "https://shrinkme.vip/demo",
            "https://redirly.icu/demo", "https://is.gd/demo"]:
    r = U.http_lane(url)
    print(f"== {url}\n   error={r.error} prot={r.protection} hops={r.hops}")
    for h in r.chain:
        print(f"   [{h.status}] {h.url[:70]} {(h.note or '')[:150]}")
