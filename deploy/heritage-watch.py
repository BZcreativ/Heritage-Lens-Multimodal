#!/usr/bin/env python3
"""Heritage Lens abuse watcher.

Follows the heritage-api access log (journald) in real time, tracks per-IP
request rates, and pushes an ntfy alert when traffic looks abusive.

Read-only: it never blocks. Blocking is handled at Cloudflare's edge (host
firewall is useless here because traffic arrives via the tunnel as localhost).

Config via environment (see /etc/heritage-watch.env):
  NTFY_SERVER   default https://ntfy.sh
  NTFY_TOPIC    required — the private topic to publish alerts to
  HW_API_FLOOD  /api/* requests per IP per 60s that trips an alert (default 60)
  HW_ERR_SCAN   4xx responses per IP per 60s that trips an alert  (default 40)
  HW_SENSITIVE  POST /api/upload|/api/ingest per IP per 600s      (default 5)
  HW_COOLDOWN   seconds to suppress repeat alerts per IP+rule      (default 900)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import urllib.request
from collections import defaultdict, deque

NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")

# (window_seconds, threshold)
API_FLOOD = (60, int(os.environ.get("HW_API_FLOOD", "60")))
ERR_SCAN = (60, int(os.environ.get("HW_ERR_SCAN", "40")))
SENSITIVE = (600, int(os.environ.get("HW_SENSITIVE", "5")))
COOLDOWN = int(os.environ.get("HW_COOLDOWN", "900"))
SWEEP = 600  # periodic cleanup of idle IP buckets

# uvicorn access line, e.g.:  INFO:  126.158.203.47:0 - "GET /api/status HTTP/1.1" 200 OK
LINE_RE = re.compile(r'(\d+\.\d+\.\d+\.\d+):\d+ - "([A-Z]+) ([^"]*?) HTTP/[\d.]+" (\d+)')

RULES = {"api": API_FLOOD, "err": ERR_SCAN, "sensitive": SENSITIVE}
SUMMARY = {
    "api": "API request flood",
    "err": "path scanning (4xx burst)",
    "sensitive": "repeated upload/ingest",
}

events: dict[str, dict[str, deque]] = {r: defaultdict(deque) for r in RULES}
last_alert: dict[tuple[str, str], float] = {}


def prune(dq: deque, window: int, now: float) -> None:
    while dq and now - dq[0] > window:
        dq.popleft()


def notify(title: str, msg: str, priority: str = "default", tags: str = "") -> None:
    if not NTFY_TOPIC:
        print(f"[no NTFY_TOPIC] {title}: {msg}", file=sys.stderr)
        return
    req = urllib.request.Request(
        f"{NTFY_SERVER}/{NTFY_TOPIC}",
        data=msg.encode(),
        headers={"Title": title, "Priority": priority, "Tags": tags},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as exc:  # never let a failed push kill the watcher
        print(f"ntfy publish failed: {exc}", file=sys.stderr)


def maybe_alert(rule: str, ip: str, now: float) -> None:
    window, threshold = RULES[rule]
    dq = events[rule][ip]
    prune(dq, window, now)
    if len(dq) < threshold:
        return
    key = (rule, ip)
    if now - last_alert.get(key, 0.0) < COOLDOWN:
        return
    last_alert[key] = now
    notify(
        f"Heritage Lens: {SUMMARY[rule]}",
        f"IP {ip} — {len(dq)} events in {window}s\nhttps://heritagelens.xyz",
        priority="high",
        tags="rotating_light",
    )


def sweep(now: float) -> None:
    for rule, (window, _) in RULES.items():
        for ip in list(events[rule]):
            prune(events[rule][ip], window, now)
            if not events[rule][ip]:
                del events[rule][ip]
    for key in list(last_alert):
        if now - last_alert[key] > COOLDOWN:
            del last_alert[key]


def main() -> None:
    notify(
        "Heritage Lens watcher started",
        f"Monitoring heritage-api. flood>{API_FLOOD[1]}/60s, "
        f"4xx>{ERR_SCAN[1]}/60s, upload-ingest>{SENSITIVE[1]}/600s.",
        priority="low",
        tags="white_check_mark",
    )
    proc = subprocess.Popen(
        ["journalctl", "-u", "heritage-api", "-f", "-n", "0", "-o", "cat"],
        stdout=subprocess.PIPE,
        text=True,
    )
    last_sweep = time.time()
    for line in proc.stdout:  # type: ignore[union-attr]
        m = LINE_RE.search(line)
        if not m:
            continue
        ip, method, path, status = m.group(1), m.group(2), m.group(3), int(m.group(4))
        now = time.time()

        if path.startswith("/api/"):
            events["api"][ip].append(now)
            maybe_alert("api", ip, now)
        if 400 <= status < 500:
            events["err"][ip].append(now)
            maybe_alert("err", ip, now)
        if method == "POST" and (path.startswith("/api/upload") or path.startswith("/api/ingest")):
            events["sensitive"][ip].append(now)
            maybe_alert("sensitive", ip, now)

        if now - last_sweep > SWEEP:
            sweep(now)
            last_sweep = now


if __name__ == "__main__":
    main()
