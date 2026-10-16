"""Local fixture: mimics a real shortener wall so the bypass can be verified.

page 1  /code1  -> 5s countdown, "Get Link" button appears, opens the
                   destination in a popup via window.open after the timer.
page 2  /code2  -> "Continue" link to a next-step page on the same host.
page 3  /code2/step2 -> destination only in a base64 encoded JS variable.
page 4  /code3  -> meta refresh to a plain redirector.
page 5  /code4  -> captcha gate, nothing to release (must be reported, not faked).
"""
import base64
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEST = "https://example.com/destination-page"
STEPS = {}


def _page(body: str) -> bytes:
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Shortener</title></head><body>{body}</body></html>""".encode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        cookie = self.headers.get("Cookie", "")

        if path == "/code1":
            body = """
            <h1>Please wait <span id="t">5</span> seconds</h1>
            <button id="go" style="display:none">Get Link</button>
            <script>
              let s = 5;
              const tick = setInterval(() => {
                s--; document.getElementById('t').textContent = s;
                if (s <= 0) {
                  clearInterval(tick);
                  const b = document.getElementById('go');
                  b.style.display = 'block';
                  b.onclick = () => window.open("%s", "_blank");
                }
              }, 1000);
            </script>""" % DEST
            return self._send(_page(body))

        if path == "/code2":
            if "seen2" not in cookie:
                self._send(_page('<a href="/code2/step2">Continue</a>'), cookie="seen2=1")
                return
            return self._send(_page("<p>thanks</p>"))

        if path == "/code2/step2":
            encoded = base64.b64encode(DEST.encode()).decode()
            body = f"""<script>var url = atob("{encoded}");
              document.write('<a href="' + url + '">Get Link</a>');</script>"""
            return self._send(_page(body))

        if path == "/code3":
            return self._send(_page(f'<meta http-equiv="refresh" content="0; url={DEST}">'))

        if path == "/code4":
            return self._send(_page("""
              <h2>Verifying you are human</h2>
              <div class="g-recaptcha" data-sitekey="x"></div>
              <script src="https://www.google.com/recaptcha/api.js"></script>"""))

        if path == "/code5":
            # destination is not in the HTML at all: only a click + XHR reveals it
            body = """
            <h1>Preparing your link</h1>
            <button id="go" disabled>Get Link</button>
            <script>
              setTimeout(() => { document.getElementById('go').disabled = false; }, 4000);
              document.getElementById('go').onclick = async () => {
                const r = await fetch('/api/link');
                const j = await r.json();
                window.open(j.url, '_blank');
              };
            </script>"""
            return self._send(_page(body))

        if path == "/api/link":
            payload = json.dumps({"url": DEST}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if path == "/code6":
            # countdown, then the top frame itself navigates off-site
            body = f"""
            <p>Redirecting in <span id="t">4</span> seconds</p>
            <script>
              let s = 4;
              const tick = setInterval(() => {{
                s--; document.getElementById('t').textContent = s;
                if (s <= 0) {{ clearInterval(tick); window.location.href = "{DEST}"; }}
              }}, 1000);
            </script>"""
            return self._send(_page(body))

        if path == "/redirector":
            self.send_response(302)
            self.send_header("Location", DEST)
            self.end_headers()
            return

        self.send_error(404)

    def _send(self, body: bytes, cookie: str = ""):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8099), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print("fixture walls on http://127.0.0.1:8099/{code1,code2,code3,code4,redirector}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
