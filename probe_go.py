import sys

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
url = sys.argv[1] if len(sys.argv) > 1 else "https://justkoalas.com/go/1286092"
r = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"},
                 allow_redirects=True)
print(r.status_code, r.url, flush=True)
print(r.text[:3000], flush=True)
