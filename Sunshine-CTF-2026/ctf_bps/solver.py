#!/usr/bin/env python3
import os
import sys
import struct

def decode_bps_number(data, offset):
    res = 0
    shift = 1
    while True:
        x = data[offset]
        offset += 1
        res += (x & 0x7f) * shift
        if (x & 0x80) != 0:
            break
        shift <<= 7
        res += shift
    return res, offset

def solve(bps_path="ctf.bps"):
    if not os.path.exists(bps_path):
        parent_path = os.path.join("..", bps_path)
        if os.path.exists(parent_path):
            bps_path = parent_path
        else:
            print(f"[-] File not found: {bps_path}")
            sys.exit(1)

    print(f"[*] Parsing BPS patch: {bps_path}...")
    with open(bps_path, "rb") as f:
        data = f.read()

    if data[:4] != b"BPS1":
        print("[-] Invalid BPS file header.")
        sys.exit(1)

    offset = 4
    src_size, offset = decode_bps_number(data, offset)
    dst_size, offset = decode_bps_number(data, offset)
    meta_size, offset = decode_bps_number(data, offset)

    if meta_size > 0:
        offset += meta_size

    # Extract target payload bytes written by patch
    target_data = []
    while offset < len(data) - 12:
        action, offset = decode_bps_number(data, offset)
        command = action & 3
        length = (action >> 2) + 1

        if command == 1:  # TargetRead
            chunk = data[offset:offset+length]
            target_data.append(chunk)
            offset += length
        elif command in (2, 3):  # SourceCopy or TargetCopy
            _, offset = decode_bps_number(data, offset)

    # Search for XOR encrypted flag (XOR key 0x5A) in the injected SNES bytecode
    print("[*] Searching for XOR-encrypted payload...")
    for chunk in target_data:
        for i in range(len(chunk)):
            decrypted = bytes([b ^ 0x5A for b in chunk[i:]])
            if decrypted.startswith(b"sun{"):
                flag = decrypted.split(b"\x5A")[0].decode("ascii", errors="ignore")
                print(f"[+] Found encrypted SNES payload at offset {i} (XOR key: 0x5A)")
                print(f"\n[+] Flag: {flag}")
                return flag

    print("[-] Flag not found.")
    return None

if __name__ == "__main__":
    bps_file = sys.argv[1] if len(sys.argv) > 1 else "ctf.bps"
    solve(bps_file)
