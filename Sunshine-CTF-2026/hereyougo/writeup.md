# Writeup: hereyougo.png

## Challenge Overview
- **Category:** Forensics / Steganography
- **File:** `hereyougo.png`

---

## Analysis & Walkthrough

1. **Inspecting the Image & Warnings**:
   When opening or processing `hereyougo.png`, `libpng` raises a warning:
   ```text
   libpng warning: IDAT: Too much image data
   ```
   This is a classic indicator that the PNG's compressed `IDAT` stream contains more scanlines than specified in the `IHDR` header (height tampering / cropped height).

2. **Calculating Actual Image Dimensions**:
   - The image uses 8-bit RGBA color mode (`color_type = 6`), meaning each scanline has:
     $$\text{Bytes per row} = 1 \text{ (filter byte)} + \text{width} \times 4 = 1 + 492 \times 4 = 1969 \text{ bytes}$$
   - Extracting and decompressing all `IDAT` chunks yields `823,042` bytes.
   - Calculating actual row count:
     $$\text{Actual Height} = \frac{823,042}{1969} = 418 \text{ pixels}$$
   - The `IHDR` header was artificially set to `382` pixels, hiding 36 scanlines at the bottom of the image.

3. **Restoring the PNG Header**:
   - Update the 4-byte height field in `IHDR` at bytes 20–24 from `382` (`0x0000017E`) to `418` (`0x000001A2`).
   - Recalculate the `IHDR` CRC32 checksum over the chunk type and data.

4. **Reading the Hidden Text**:
   Opening the restored image reveals a line of text at the bottom:
   ```text
   sun{totally_original_challenge_idea}
   ```

---

## Solution Script

The automated restoration script is located at [`solver.py`](solver.py).

Run the solver:
```bash
python3 solver.py
```

### Flag
```text
sun{totally_original_challenge_idea}
```
