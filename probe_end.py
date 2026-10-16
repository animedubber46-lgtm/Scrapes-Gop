"""At the end of the teaser chain, show every link and off-site URL on the page."""
import re
import sys
import urllib.parse

import unshorten as U
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
url = sys.argv[1]

DUMP = r"""
() => {
  const vis = (e) => { const r = e.getBoundingClientRect();
    return (r.width > 0 || r.height > 0) && getComputedStyle(e).display !== 'none'; };
  return [...document.querySelectorAll('a[href],button,input[type=submit],input[type=button]')]
    .filter(vis)
    .map(e => ({tag: e.tagName, text: (e.innerText||e.value||'').trim().slice(0,40),
                href: e.getAttribute('href'), id: e.id || '',
                onclick: (e.getAttribute('onclick')||'').slice(0,100)}));
}
"""

OFFSITE = re.compile(r"https?://(?!mtc1\.thetechhint\.in)[^\s\"'<>\\]+")

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900})
    ctx.add_init_script(U._BROWSER_INIT)
    page = ctx.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    for _ in range(3):
        page.wait_for_timeout(3000)
        for n in page.evaluate(DUMP):
            print(f"  {n['tag']:6} {n['text']!r:34} id={n['id']!r:10} href={str(n['href'])[:60]}"
                  f"{('  onclick=' + n['onclick']) if n['onclick'] else ''}", flush=True)
        html = page.content()
        hits = [h for h in dict.fromkeys(OFFSITE.findall(html))]
        junk = [h for h in hits if not re.search(
            r"(googlesyndication|doubleclick|google-analytics|gstatic|facebook|w3\.org|"
            r"schema\.org|wordpress\.com|fonts\.g|youtube|jquery|bootstrap)", h, re.I)]
        print("  off-site urls:", junk[:15], flush=True)
        print("  targets:", page.evaluate("() => window.__lbTargets || []"), flush=True)
        print("  ---", page.url, flush=True)
    b.close()
