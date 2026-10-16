# LinkBypasser (demo)

Paste a shortened link, get the **real destination**. Countdown pages, "Get Link"
buttons, ad walls, multi-step flows and base64/JS-obfuscated targets are all
cleared - the shortener page is never handed back as if it were the answer.

## Run

```bash
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000
```

Browser lane needs Chromium once:

```bash
python -m playwright install chromium
```

To try it end to end against the bundled fake shortener walls (two terminals):

```bash
python test_wall.py      # serves /code1 ... /code6 on 127.0.0.1:8099
python run_local.py      # app with the private-host guard relaxed for localhost
python run_local.py 5055 # ... or on another port if 5000 is taken
```

## How the bypass works (`unshorten.py`)

**HTTP lane** - fast, no browser:

1. Normalise the URL, reject private/loopback hosts.
2. Walk the chain hop by hop (`allow_redirects=False`) inside **one cookie jar**
   (`curl_cffi` with Chrome TLS impersonation, falling back to `requests`).
   A single jar matters: multi-step walls set a cookie on page 1 and expect it
   back on page 2.
3. On a wall page, mine the HTML for the target: `meta refresh`, cross-host
   `canonical`, `window.open` / `location=`, `var url|link|dest = "..."`,
   `atob("...")`, `unescape(...)`, "Get Link"/"Continue" anchors, `data-*`
   attributes, iframes, JSON `url`/`destination` keys, and bare URLs in
   non-HTML responses.
4. Score and filter candidates, because a wall page is full of decoys:
   ad/track/CDN hosts are hard-blocked, social hosts only count when the
   redirect mechanism is unambiguous, site chrome (`/login`, `/pages/...`) is
   never treated as a next step, and asset URLs are dropped.
5. Decide whether the page is a wall by **score**, not a single pattern, so a
   small real landing page is not mistaken for a wall.

**Browser lane** - headless Chromium, for walls the HTTP pass cannot clear:

- fast-forwards `setTimeout` / `setInterval` so countdowns finish instantly,
- stubs `window.open` and records every `location.href` assignment,
- clicks `Get Link` / `Continue` / `Next` / `Skip` / `Proceed` as a human would,
- watches the network ledger and the popup list for any off-site URL,
- blocks images/fonts/media and ad networks, which cuts a step from ~15s to ~2s,
- reloads a page once if it stops changing, and gives up with a warning rather
  than burning the budget.

**Multi-step campaigns (the arolinks family).** These do not redirect - they
walk the visitor through article pages tagged `Step 1`, `Step 2` ... each with a
fake `Verify` progress scanner and a `Continue` button (`#btn7 -> /readmore`),
through thin `Landing..` tracker pages, and only reveal the destination in the
href of the final `Get Link` button. So the lane:

- keeps walking **after** it leaves the shortener's domain while a `Step N`
  marker or a flow button is on screen,
- presses `Verify` then `Continue` with a real (trusted) mouse click, because
  these widgets ignore synthetic `el.click()`,
- lifts the full-screen ad overlay off the page first - ad networks are blocked,
  so the overlay never fills and would otherwise swallow every click,
- when the click is still swallowed by the ad handler, `location.assign()`s the
  same `/readmore` href from inside the page, which skips the click listeners
  and keeps the walk moving,
- ignores the decoys sitting in the article body (`VERIFY ... CAPACITY` scanner
  buttons, the `Skip to content` accessibility link, ad anchors),
- only accepts an off-site page as the destination when nothing was clicked and
  the page is not a `noindex` "Landing.." hop - otherwise a mid-flow article
  would be mistaken for the answer,
- trusts a popup **only** after `Get Link` was pressed, because every `Continue`
  also fires an ad popup at a decoy article,
- returns the `Get Link` href, or the URL that button released.

Once a link is really released (`Get Link` href, or a target the page handed
over) it is accepted as-is, so real destinations such as `telegram.me/+...`,
`discord.gg/...` or `wa.me/...` invites are never mistaken for shorteners.

One visit takes ~40s because the campaign really is several page loads plus
countdowns. The destination rotates per visit, so the same short link can
return a different invite each time.

Captchas are never faked. If the destination sits behind one, the tool reports
the gate (`captcha`, `safelink`, `cloudflare`, `shortener-wall`, `unresolved`)
and shows the page it stopped on, instead of handing back a shortener page as if
it were the answer.

**Orchestration** - `bypass(url, mode)`:

| mode | behaviour |
|---|---|
| `auto` (default) | HTTP pass, then the browser lane if a wall is still in front |
| `http` | HTTP pass only, instant |
| `browser` | browser lane only, slowest but clears the most |

If the destination is still not released, the tool says so and names the gate
instead of returning the shortener's page.

## API

| Route | Method | Body / query | Returns |
|---|---|---|---|
| `/api/expand` | POST | `{"url": "...", "mode": "auto"}` | one result |
| `/api/bulk` | POST | `{"text": "one url per line", "mode": "auto"}` | `{count, bypassed, results[]}` (max 25) |
| `/api/health` | GET | – | `{"status":"ok"}` |

```json
{
  "input_url": "https://arolinks.com/xxxxxx",
  "ok": true, "bypassed": true,
  "destination": "https://real-target.example/page",
  "final_url": "https://real-target.example/page",
  "method": "browser", "lane": "http+browser", "protection": null,
  "hops": 6, "elapsed_ms": 8421,
  "chain": [{"index": 1, "url": "...", "status": 301, "type": "redirect", "location": "..."}],
  "preview": {"title": "...", "description": "...", "image": "...", "favicon": "..."}
}
```

`bypassed: false` means no destination was reached; `protection` says why.

## Tests

```bash
python test_engine.py    # HTTP lane, public links
python test_wall.py &    # fake shortener walls
python test_bypass.py    # 6 wall types, both lanes, with assertions
python test_live.py      # a real arolinks campaign link, end to end (asserts)
python walk_flow.py      # dev tool: print every button of every flow step
python probe_flow.py     # dev tool: same walk, with a DOM dump per step
python run_local.py &
python test_api.py       # the same through the web API
```

`test_live.py https://arolinks.com/sOl08C` asserts the exact destination of that
campaign link (`https://telegram.me/+aBh3g24AwuMwZjE9`); `test_api.py` takes an
optional base URL when port 5000 is already in use.

`test_wall.py` serves: a `window.open` wall, a cookie + two-step + base64 wall,
a meta-refresh wall, a wall whose target only appears after a click + XHR
(browser lane only), a countdown wall, and a captcha wall that must be reported
as *not* bypassed.

Only expand links you are allowed to visit, and respect the target site's terms.
