# CTF Writeups

Writeups, solve scripts and challenge artifacts from CTF competitions.

## Layout

```
CTF-writeups/
└── <Competition>/
    └── <challenge>/
        ├── writeup.md      # analysis + flag
        ├── solver.py       # reproducible solve script
        └── artifacts/      # challenge files, captures, generated output
```

## Competitions

### Sunshine-CTF-2026

| Challenge | Category | Flag |
|-----------|----------|------|
| [boardwriter](Sunshine-CTF-2026/boardwriter) | Misc / Crypto / Stego | `sun{praisethesun}` |
| [ctf_bps](Sunshine-CTF-2026/ctf_bps) | Reverse Engineering / ROM Forensics | `sun{F1aM3_oN_M4r10}` |
| [gem_collection](Sunshine-CTF-2026/gem_collection) | Forensics / Malicious Document | `sun{yup_issa_gem}` |
| [groundhog](Sunshine-CTF-2026/groundhog) | Web (469) | `sun{s1x_m0r3_w33ks_0f_g0ph3r_ssrf}` |
| [hereyougo](Sunshine-CTF-2026/hereyougo) | Forensics / Steganography | `sun{totally_original_challenge_idea}` |
| [intmod_dir](Sunshine-CTF-2026/intmod_dir) | Reverse Engineering / Cryptanalysis | `sun{I_L0v3_Int3rrupts&SelfMod!!!}` |
| [robocall_dir](Sunshine-CTF-2026/robocall_dir) | Binary Exploitation / Reverse Engineering | see writeup |
| [sitecheck](Sunshine-CTF-2026/sitecheck) | Web (500) | `sun{fr4gm3nt3d_r3fl3ct10ns_1n_th3_futur3}` |
| [suntrail](Sunshine-CTF-2026/suntrail) | Misc / Crypto / Stego | `sun{qwerty_sucks}` |
| [used-goods-of-tomorrow](Sunshine-CTF-2026/used-goods-of-tomorrow) | Web (500) | `sun{1_l0v3_fr33_stuff}` |
| [welcomecall](Sunshine-CTF-2026/welcomecall) | Network Forensics / Audio | `sun{thankyouforplaying}` |
| [you-are-kidding-me](Sunshine-CTF-2026/you-are-kidding-me) | Web (500) | `sun{h0tw1r3d_4dm1n_jwt}` |

> `cookiecorp` is a work-in-progress challenge with no writeup yet.

## Reproducing a solve

Each challenge is self-contained:

```bash
cd Sunshine-CTF-2026/<challenge>
python3 solver.py            # some accept artifact paths as argv
```

Dependencies vary per challenge (e.g. `pwntools`, `requests`, `angr`); see the
writeup for specifics. Artifacts are the inputs the solver expects, so run the
solver from the challenge directory.
