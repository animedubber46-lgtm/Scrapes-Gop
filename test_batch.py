"""Run every link in message.txt through the engine and report what still fails.

    python test_batch.py                       # all links, auto mode
    python test_batch.py --workers 6
    python test_batch.py --only-failed         # re-run whatever failed last time
    python test_batch.py --mode browser        # force one lane
    python test_batch.py --limit 10            # quick smoke run

Results land in batch_results.jsonl (one line per link, appended) and a summary
is printed grouped by failure signature.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import unshorten as U

RESULTS = "batch_results.jsonl"
LIST = "message.txt"


def read_links(path: str = LIST) -> list[str]:
    if not os.path.exists(path):
        sys.exit(f"{path} not found")
    out, seen = [], set()
    for line in open(LIST, encoding="utf-8", errors="replace"):
        url = line.strip()
        if url and not url.startswith("#") and url not in seen:
            seen.add(url)
            out.append(url)
    return out


def load_previous() -> dict[str, dict]:
    if not os.path.exists(RESULTS):
        return {}
    prev = {}
    for line in open(RESULTS, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        prev[row["url"]] = row           # later lines win
    return prev


def signature(row: dict) -> str:
    """Group failures by cause so one fix can cover a whole family."""
    if row.get("bypassed"):
        return "ok"
    if row.get("error"):
        return "error: " + row["error"][:40]
    prot = row.get("protection") or "-"
    hops = row.get("hops") or 0
    last = (row.get("chain") or [{}])[-1].get("url", "")
    return f"{prot} hops={hops} last={U._root(last) or '-'}"


def one(url: str, mode: str) -> dict:
    started = time.perf_counter()
    try:
        r = U.bypass(url, mode=mode)
        row = r.to_dict()
    except Exception as exc:                     # never let one link kill the run
        row = {"input_url": url, "bypassed": False, "error": f"{type(exc).__name__}: {exc}",
               "protection": None, "chain": [], "hops": 0, "lane": "-", "method": "-",
               "elapsed_ms": 0, "destination": None, "final_url": None}
    row["url"] = url
    row["elapsed_ms"] = row.get("elapsed_ms") or int((time.perf_counter() - started) * 1000)
    with open(RESULTS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--mode", default="auto", choices=["auto", "http", "browser"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only-failed", action="store_true")
    ap.add_argument("--timeout", type=int, default=260)
    ap.add_argument("--file", default=LIST)
    args = ap.parse_args()

    links = read_links(args.file)
    if args.only_failed:
        prev = load_previous()
        links = [u for u in links if not prev.get(u, {}).get("bypassed")]
    if args.limit:
        links = links[: args.limit]

    print(f"{len(links)} links, mode={args.mode}, workers={args.workers}", flush=True)
    done = ok = 0
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(one, url, args.mode): url for url in links}
        for fut in as_completed(futures):
            url = futures[fut]
            try:
                row = fut.result(timeout=args.timeout)
            except Exception as exc:
                row = {"url": url, "bypassed": False, "protection": "harness-timeout",
                       "error": str(exc)[:60], "hops": 0, "lane": "-",
                       "elapsed_ms": args.timeout * 1000, "destination": None,
                       "chain": []}
            done += 1
            ok += bool(row.get("bypassed"))
            dest = (row.get("destination") or row.get("error") or "-")
            print(f"[{done:3}/{len(links)}] {'OK ' if row.get('bypassed') else 'FAIL'} "
                  f"{url[:44]:44} {str(row.get('protection')):14} "
                  f"{row.get('elapsed_ms', 0) // 1000:3}s -> {dest[:58]}", flush=True)

    print(f"\n{ok}/{done} bypassed in {time.perf_counter() - started:.0f}s", flush=True)
    prev = load_previous()
    groups: dict[str, list[str]] = {}
    for url in links:
        groups.setdefault(signature(prev.get(url, {})), []).append(url)
    print("\n== grouped by cause ==")
    for sig, urls in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"\n[{len(urls):3}] {sig}")
        for u in urls[:12]:
            print(f"      {u}")
        if len(urls) > 12:
            print(f"      ... +{len(urls) - 12} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
