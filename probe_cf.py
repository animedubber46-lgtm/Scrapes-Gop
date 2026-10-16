"""Which Chromium setup gets past the Cloudflare interstitial?

Tries a few launch profiles against one URL and prints where each one ends up.
"""
import sys

import unshorten as U
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

url = sys.argv[1] if len(sys.argv) > 1 else "https://kogap.xyz/demo"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

PROFILES = {
    "headless-default": dict(headless=True, args=[]),
    "headless-stealth": dict(headless=True, args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--no-sandbox"]),
    "headed": dict(headless=False, args=["--disable-blink-features=AutomationControlled"]),
}

with sync_playwright() as pw:
    for name, cfg in PROFILES.items():
        try:
            b = pw.chromium.launch(**cfg)
            ctx = b.new_context(user_agent=UA, viewport={"width": 1280, "height": 900},
                                locale="en-US")
            ctx.add_init_script(U._BROWSER_INIT)
            ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            for i in range(10):
                page.wait_for_timeout(2500)
                try:
                    title = (page.title() or "")[:40]
                except Exception:
                    continue
                if "just a moment" not in title.lower() and "attention" not in title.lower():
                    break
            try:
                title = (page.title() or "")[:40]
            except Exception:
                title = "<unreadable>"
            print(f"{name:18} -> {page.url[:80]} | {title!r}", flush=True)
            b.close()
        except Exception as exc:
            print(f"{name:18} -> ERROR {type(exc).__name__}: {str(exc)[:70]}", flush=True)
