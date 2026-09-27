# intmod - SunshineCTF Writeup

## 1. Challenge Overview
- **Binary:** `intmod` (ELF 64-bit LSB executable, x86-64, statically linked / stripped)
- **Category:** Reverse Engineering / Cryptanalysis
- **Flag:** `sun{I_L0v3_Int3rrupts&SelfMod!!!}`

---

## 2. Reverse Engineering Findings

### 2.1 Input Formatting & Packing
1. The binary requires an exact 33-byte ASCII input from `stdin`.
2. The 33 bytes are padded using standard **PKCS#7 padding** with 7 bytes of `0x07` to reach a length of 40 bytes.
3. The 40 bytes are packed into five 64-bit little-endian integers:
   - $r_0 = \text{bytes}[0..7]$
   - $r_1 = \text{bytes}[8..15]$
   - $r_2 = \text{bytes}[16..23]$
   - $r_3 = \text{bytes}[24..31]$
   - $r_4 = \text{bytes}[32..39]$ (with `bytes[33..39] = 0x07`)

---

### 2.2 Signal-Driven Custom VM & Anti-Analysis Architecture
The binary implements a virtual machine where instruction execution and bytecode decryption are driven by Unix hardware signals (`SIGTRAP` from `int3`, `SIGFPE` from `div 0`, and `SIGILL` from `ud2`):
- Whenever an exception occurs, a custom signal handler (`0x4037a0`) intercepts the CPU exception via `ucontext_t`.
- The signal handler dynamically decrypts the next instruction using an XTEA-based decryption schedule, steps the VM execution state, and alters register contents in the saved context before returning via `ucontext.REG_RIP`.
- When run under interactive GDB or standard ptrace-based debuggers, GDB intercepts the `SIGTRAP` and breaks signal delivery to the handler. To trace the execution, dynamic instrumentation via `LD_PRELOAD` hooking the instruction dispatch handler (`0x400ae0`) or direct static analysis was used.

---

### 2.3 Instruction Set & Modular Polynomial Constraints
The VM executes a series of 45 mixing operations followed by 40 polynomial evaluation constraints:
- **Opcode 0 (`ADD`):** `r[dst] = (r[dst] + rol64(r[src], shift)) mod 2^64`
- **Opcode 1 (`XOR`):** `r[dst] = r[dst] ^ rol64(r[src], shift)`
- **Opcode 2 (`IMUL`):** `r[dst] = (r[dst] * imm) mod 2^64`
- **Opcode 3 (`ROL`):** `r[dst] = rol64(r[dst], shift)`
- **Opcode 4 (`SWAP`):** `swap(r[dst], r[src])`
- **Opcode 5 (`POLY_EVAL`):** Unpacks the 5 64-bit registers into a 40-byte buffer $B = (B_0, \dots, B_{39})$ and evaluates the polynomial modulo $65521$:
  $$P(x_i) = \sum_{k=0}^{39} B_k x_i^k \pmod{65521}$$
  and computes $\text{diff}_i = (P(x_i) - y_i) \pmod{65521}$.
- **Opcode 6 (`CHECK`):** Verifies that $\text{diff}_i \equiv \text{imm}_{6,i} \pmod{65521}$, accumulating any mismatch into `r[0x48]`:
  $$\text{accumulator} = \bigvee_{i=0}^{39} (\text{diff}_i \oplus \text{imm}_{6,i})$$

Success requires `r[0x48] == 0`, meaning all 40 polynomial equations must simultaneously satisfy:
$$P(x_i) \equiv y_i + \text{imm}_{6,i} \pmod{65521}, \quad \text{for } i = 0, \dots, 39$$

---

## 3. Solution Strategy

1. **Solve for the Required 40-Byte State ($B$):**
   The 40 polynomial evaluation points $(x_i, Y_i)$ form a $40 \times 40$ Vandermonde linear system over the prime field $\mathbb{F}_{65521}$:
   $$V \cdot B \equiv Y \pmod{65521}$$
   Using Gaussian elimination over $\mathbb{F}_{65521}$, we uniquely determine all 40 coefficients $B_0, \dots, B_{39}$ and pack them into the target 64-bit state registers $r_{\text{target}}$ at Step 45.

2. **Invert the 45 State Transformations:**
   Starting from $r_{\text{target}}$ at Step 45, we step backwards to Step 0 by applying the exact inverse of each arithmetic operation, rotation, swap, and auxiliary register transformation.

3. **Extract Flag:**
   Unpacking the initial state registers $r_{\text{init}}$ yields the 33 ASCII characters of the flag with the expected PKCS#7 padding.

---

## 4. Execution & Verification

Run the solver:
```bash
python3 solver.py
```

Output:
```text
[+] Solved 40 polynomial coefficients mod 65521
[+] Target state at Step 45: ['0x7647653d32c8af6c', '0x8b335299eb07dda8', '0x82dd9502a3be9591', '0xd66e926f06c4a36f', '0x77a194bf7b25dff2']
[+] Extracted Flag: sun{I_L0v3_Int3rrupts&SelfMod!!!}
[+] PKCS#7 Padding check: [7, 7, 7, 7, 7, 7, 7] (expected [7, 7, 7, 7, 7, 7, 7])
[+] Verification complete!
```

Testing against `./intmod`:
```bash
$ ./intmod <<< "sun{I_L0v3_Int3rrupts&SelfMod!!!}"
Correct
```
