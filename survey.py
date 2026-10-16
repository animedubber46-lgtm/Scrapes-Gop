"""Cheap survey of message.txt: status, size, title, and where it lands.

    python survey.py            # all links
    python survey.py 40         # first 40
"""
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def probe(url: str) -> str:
    try:
        r = requests.get(url, timeout=25, headers={"User-Agent": UA},
                         allow_redirects=True)
        m = TITLE.search(r.text or "")
        title = re.sub(r"\s+", " ", m.group(1)).strip()[:44] if m else "-"
        return (f"{r.status_code} {len(r.content):7} {url.split('//')[1][:26]:26} "
                f"-> {r.url[:52]:52} | {title}")
    except Exception as exc:
        return f"ERR {'':7} {url.split('//')[1][:26]:26} -> {type(exc).__name__}: {str(exc)[:40]}"


def main():
    links = [l.strip() for l in open("message.txt", encoding="utf-8", errors="replace")
             if l.strip() and not l.startswith("#")]
    if len(sys.argv) > 1:
        links = links[: int(sys.argv[1])]
    with ThreadPoolExecutor(max_workers=10) as pool:
        for line in pool.map(probe, links):
            print(line, flush=True)


if __name__ == "__main__":
    main()
