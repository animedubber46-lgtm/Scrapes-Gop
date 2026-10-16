"""Show the stored batch result for one link (chain + fields)."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
want = sys.argv[1]
row = None
for line in open("batch_results.jsonl", encoding="utf-8", errors="replace"):
    try:
        r = json.loads(line)
    except Exception:
        continue
    if want in r.get("url", ""):
        row = r
if not row:
    sys.exit("not found")
for k in ("url", "bypassed", "lane", "method", "protection", "error", "hops", "elapsed_ms"):
    print(f"{k:12} {row.get(k)}")
print("destination:", row.get("destination"))
for hop in row.get("chain", []):
    print(f"  {hop.get('index'):2}. [{hop.get('status')}] {hop.get('type')} {str(hop.get('url'))[:90]}")
    if hop.get("location"):
        print(f"       -> {str(hop.get('location'))[:90]}")
    if hop.get("note"):
        print(f"       ({hop.get('note')})")
