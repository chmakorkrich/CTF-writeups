# Writeup: gem_collection.pptm

## Challenge Overview
- **Category:** Forensics / Reverse Engineering / Malicious Document Analysis
- **File:** `gem_collection.pptm`

## Analysis & Walkthrough

1. **Inspecting File Format:**
   The challenge provides a `.pptm` file, which is a Microsoft PowerPoint Macro-Enabled Presentation. Underneath, OpenXML presentations are ZIP archives containing document structures, media, and an embedded OLE binary at `ppt/vbaProject.bin` containing VBA macros.

2. **Extracting VBA Macros:**
   Using `olevba` (from `oletools`) or parsing `ppt/vbaProject.bin`, we inspect the macro module `MediaCache.bas`:

   ```vba
   Option Explicit

   Public Sub RefreshCache()
       Dim encoded As String
       Dim commandLine As String
       encoded = "JABjAGEAbQBwAGEAaQBnAG4AIAA9ACAAJwBzAHUAbgB7AHkAdQBwAF8AaQBzAHMAYQBfAGcAZQBtAH0AJwANAAoAJABzAG8AdQByAGMAZQAgAD0AIAAnAGgAdAB0AHAAcwA6AC8ALwBnAGUAbQAtAGMAYQBjAGgAZQAuAGUAeABhAG0AcABsAGUALgBpAG4AdgBhAGwAaQBkAC8AYwBvAGEAbAAuAGIAaQBuACcADQAKACQAZABlAHMAdABpAG4AYQB0AGkAbwBuACAAPQAgACcAYwBvAGEAbAAuAGIAaQBuACcADQAKAFsAcABzAGMAdQBzAHQAbwBtAG8AYgBqAGUAYwB0AF0AQAB7AE8AcABlAHIAYQB0AGkAbwBuAD0AJwBkAG8AdwBuAGwAbwBhAGQAJwA7ACAAQwBhAG0AcABhAGkAZwBuAD0AJABjAGEAbQBwAGEAaQBnAG4AOwAgAFMAbwB1AHIAYwBlAD0AJABzAG8AdQByAGMAZQA7ACAARABlAHMAdABpAG4AYQB0AGkAbwBuAD0AJABkAGUAcwB0AGkAbgBhAHQAaQBvAG4AfQANAAoA"
       commandLine = "powershell.exe -NoProfile -EncodedCommand " & encoded
       Debug.Print commandLine
   End Sub
   ```

3. **Decoding PowerShell `-EncodedCommand`:**
   PowerShell's `-EncodedCommand` takes a Base64-encoded UTF-16LE string. Decoding the base64 payload:

   ```powershell
   $campaign = 'sun{yup_issa_gem}'
   $source = 'https://gem-cache.example.invalid/coal.bin'
   $destination = 'coal.bin'
   [pscustomobject]@{Operation='download'; Campaign=$campaign; Source=$source; Destination=$destination}
   ```

4. **Flag Extraction:**
   The `$campaign` variable directly reveals the flag: `sun{yup_issa_gem}`.

---

## Solution Script

The automated solution script is located at [`solver.py`](solver.py).

Run the solver:
```bash
python3 solver.py
```

### Flag
```text
sun{yup_issa_gem}
```
