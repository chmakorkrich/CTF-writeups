# Writeup: boardwriter.klc

## Challenge Overview
- **Category:** Miscellaneous / Crypto / Steganography
- **File:** `boardwriter.klc`

---

## Analysis & Walkthrough

1. **Inspecting File Structure**:
   `boardwriter.klc` is a UTF-16 encoded Microsoft Keyboard Layout Creator configuration file.
   In the main `LAYOUT` table, the backtick key `OEM_3` (scan code `29`) is assigned as a dead key:
   ```text
   29  OEM_3   0   0060@   007e   -1
   ```
   Pressing this key activates dead key state `0060`.

2. **Chained Dead Keys**:
   In Windows keyboard layouts, dead keys can chain to other dead keys (indicated by the `@` suffix). 
   Tracing the dead key definitions in the file:

   | Dead Key | Input Char | Next Dead Key / Output |
   |---|---|---|
   | `0060` (Initial `` ` ``) | `'s'` (`0073`) | `02d0@` |
   | `02d0` | `'u'` (`0075`) | `02ed@` |
   | `02ed` | `'n'` (`006e`) | `02b4@` |
   | `02b4` | `'{'` (`007b`) | `02ef@` |
   | `02ef` | `'p'` (`0070`) | `02ba@` |
   | `02ba` | `'r'` (`0072`) | `02c9@` |
   | `02c9` | `'a'` (`0061`) | `02d3@` |
   | `02d3` | `'i'` (`0069`) | `02e9@` |
   | `02e9` | `'s'` (`0073`) | `02bd@` |
   | `02bd` | `'e'` (`0065`) | `02cd@` |
   | `02cd` | `'t'` (`0074`) | `02e4@` |
   | `02e4` | `'h'` (`0068`) | `02d8@` |
   | `02d8` | `'e'` (`0065`) | `02ee@` |
   | `02ee` | `'s'` (`0073`) | `02d4@` |
   | `02d4` | `'u'` (`0075`) | `02e1@` |
   | `02e1` | `'n'` (`006e`) | `02b0@` |
   | `02b0` | `'}'` (`007d`) | `2600` (☀ Sun symbol) |

3. **Reconstructing the Flag**:
   Following the chained input characters from start to the terminal `2600` symbol produces:
   ```text
   sun{praisethesun}
   ```

---

## Solution Script

The automated parser and deadkey tracer is located at [`solver.py`](solver.py).

Run the solver:
```bash
python3 solver.py
```

### Flag
```text
sun{praisethesun}
```
