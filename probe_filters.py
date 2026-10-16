import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import unshorten as U

CASES = [
    "https://www.google.com/",
    "https://www.google.com/search?q=x",
    "https://www.godaddy.com/forsale/shrinkme.dev",
    "https://gplinks.com/subscriber/login",
    "https://x.com/yz",
    "https://docs.google.com/forms/d/1eExcSLO2",
    "http://video.google.com/videoplay?docid=-873",
    "https://telegram.me/+abc",
    "https://app.khaddavi.net/game-x",
    "https://techmint.in/some-article/",
    "https://mtc1.thetechhint.in/?adlinkfly=demo",
    "https://justkoalas.com/go/1286092",
]
for u in CASES:
    print(f"{U.looks_like_destination(u)!s:5} final={U.is_final_destination(u, 'https://cuty.io/demo')!s:5} {u}")
