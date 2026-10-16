"""Dev probe: walk the arolinks flow and print exactly what each step offers.

    python probe_flow.py [url] [max_steps]

Prints, per step: the URL, every visible clickable element (text / href /
onclick / id), any script mentioning telegram, and every window.open or
location the page pushed. Used to find where the real link is released.
"""
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("LB_ALLOW_LOCAL", "1")

import unshorten as U
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "https://arolinks.com/sOl08C"
max_steps = int(sys.argv[2]) if len(sys.argv) > 2 else 40

DUMP = r"""
() => {
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return (r.width > 0 || r.height > 0) && s.display !== 'none' && s.visibility !== 'hidden';
  };
  const text = (el) => (el.innerText || el.value || '').trim().replace(/\s+/g, ' ');
  const nodes = [...document.querySelectorAll('a[href],button,input[type=submit],input[type=button]')]
    .filter(visible)
    .map(el => ({
      tag: el.tagName,
      text: text(el).slice(0, 40),
      href: el.getAttribute('href'),
      onclick: (el.getAttribute('onclick') || '').slice(0, 120),
      id: el.id || '',
      cls: (el.className || '').toString().slice(0, 60),
      html: el.outerHTML.slice(0, 200),
    }));
  const html = document.documentElement.innerHTML;
  const tg = (html.match(/[^"'\s]*telegram[^"'\s]*/gi) || []).slice(0, 6);
  const body = document.body ? document.body.innerText : '';
  return {
    nodes: nodes,
    targets: window.__lbTargets || [],
    telegram: tg,
    steps: (body.match(/step\s*\d+/gi) || []).slice(0, 3),
    title: document.title,
  };
}
"""

hit = re.compile(r"telegram|t\.me", re.I)
seen_urls = set()

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900},
    )
    context.add_init_script(U._BROWSER_INIT)
    page = context.new_page()
    popups = []
    def on_popup(p):
        popups.append(p)
    page.on("popup", on_popup)
    seen_requests = []
    page.on("request", lambda r: seen_requests.append(r.url) if hit.search(r.url) else None)

    page.goto(url, wait_until="domcontentloaded", timeout=45000)

    for step in range(max_steps):
        page.wait_for_timeout(2500)
        info = None
        for _ in range(5):
            try:
                info = page.evaluate(DUMP)
                break
            except Exception:
                page.wait_for_timeout(700)
        if info is None:
            print(f"[{step}] evaluate kept failing (mid-navigation)")
            page.wait_for_load_state("domcontentloaded", timeout=20000)
            continue
        current = page.url
        print(f"\n=== step {step}  {current}")
        print(f"    title={info['title']!r} steps={info['steps']} targets={info['targets'][-3:]}")
        for n in info["nodes"]:
            interesting = (n["id"] in ("btn6", "btn7", "continueBtn")
                           or re.search(r"get\s*link|continue|verify|next", n["text"], re.I)
                           or hit.search(f"{n['href']} {n['onclick']} {n['html']}"))
            if not interesting:
                continue
            flag = "  <== " if hit.search(f"{n['href']} {n['onclick']} {n['html']}") else "      "
            print(f"   {flag}{n['tag']:6} {n['text']!r:32} id={n['id']!r:12} href={n['href']!r}")
            if n["onclick"]:
                print(f"          onclick={n['onclick']}")
            if flag.strip():
                print(f"          html={n['html']}")
        if info["telegram"]:
            print(f"    TELEGRAM in DOM: {info['telegram']}")
        for p in popups:
            try:
                if p.url not in seen_urls:
                    seen_urls.add(p.url)
                    print(f"    POPUP -> {p.url}")
            except Exception:
                pass
        new_reqs = [u for u in seen_requests if u not in seen_urls]
        for u in new_reqs:
            seen_urls.add(u)
            print(f"    REQUEST -> {u}")

        clicked = None
        for _ in range(6):
            clicked = U._flow_click(page, "getlink") or U._flow_click(page, "verify") \
                or U._flow_click(page, "continue")
            if clicked:
                break
            page.wait_for_timeout(2000)
        print(f"    clicked: {clicked}")
        if not clicked:
            print("    nothing clickable left - stopping")
            break

    print("\nfinal url:", page.url)
    for p in popups:
        try:
            print("popup:", p.url)
        except Exception:
            pass
    browser.close()
