# Writeup: suntrail.klc

## Challenge Overview
- **Category:** Miscellaneous / Crypto / Steganography
- **File:** `suntrail.klc`

---

## Analysis & Walkthrough

1. **File Format (.klc)**:
   The `.klc` file is a Microsoft Keyboard Layout Creator specification. Under the `LAYOUT` section, keys are defined with their scan codes, virtual key names, and output Unicode characters for various shift states:

   ```text
   // SC   VK_   Cap   State0   State1   State2
   10      Q     0     2198     0073     -1
   11      W     0     2192     0077     -1
   12      E     0     2198     0065     -1
   13      R     0     2192     0073     -1
   14      T     0     2198     0075     -1
   1e      A     0     2198     0075     -1
   1f      S     0     2196     0071     -1
   20      D     0     2198     0072     -1
   21      F     0     2196     005f     -1
   22      G     0     2198     0063     -1
   23      H     0     25a0     007d     -1
   2c      Z     0     2192     006e     -1
   2d      X     0     2196     007b     -1
   2e      C     0     2192     0074     -1
   2f      V     0     2196     0079     -1
   30      B     0     2192     006b     -1
   31      N     0     2196     0073     -1
   ```

2. **Decoding Unicode Symbols**:
   - **State 0 (Unshifted characters)** contains directional arrows and a stop marker:
     - `U+2198`: $\searrow$ (South-East / Down-Right)
     - `U+2192`: $\rightarrow$ (Right)
     - `U+2196`: $\nwarrow$ (North-West / Up-Left)
     - `U+25A0`: $\blacksquare$ (Black Square / Stop)
   - **State 1 (Shifted characters)** contains printable ASCII letters and punctuation.

3. **Following the Physical Keyboard Trail**:
   On a standard staggered QWERTY keyboard:
   - Row 1: `Q W E R T`
   - Row 2: `A S D F G H` (staggered slightly right)
   - Row 3: `Z X C V B N` (staggered slightly right)

   Following the arrows starting from `Q`:
   - `Q` ($\searrow$) $\to$ `A`
   - `A` ($\searrow$) $\to$ `Z`
   - `Z` ($\rightarrow$) $\to$ `X`
   - `X` ($\nwarrow$) $\to$ `S`
   - `S` ($\nwarrow$) $\to$ `W`
   - `W` ($\rightarrow$) $\to$ `E`
   - `E` ($\searrow$) $\to$ `D`
   - `D` ($\searrow$) $\to$ `C`
   - `C` ($\rightarrow$) $\to$ `V`
   - `V` ($\nwarrow$) $\to$ `F`
   - `F` ($\nwarrow$) $\to$ `R`
   - `R` ($\rightarrow$) $\to$ `T`
   - `T` ($\searrow$) $\to$ `G`
   - `G` ($\searrow$) $\to$ `B`
   - `B` ($\rightarrow$) $\to$ `N`
   - `N` ($\nwarrow$) $\to$ `H`
   - `H` ($\blacksquare$) $\to$ **STOP**

4. **Reconstructing the Flag**:
   Concatenating the shifted character (State 1) from each key in the trail:

   | Key | Shift Char | Arrow | Direction | Next Key |
   |:---:|:---:|:---:|:---:|:---:|
   | **Q** | `s` | `\u2198` | $\searrow$ (Down-Right) | `A` |
   | **A** | `u` | `\u2198` | $\searrow$ (Down-Right) | `Z` |
   | **Z** | `n` | `\u2192` | $\rightarrow$ (Right) | `X` |
   | **X** | `{` | `\u2196` | $\nwarrow$ (Up-Left) | `S` |
   | **S** | `q` | `\u2196` | $\nwarrow$ (Up-Left) | `W` |
   | **W** | `w` | `\u2192` | $\rightarrow$ (Right) | `E` |
   | **E** | `e` | `\u2198` | $\searrow$ (Down-Right) | `D` |
   | **D** | `r` | `\u2198` | $\searrow$ (Down-Right) | `C` |
   | **C** | `t` | `\u2192` | $\rightarrow$ (Right) | `V` |
   | **V** | `y` | `\u2196` | $\nwarrow$ (Up-Left) | `F` |
   | **F** | `_` | `\u2196` | $\nwarrow$ (Up-Left) | `R` |
   | **R** | `s` | `\u2192` | $\rightarrow$ (Right) | `T` |
   | **T** | `u` | `\u2198` | $\searrow$ (Down-Right) | `G` |
   | **G** | `c` | `\u2198` | $\searrow$ (Down-Right) | `B` |
   | **B** | `k` | `\u2192` | $\rightarrow$ (Right) | `N` |
   | **N** | `s` | `\u2196` | $\nwarrow$ (Up-Left) | `H` |
   | **H** | `}` | `\u25a0` | $\blacksquare$ (STOP) | *End* |

---

## Solution Script

The automated parser and solver script is located at [`solver.py`](solver.py).

Run the solver:
```bash
python3 solver.py
```

### Flag
```text
sun{qwerty_sucks}
```
