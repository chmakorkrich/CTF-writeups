# Writeup: robocall

## Challenge Overview
- **Category:** Binary Exploitation / Reverse Engineering
- **File:** `robocall` (64-bit ELF, PIE enabled, NX enabled, No Canary)

---

## Vulnerability & Mechanism

1. **Stack-Based Secret Layout (`place_flag`)**:
   - The binary reads `flag.txt` into a buffer and writes 4-byte chunks into memory offsets determined by the global table `CHUNK_DEPTH`:
     $$\text{Addr}(i) = RBP_{\text{main}} - 0x764 - CHUNK\_DEPTH[i]$$
   - When `place_flag` returns, the stack frame is unwound, but the flag values remain in uninitialized stack memory.

2. **Delay Bypass (`be_annoying`)**:
   - The initial prompt in `main` asks for an integer input. Supplying `42` clears the global flag `be_annoying = 0`, bypassing all `nanosleep` delays throughout the execution.

3. **Uninitialized Variable Information Disclosure (`cancel_plan`)**:
   - In `cancel_plan`, the program prompts the user for input and calls `raw_parse_int(&val)` to write to `[rbp - 0x204]`.
   - If the input is non-numeric (e.g. `'a'`), `raw_parse_int` fails silently without modifying `[rbp - 0x204]`.
   - The program subsequently prints `You've entered "<val>", are you sure?` via `raw_print_int`, leaking whatever 4-byte integer is at `RBP_{\text{cancel\_plan}} - 0x204`.

4. **Deterministic Stack Frame Alignment**:
   - Each menu function in the binary allocates a deterministic stack frame size ($S + 0x10$).
   - By navigating specific menu paths before calling `cancel_plan`, we can control the call depth $D$ such that:
     $$D = 0x560 + CHUNK\_DEPTH[i]$$
     $$RBP_{\text{cancel\_plan}} - 0x204 = RBP_{\text{main}} - 0x764 - CHUNK\_DEPTH[i]$$
   - This aligns the uninitialized variable with each of the 13 flag chunks.

---

## Navigation Table

| Chunk | Depth Offset | Path from `start_position` |
|---|---|---|
| **0** | `0x400` | `1` $\to$ `2` $\to$ `outage_addr` |
| **1** | `0x480` | `3` (scream) $\times 4$ |
| **2** | `0x520` | `3` $\to$ `1` $\to$ `2` $\to$ `outage_addr` |
| **3** | `0x570` | `1` $\to$ `4` $\to$ `1` $\to$ `outage_addr` |
| **4** | `0x5a0` | `3` (scream) $\times 5$ |
| **5** | `0x640` | `3` $\times 2$ $\to$ `1` $\to$ `2` $\to$ `outage_addr` |
| **6** | `0x690` | `3` $\to$ `1` $\to$ `4` $\to$ `1` $\to$ `outage_addr` |
| **7** | `0x6c0` | `3` (scream) $\times 6$ |
| **8** | `0x760` | `3` $\times 3$ $\to$ `1` $\to$ `2` $\to$ `outage_addr` |
| **9** | `0x7b0` | `3` $\times 2$ $\to$ `1` $\to$ `4` $\to$ `1` $\to$ `outage_addr` |
| **10** | `0x7e0` | `3` (scream) $\times 7$ |
| **11** | `0x800` | `3` $\times 2$ $\to$ `1` $\to$ `3` $\to$ `p, a, pet, 9` $\to$ `p, a, pet, 1, c1, c2, c3, c4` |
| **12** | `0x880` | `1` $\to$ `2` $\to$ `outage_addr` $\to$ `3` $\times 4$ |

*After reaching the target depth, navigating to `cancel_plan` via `1` $\to$ `6` $\to$ `2` and sending `a` triggers the leak.*

---

## Solution Script

The exploit script is provided in [`solver.py`](solver.py).

```bash
python3 solver.py [host:port]
```
