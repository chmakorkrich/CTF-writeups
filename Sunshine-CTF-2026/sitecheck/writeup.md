# SiteCheck — SunshineCTF 2026 (web, 500 pts)

**Flag:** `sun{fr4gm3nt3d_r3fl3ct10ns_1n_th3_futur3}`

## Challenge summary

> SiteCheck is a "web-diagnostics service": you enlist, submit any http(s) URL,
> and an autonomous "inspection drone" flies out to it, times the load, counts
> the resources, and beams back a viewport screenshot.
>
> "The drone politely refuses to inspect internal or local addresses."

The service lives at `https://spaceship.web.2026.sunshinectf.games`.

## Recon

Registering an account (`POST /register` with `username`, `password`, `viewport`)
lands you on `/dashboard`, which has a single form: `POST /scan` with a `url`
field. A successful scan 302-redirects to `/result/<uuid>`, which shows:

- status code, load time, number of files fetched
- a **screenshot** of the page the drone rendered (`/screenshots/<uuid>.png`)
- any error from the drone — notably raw Playwright messages such as
  `page.goto: net::ERR_CONNECTION_REFUSED at ...`, confirming the drone is a
  headless Chromium driven by Playwright.

## Vulnerability 1: SSRF with an incomplete filter

Probing the URL filter:

| URL | Result |
|---|---|
| `http://127.0.0.1/` | blocked |
| `http://localhost/` | blocked |
| `http://0.0.0.0/` | blocked |
| `http://127.1/`, `http://2130706433/`, `http://0x7f000001/` | blocked |
| `http://[::1]/` | **allowed** (connection refused — nothing on :80) |
| `http://169.254.169.254/...` | **allowed** (GCP metadata 403/404) |

The filter enumerates IPv4 loopback spellings but never considers **IPv6
loopback**. Everything after this goes through `http://[::1]/`.

(The box is a GCE instance — `169.254.169.254` answers. The v1 metadata API
returns 403 without the `Metadata-Flavor: Google` header, which a plain
`page.goto` can't set, so that path dead-ends.)

## Vulnerability 2: the drone is authenticated as admin

Port-scanning `[::1]` through the drone (each probe is one `/scan` request):

- `:80`, `:5000`, `:8000`, `:8080`, `:8888` → connection refused
- **`:3000` → HTTP 200**, and the screenshot shows the full SiteCheck app…
  with the top-nav reading `admin — CLEARANCE: OMEGA`.

The drone's browser carries a pre-authenticated **admin** session, and the
app it is browsing is the *real* app on localhost:3000 (the public-facing
site is just a reverse proxy in front of it).

## Exfiltration: read the admin's Personnel File via screenshots

The admin navbar has a **Personnel File** link → `/profile`. It renders a
dossier with three client-side tabs: `overview`, `service-record`,
`clearance`. The tabs are toggled by URL hash, so pointing the drone at:

```
http://[::1]:3000/profile#clearance
```

makes the admin browser render the `Clearance Data` section (marked
`CLASSIFIED`) and screenshot it. The snapshot contains the flag:

```
sun{fr4gm3nt3d_r3fl3ct10ns_1n_th3_futur3}
```

## Attack chain (why the flag name fits)

- **fragmented** — IPv6 loopback (`[::1]`) slips past an IPv4-only SSRF filter
- **reflections** — the drone's *reflected* viewport screenshot is the
  exfiltration channel, and the URL **fragment** (`#clearance`) selects the
  classified tab

## Solver

See `solver.py` — runs the whole chain end to end and OCRs the final
screenshot for the flag (needs `pytesseract` + tesseract, otherwise it just
saves the PNG).

## Mitigations

- Parse URLs and reject **all** non-public IP literals: IPv4 (all notations),
  IPv6 (including IPv4-mapped like `[::ffff:127.0.0.1]`), plus DNS-rebinding
  protection (resolve, then re-check every redirect hop).
- Don't let the crawler hold privileged sessions; use a throwaway profile with
  no cookies for arbitrary-URL scans.
- Keep "inspect a URL" workers on an isolated network with no access to
  internal services or link-local/cloud metadata.
