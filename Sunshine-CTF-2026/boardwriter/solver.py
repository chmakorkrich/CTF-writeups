#!/usr/bin/env python3
import os
import sys

def parse_deadkeys(klc_path="boardwriter.klc"):
    if not os.path.exists(klc_path):
        parent_path = os.path.join("..", klc_path)
        if os.path.exists(parent_path):
            klc_path = parent_path
        else:
            print(f"[-] File not found: {klc_path}")
            sys.exit(1)

    print(f"[*] Reading {klc_path}...")
    with open(klc_path, "rb") as f:
        raw = f.read()

    # Try utf-16 / utf-16le / utf-8
    text = ""
    for enc in ["utf-16", "utf-16le", "utf-8", "latin1"]:
        try:
            text = raw.decode(enc)
            break
        except Exception:
            pass

    deadkeys = {}
    current_dk = None

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("DEADKEY"):
            parts = line.split()
            current_dk = parts[1]
            deadkeys[current_dk] = {}
        elif current_dk and line and not line.startswith("//"):
            parts = line.split()
            if len(parts) >= 2:
                key_char = chr(int(parts[0], 16))
                next_val = parts[1]
                deadkeys[current_dk][key_char] = next_val

    return deadkeys

def solve(klc_path="boardwriter.klc"):
    deadkeys = parse_deadkeys(klc_path)
    
    # Starting deadkey defined on OEM_3 is U+0060
    cur_dk = "0060"
    flag_chars = []
    chain = []

    print("[*] Tracing deadkey chain starting from U+0060...")
    while cur_dk in deadkeys:
        char, nxt = list(deadkeys[cur_dk].items())[0]
        flag_chars.append(char)
        chain.append(f"DEADKEY {cur_dk} + '{char}' -> {nxt}")
        if nxt.endswith("@"):
            cur_dk = nxt.rstrip("@")
        else:
            terminal_symbol = chr(int(nxt, 16))
            chain.append(f"Output: {terminal_symbol} (U+{nxt})")
            break

    for step in chain:
        print(f"  {step}")

    flag = "".join(flag_chars)
    print(f"\n[+] Flag: {flag}")
    return flag

if __name__ == "__main__":
    klc_file = sys.argv[1] if len(sys.argv) > 1 else "boardwriter.klc"
    solve(klc_file)
