"""Bypass checks.

  python test_wall.py        (leave running, serves fake shortener walls)
  python test_engine.py      HTTP lane only, public links
  python test_bypass.py      both lanes, incl. the local fixture walls
"""
import unshorten as U

FIXTURE = "http://127.0.0.1:8099"
PUBLIC = [
    "https://t.co/xyz",
    "https://httpbin.org/redirect-to?url=https%3A%2F%2Fexample.com",
    "https://httpbin.org/redirect/2",
    "https://bit.ly/3xample1",
    "arolinks.com",
    "",
    "not a url",
]

WALLS = [
    (f"{FIXTURE}/code1", "https://example.com/destination-page"),   # URL in window.open
    (f"{FIXTURE}/code2", "https://example.com/destination-page"),   # cookie + 2 steps + base64
    (f"{FIXTURE}/code3", "https://example.com/destination-page"),   # meta refresh
    (f"{FIXTURE}/code5", "https://example.com/destination-page"),   # click + XHR (browser lane)
    (f"{FIXTURE}/code6", "https://example.com/destination-page"),   # countdown + top navigation
    (f"{FIXTURE}/code4", None),                                     # captcha -> must be reported
]


def show(tag, r):
    dest = r.destination or r.error or "-"
    print(f"{tag:34} bypassed={r.bypassed!s:5} lane={r.lane:12} method={r.method:11} "
          f"prot={str(r.protection):14} -> {dest[:60]}")


def main():
    print("== HTTP lane (public) ==")
    for url in PUBLIC:
        r = U.http_lane(url)
        show(url[:33], r)

    print("\n== auto mode on local walls ==")
    for url, expect in WALLS:
        r = U.bypass(url, mode="auto", safety=False)
        show(url, r)
        if expect:
            assert r.bypassed and r.destination == expect, f"expected {expect}, got {r.destination}"
        else:
            assert not r.bypassed, "captcha wall must not be reported as bypassed"
    print("\nall wall assertions passed")


if __name__ == "__main__":
    main()
