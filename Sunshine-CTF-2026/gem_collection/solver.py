#!/usr/bin/env python3
import os
import sys
import base64
import re
from oletools.olevba import VBA_Parser

def solve(pptm_path="gem_collection.pptm"):
    if not os.path.exists(pptm_path):
        # Check parent directory
        parent_path = os.path.join("..", pptm_path)
        if os.path.exists(parent_path):
            pptm_path = parent_path
        else:
            print(f"[-] File not found: {pptm_path}")
            sys.exit(1)

    print(f"[*] Parsing VBA macros in {pptm_path}...")
    vba_parser = VBA_Parser(pptm_path)
    
    if not vba_parser.detect_vba_macros():
        print("[-] No VBA macros found.")
        sys.exit(1)

    for (filename, stream_path, vba_filename, vba_code) in vba_parser.extract_macros():
        # Look for encoded Base64 string in the macro
        match = re.search(r'encoded\s*=\s*"([A-Za-z0-9+/=]+)"', vba_code)
        if match:
            encoded_b64 = match.group(1)
            try:
                # PowerShell EncodedCommand uses UTF-16LE
                decoded = base64.b64decode(encoded_b64).decode("utf-16le")
                print(f"[+] Decoded PowerShell script:\n{decoded}")
                
                # Extract flag matching sun{...}
                flag_match = re.search(r'sun\{[^}]+\}', decoded)
                if flag_match:
                    flag = flag_match.group(0)
                    print(f"\n[+] Flag: {flag}")
                    return flag
            except Exception as e:
                print(f"[-] Error decoding: {e}")

    print("[-] Flag not found.")
    return None

if __name__ == "__main__":
    pptm_file = sys.argv[1] if len(sys.argv) > 1 else "gem_collection.pptm"
    solve(pptm_file)
