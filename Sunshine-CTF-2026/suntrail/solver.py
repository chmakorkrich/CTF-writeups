#!/usr/bin/env python3
import os
import sys

# Keyboard transition map based on the physical staggered QWERTY layout
# Following arrows:
# SE (\u2198): down-right
# R  (\u2192): right
# NW (\u2196): up-left
# STOP (\u25a0): end of trail

KEYBOARD_TRANSITIONS = {
    'Q': ('SE', 'A'),
    'A': ('SE', 'Z'),
    'Z': ('R',  'X'),
    'X': ('NW', 'S'),
    'S': ('NW', 'W'),
    'W': ('R',  'E'),
    'E': ('SE', 'D'),
    'D': ('SE', 'C'),
    'C': ('R',  'V'),
    'V': ('NW', 'F'),
    'F': ('NW', 'R'),
    'R': ('R',  'T'),
    'T': ('SE', 'G'),
    'G': ('SE', 'B'),
    'B': ('R',  'N'),
    'N': ('NW', 'H'),
    'H': ('STOP', None),
}

def parse_klc(klc_path="suntrail.klc"):
    if not os.path.exists(klc_path):
        parent_path = os.path.join("..", klc_path)
        if os.path.exists(parent_path):
            klc_path = parent_path
        else:
            print(f"[-] File not found: {klc_path}")
            sys.exit(1)

    key_data = {}
    with open(klc_path, "r", encoding="utf-8", errors="ignore") as f:
        in_layout = False
        for line in f:
            line = line.strip()
            if line.startswith("LAYOUT"):
                in_layout = True
                continue
            if line.startswith("ENDKBD"):
                break
            if in_layout and line and not line.startswith("//"):
                parts = line.split()
                if len(parts) >= 5 and parts[1] != "SPACE":
                    sc, vk, cap, state0, state1 = parts[0], parts[1], parts[2], parts[3], parts[4]
                    arrow_char = chr(int(state0, 16))
                    shift_char = chr(int(state1, 16))
                    key_data[vk] = {
                        "arrow": arrow_char,
                        "arrow_hex": state0,
                        "char": shift_char,
                    }
    return key_data

def solve(klc_path="suntrail.klc"):
    key_data = parse_klc(klc_path)
    
    print("[*] Following the suntrail keyboard path...")
    current_key = "Q"
    flag_chars = []
    trail = []

    while current_key:
        info = key_data.get(current_key)
        if not info:
            break
        char = info["char"]
        arrow = info["arrow"]
        flag_chars.append(char)
        direction, next_key = KEYBOARD_TRANSITIONS[current_key]
        trail.append(f"{current_key} ('{char}', {arrow} {direction})")
        current_key = next_key

    print(" -> ".join(trail))
    flag = "".join(flag_chars)
    print(f"\n[+] Flag: {flag}")
    return flag

if __name__ == "__main__":
    klc_file = sys.argv[1] if len(sys.argv) > 1 else "suntrail.klc"
    solve(klc_file)
