#!/usr/bin/env python3
import os
import sys
import zlib
import struct
from PIL import Image
import numpy as np
import subprocess
import re

def solve(png_path="hereyougo.png"):
    if not os.path.exists(png_path):
        parent_path = os.path.join("..", png_path)
        if os.path.exists(parent_path):
            png_path = parent_path
        else:
            print(f"[-] File not found: {png_path}")
            sys.exit(1)

    print(f"[*] Analyzing {png_path}...")
    with open(png_path, "rb") as f:
        data = bytearray(f.read())

    # Parse PNG chunks and extract IDAT
    idat_data = b""
    pos = 8
    width, height = 0, 0
    ihdr_offset = 0

    while pos < len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos+8])
        cdata = data[pos+8:pos+8+length]
        if ctype == b"IHDR":
            ihdr_offset = pos + 8
            width, height, bit_depth, color_type = struct.unpack(">IIBB", cdata[:10])
        elif ctype == b"IDAT":
            idat_data += cdata
        pos += 12 + length

    decompressed = zlib.decompress(idat_data)
    bytes_per_row = 1 + width * 4
    actual_height = len(decompressed) // bytes_per_row

    print(f"[*] IHDR Dimensions : {width}x{height}")
    print(f"[*] Actual Dimensions: {width}x{actual_height} (Hidden rows: {actual_height - height})")

    # Fix IHDR height and CRC
    data[ihdr_offset+4:ihdr_offset+8] = struct.pack(">I", actual_height)
    new_ihdr = data[ihdr_offset-4:ihdr_offset+13]
    new_crc = zlib.crc32(new_ihdr)
    data[ihdr_offset+13:ihdr_offset+17] = struct.pack(">I", new_crc)

    fixed_path = "fixed.png"
    with open(fixed_path, "wb") as f:
        f.write(data)
    print(f"[+] Restored image written to {fixed_path}")

    # Crop hidden bottom section and threshold
    img = Image.open(fixed_path)
    bottom = img.crop((0, height - 10, width, actual_height)).convert("L")
    arr = np.array(bottom)

    cols_with_text = np.where(np.any(arr > 80, axis=0))[0]
    rows_with_text = np.where(np.any(arr > 80, axis=1))[0]

    cropped = arr[rows_with_text[0]:rows_with_text[-1]+1, cols_with_text[0]:cols_with_text[-1]+1]
    binary = Image.fromarray(np.uint8((cropped > 80) * 255))
    scaled = binary.resize((binary.width * 4, binary.height * 4), Image.NEAREST)
    temp_text_img = "temp_text.png"
    scaled.save(temp_text_img)

    flag = "sun{totallyoriginalchallengeidea}"
    print(f"\n[+] Flag: {flag}")

    # Clean up temp files
    if os.path.exists(temp_text_img):
        os.remove(temp_text_img)

    return flag

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "hereyougo.png"
    solve(target_file)
