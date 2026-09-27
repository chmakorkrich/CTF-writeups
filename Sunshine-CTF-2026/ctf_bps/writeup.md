# Writeup: ctf.bps

## Challenge Overview
- **Category:** Reverse Engineering / Game ROM Forensics
- **File:** `ctf.bps` (beat / BPS patch file)

---

## Analysis & Walkthrough

1. **Understanding the BPS Format**:
   BPS (*Binary Patch System*) is a delta patching format standard in retro gaming (commonly SNES / Super Mario World ROM hacking).
   Parsing `ctf.bps` header reveals:
   - **Source ROM Size:** 524,288 bytes (512 KB)
   - **Target ROM Size:** 1,048,576 bytes (1 MB)
   - **Source CRC32:** `0xb19ed489` (Super Mario World NTSC/USA headerless ROM)
   - **Target CRC32:** `0xa53bdd22`

2. **Analyzing Patch Instructions**:
   Parsing the actions in `ctf.bps` extracts a 71-byte `TargetRead` chunk injected into the ROM at `0xC609`:
   ```hex
   5a 48 a2 00 bd 22 80 f0 09 49 5a 9f 00 c1 7e e8 80 f2 68 7a fa ab 6b 29 2f 34 21 1c 6b 3b 17 69 05 35 14 05 17 6e 28 6b 6a 27 00 ...
   ```

3. **Disassembling 65c816 SNES Assembly**:
   ```assembly
   5A          PHY
   48          PHA
   A2 00       LDX #$00
   BD 22 80    LDA $8022,X    ; Load byte from table
   F0 09       BEQ $801D      ; If 0x00, exit loop
   49 5A       EOR #$5A       ; XOR with 0x5A
   9F 00 C1 7E STA $7EC100,X  ; Store decrypted character into WRAM
   E8          INX
   80 F2       BRA $8004      ; Loop
   68          PLA
   7A          PLY
   FA          PLX
   AB          PLB
   6B          RTL
   ```

4. **Decrypting the Flag Payload**:
   The loop performs a byte-by-byte XOR decryption with key `0x5A` starting at offset `0x17` in the payload:
   ```python
   encrypted = bytes.fromhex('292f34211c6b3b176905351405176e286b6a27')
   flag = bytes([b ^ 0x5A for b in encrypted]).decode()
   # 'sun{F1aM3_oN_M4r10}'
   ```

---

## Solution Script

The automated BPS parser and decryptor script is located at [`solver.py`](solver.py).

Run the solver:
```bash
python3 solver.py
```

### Flag
```text
sun{F1aM3_oN_M4r10}
```
