"""HTTP-lane smoke test against public links.

    python test_engine.py
"""
import unshorten as U

CASES = [
    "https://t.co/xyz",
    "https://httpbin.org/redirect-to?url=https%3A%2F%2Fexample.com",
    "https://httpbin.org/redirect/2",
    "https://bit.ly/3xample1",
    "arolinks.com",
    "not a url",
    "",
    "http://127.0.0.1:5000/",
]

if __name__ == "__main__":
    for url in CASES:
        r = U.http_lane(url)
        print(f"{url!r:60} bypassed={r.bypassed!s:5} method={r.method:12} "
              f"prot={str(r.protection):14} -> {r.destination or r.error}")
