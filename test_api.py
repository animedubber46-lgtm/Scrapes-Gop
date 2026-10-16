"""Web API checks, including the real arolinks campaign link.

    python test_api.py [base_url]      (default http://127.0.0.1:5000)
"""
import os
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

B = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("LB_API", "http://127.0.0.1:5000")
AROLINKS = "https://arolinks.com/sOl08C"


def show(tag, r):
    print(f"{tag:30} bypassed={str(r.get('bypassed')):5} lane={str(r.get('lane')):12} "
          f"method={str(r.get('method')):11} prot={str(r.get('protection')):12} "
          f"-> {r.get('destination') or r.get('error')}")


print("== page ==")
print("GET / ->", requests.get(B).status_code)

print("\n== /api/expand, fast public links ==")
for url in ["https://t.co/xyz", "https://bit.ly/3xample1", "not a url", ""]:
    show(url[:29] or "(empty)", requests.post(B + "/api/expand", json={"url": url}).json())

print("\n== /api/expand, fixture walls (need `python run_local.py`, not app.py) ==")
for path in ["code1", "code2", "code3", "code5", "code6", "code4"]:
    r = requests.post(B + "/api/expand",
                      json={"url": f"http://127.0.0.1:8099/{path}"}).json()
    show(path, r)
    if "not a public internet" in (r.get("error") or ""):
        print("   ^ blocked by the private-host guard (expected under app.py)")

print("\n== /api/expand, the real arolinks flow ==")
r = requests.post(B + "/api/expand", json={"url": AROLINKS}, timeout=240).json()
show(AROLINKS[:29], r)
print("   chain:")
for hop in r.get("chain", []):
    note = f"  ({hop['note']})" if hop.get("note") else ""
    print(f"     {hop['index']:2}. {hop['type']:11} {hop['url'][:70]}{note}")
print("   preview:", (r.get("preview") or {}).get("title"))
assert r.get("bypassed"), "arolinks flow was not bypassed"
dest = r.get("destination") or ""
assert "/readmore" not in dest, "returned an intermediate page"
assert "telegram.me" in dest or "t.me/" in dest, f"not the invite destination: {dest}"
print("   OK: destination is", dest)

print("\n== /api/bulk ==")
r = requests.post(B + "/api/bulk", json={
    "text": "https://t.co/xyz\nhttp://127.0.0.1:8099/code3\n"
            "http://127.0.0.1:8099/code4\nhttps://example.com"}, timeout=240).json()
print("count", r["count"], "bypassed", r["bypassed"])
for item in r["results"]:
    show(item["input_url"][:29], item)

print("\n== /api/health ==")
print(requests.get(B + "/api/health").json())
print("\nall API checks passed")
