"""Walk the arolinks flow in a real browser and print what each step offers.

    python walk_flow.py [url]
"""
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import unshorten as U
from playwright.sync_api import sync_playwright

START = sys.argv[1] if len(sys.argv) > 1 else "https://arolinks.com/nyQtXW"

DUMP = """() => {
  const interesting = (el) => {
    const id = (el.id || ''), cls = (el.className || '').toString();
    const text = (el.innerText || el.value || '').trim().replace(/\\s+/g, ' ');
    if (/^(btn\\d+|continue\\w*|getlink\\w*|verify\\w*|step\\w*|getlinkbtn\\w*)$/i.test(id)) return true;
    if (/ce-btn|getlink|step-btn|verify-btn/i.test(cls)) return true;
    if (/^(get\s*link|continue|next|verify|proceed|start|open|download)\b/i.test(text)) return true;
    return false;
  };
  const out = [];
  for (const el of document.querySelectorAll('a[href],button,input[type=submit],input[type=button],[role=button]')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    if (!interesting(el)) continue;
    out.push({
      tag: el.tagName, id: el.id || '', cls: (el.className || '').toString().slice(0, 40),
      text: (el.innerText || el.value || '').trim().replace(/\\s+/g, ' ').slice(0, 34),
      href: (el.getAttribute('href') || '').slice(0, 80),
      disabled: !!el.disabled, onclick: (el.getAttribute('onclick') || '').slice(0, 40),
    });
  }
  const body = document.body ? document.body.innerText : '';
    return {
      steps: (body.match(/step\\s*\\d+/gi) || []).slice(0, 4),
      waiting: (body.match(/please wait[^\\n]{0,20}|\\d+\\s*seconds?/gi) || []).slice(0, 3),
      items: out,
    };
}"""

CLICK = """(rx) => {
  const order = ['get link', 'verify', 'continue', 'next', 'proceed', 'start', 'open'];
  const nodes = [...document.querySelectorAll('a[href],button,input[type=submit],input[type=button],[role=button]')];
  const usable = nodes.filter(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return false;
    if (el.disabled || el.dataset.walked) return false;
    if (/scanner/i.test(el.getAttribute('onclick') || '')) return false;
    const t = (el.innerText || el.value || '').trim().replace(/\\s+/g, ' ');
    if (/skip\\s*to\\s*content/i.test(t)) return false;
    if (/screen-reader-text|skip-link/.test((el.className || '').toString())) return false;
    if (/^#(content|main|top)$/i.test(el.getAttribute('href') || '')) return false;
    return new RegExp(rx, 'i').test(t) || /^(btn\\d+|continueBtn|getlink\\w*)$/i.test(el.id || '')
        || /ce-btn/i.test((el.className || '').toString());
  });
  for (const word of order) {
    const hit = usable.find(el => (el.innerText || el.value || '').trim().toLowerCase().startsWith(word))
      || usable.find(el => /^(btn\\d+|continueBtn|getlink\\w*)$/i.test(el.id || ''));
    if (hit) {
      hit.dataset.walked = '1';
      const label = (hit.innerText || hit.value || hit.id).trim().slice(0, 26);
      hit.click();
      return label;
    }
  }
  return null;
}"""

VOCAB = r"(get\s*link|continue|next|verify|proceed|start|open|download)"


def safe_eval(page, expr, tries=3):
    for _ in range(tries):
        try:
            return page.evaluate(expr, VOCAB) if "rx" in expr or expr is CLICK else page.evaluate(expr)
        except Exception as exc:
            if "destroyed" in str(exc) or "navigation" in str(exc):
                time.sleep(1.0)
                continue
            raise
    return {"steps": [], "waiting": [], "items": []}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = browser.new_context(user_agent=U.USER_AGENT, viewport={"width": 1366, "height": 900})
        ctx.add_init_script(U._BROWSER_INIT)
        page = ctx.new_page()
        ledger = []
        page.on("request", lambda r: ledger.append(r.url))
        page.goto(START, wait_until="domcontentloaded", timeout=45000)

        for i in range(30):
            time.sleep(1.5)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=8000)
            except Exception:
                pass
            info = safe_eval(page, DUMP)
            print(f"\n--- {i+1}. {page.url}")
            if info["steps"]:
                print("    steps:", info["steps"], "waiting:", info["waiting"])
            for item in info["items"]:
                line = (f"    <{item['tag']}> id={item['id']!r} cls={item['cls']!r} "
                        f"text={item['text']!r} href={item['href']!r} dis={item['disabled']} "
                        f"onclick={item['onclick']!r}")
                print(line.encode("ascii", "replace").decode("ascii"))

            final = [x for x in info["items"]
                     if re.search(r"get\s*link", x["text"], re.I) and x["href"].startswith("http")]
            getlink_any = [x for x in info["items"] if re.search(r"get\s*link", x["text"], re.I)]
            if getlink_any:
                print("\n*** GET LINK BUTTON FOUND:")
                for item in getlink_any:
                    print(f"    <{item['tag']}> text={item['text']!r}")
                    print(f"    href = {item['href']}")
                if final:
                    print("\n*** DESTINATION:", final[0]["href"])
                break
            clicked = safe_eval(page, CLICK)
            print("    clicked:", clicked)
            if not clicked:
                print("    nothing to click - stopping")
                break

        print("\nOFF-SITE LEDGER (non article hosts):")
        for req in ledger:
            if U.looks_like_destination(req):
                print("   ", req[:130])
        browser.close()


if __name__ == "__main__":
    main()
