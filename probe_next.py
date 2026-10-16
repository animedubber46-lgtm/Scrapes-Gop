"""Walk the /page/N/ teaser chain: click Next until the page stops offering it."""
import re
import sys

import unshorten as U
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

url = sys.argv[1] if len(sys.argv) > 1 else "https://shortxlinks.com/demo"
hops = int(sys.argv[2]) if len(sys.argv) > 2 else 14

NEXT = r"""
() => {
  const nodes = [...document.querySelectorAll('a[href],button')].filter(e => {
    const r = e.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  });
  const hit = nodes.find(e => /^\s*(next|continue|[\u2192\u00bb>]+)\s*$/i.test((e.innerText||'').trim()))
    || nodes.find(e => /next/i.test((e.innerText||'')) && /\/page\//i.test(e.getAttribute('href')||''));
  if (!hit) return null;
  hit.dataset.lbTarget = '1';
  hit.scrollIntoView({block:'center'});
  const r = hit.getBoundingClientRect();
  return { href: hit.href || hit.getAttribute('href'), x: r.left + r.width/2, y: r.top + r.height/2 };
}
"""

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    ctx = b.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900})
    ctx.add_init_script(U._BROWSER_INIT)
    page = ctx.new_page()
    page.on("popup", lambda p: print("POPUP:", p.url, flush=True))
    page.goto(url, wait_until="domcontentloaded", timeout=45000)

    for i in range(hops):
        page.wait_for_timeout(2500)
        title = page.title()
        print(f"[{i}] {page.url[:90]} | {title[:40]}", flush=True)
        try:
            info = U._flow_dump(page)
        except Exception:
            info = {}
        if info.get("getLink"):
            print("GET LINK:", info["getLink"], flush=True)
            break
        try:
            nxt = page.evaluate(NEXT)
        except Exception as exc:
            print("   eval failed:", str(exc)[:80], flush=True)
            continue
        if not nxt:
            print("   no Next here", flush=True)
            continue
        print(f"   next -> {nxt['href']}", flush=True)
        page.mouse.click(nxt["x"], nxt["y"], delay=60)
        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass
    print("final:", page.url, flush=True)
    b.close()
