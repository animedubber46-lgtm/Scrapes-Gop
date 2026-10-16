import requests

for p in ["code1", "code4"]:
    try:
        r = requests.get("http://127.0.0.1:8099/" + p, timeout=10)
        print(p, r.status_code, len(r.text), flush=True)
    except Exception as exc:
        print(p, "ERR", exc, flush=True)
