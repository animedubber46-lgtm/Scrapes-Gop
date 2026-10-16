"""Live check against a real short link - this is the one that matters.

    python test_live.py [url] [mode]

Default url is the arolinks campaign link: the walk goes
arolinks -> landing -> "Step 1" article (Verify + Continue) -> "Step 2" article
-> ... -> "Get Link" button, whose href is the destination.
The destination rotates per visit, so the assertion is structural:
it must be a real article URL, not a shortener / landing / readmore page.
"""
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("LB_DEBUG", "1" if "--debug" in sys.argv else "")

import unshorten as U

url = sys.argv[1] if len(sys.argv) > 1 else "https://arolinks.com/nyQtXW"
mode = sys.argv[2] if len(sys.argv) > 2 else "auto"

BAD = re.compile(r"/(readmore|studyeducations|educationschol\w*)/|[?&](st|pgtr|universt\w*|universit\w*)=", re.I)

r = U.bypass(url, mode=mode)
print(f"input      : {r.input_url}")
print(f"bypassed   : {r.bypassed}")
print(f"lane/method: {r.lane} / {r.method}")
print(f"protection : {r.protection}")
print(f"hops       : {r.hops}   elapsed: {r.elapsed_ms} ms")
print(f"note       : {r.note}")
print(f"warnings   : {r.warnings}")
print(f"\nDESTINATION: {r.destination}")
print("\nchain:")
for hop in r.chain:
    print(f"  {hop.index:2}. [{hop.status or '-'}] {hop.type:11} {hop.url[:100]}")
    if hop.location:
        print(f"       -> {hop.location[:100]}")
    if hop.note:
        print(f"       ({hop.note})")
if r.preview:
    print("\npreview title:", r.preview.get("title"))

assert r.bypassed, f"not bypassed: protection={r.protection} note={r.note}"
assert not BAD.search(r.destination), f"got an intermediate page, not the destination: {r.destination}"
assert U.looks_like_destination(r.destination), f"implausible destination: {r.destination}"

# the campaign link of record must land on this exact invite
EXPECTED = "https://telegram.me/+aBh3g24AwuMwZjE9"
if "sOl08C" in url:
    assert r.destination == EXPECTED, f"expected {EXPECTED}, got {r.destination}"

print(f"\nOK  {r.destination}  ({r.elapsed_ms} ms, lane {r.lane})")
