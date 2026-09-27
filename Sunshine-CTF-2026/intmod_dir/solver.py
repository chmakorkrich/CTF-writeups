#!/usr/bin/env python3
"""
SunshineCTF - intmod Solver
Challenge: intmod (ELF 64-bit x86-64)
Category: Reverse Engineering / Cryptanalysis

Summary:
The binary is a signal-driven VM that validates a 33-byte input flag.
The input is PKCS#7 padded to 40 bytes and packed into 5 64-bit integers.
45 mixing operations (combining arithmetic, rotations, swaps, and signal-driven
register updates) mix the state into a 40-byte buffer B.
The VM then evaluates 40 modular polynomials over GF(65521) via Horner's method:
    P(x_i) = sum_{k=0}^{39} B[k] * x_i^k mod 65521
and checks that P(x_i) == Y_i (mod 65521) for 40 distinct evaluation points.
Solving the 40x40 Vandermonde system over GF(65521) yields the required state buffer,
and inverting the 45 mixing steps recovers the exact flag.
"""

MOD = 65521
MASK64 = 0xffffffffffffffff

def rol64(v, s):
    s %= 64
    return ((v << s) | (v >> (64 - s))) & MASK64

def ror64(v, s):
    s %= 64
    return ((v >> s) | (v << (64 - s))) & MASK64

def modInverse(a, m=MOD):
    return pow(a, m - 2, m)

def solve_vandermonde(eqs):
    """
    Solves sum_{k=0}^{39} B[k] * x^k = Y (mod 65521)
    eqs: list of (x_i, Y_i) tuples
    """
    n = len(eqs)
    M = []
    for x, Y in eqs:
        row = []
        xk = 1
        for k in range(n):
            row.append(xk)
            xk = (xk * x) % MOD
        row.append(Y % MOD)
        M.append(row)
        
    for i in range(n):
        pivot = i
        while pivot < n and M[pivot][i] == 0:
            pivot += 1
        if pivot == n:
            raise ValueError(f"Singular matrix at column {i}")
        M[i], M[pivot] = M[pivot], M[i]
        inv = modInverse(M[i][i])
        for j in range(i, n + 1):
            M[i][j] = (M[i][j] * inv) % MOD
        for r in range(n):
            if r != i and M[r][i] != 0:
                factor = M[r][i]
                for j in range(i, n + 1):
                    M[r][j] = (M[r][j] - factor * M[i][j]) % MOD
    return [M[i][n] for i in range(n)]

# Extracted from VM bytecode (40 (x, Y) constraints)
# Each pair is (x_i, (y_i + imm_6_i) mod 65521)
EQUATIONS = [
    (0x2729, (0xd6b6 + 0x8363) % MOD),
    (0x5968, (0x1ef1 + 0xd01a) % MOD),
    (0x5afe, (0x49b5 + 0xeb39) % MOD),
    (0xb0d9, (0x8acc + 0xb57b) % MOD),
    (0xf735, (0x8df2 + 0x1b2a) % MOD),
    (0x8744, (0x2bc8 + 0xd535) % MOD),
    (0x0794, (0xbcaf + 0x8fdc) % MOD),
    (0xc287, (0xedc7 + 0x6e84) % MOD),
    (0x929e, (0xe1bf + 0x2e22) % MOD),
    (0xd364, (0xb308 + 0xf4ea) % MOD),
    (0xe358, (0x911a + 0x11f4) % MOD),
    (0x6b76, (0xe729 + 0xc9ae) % MOD),
    (0x49a5, (0x8b4f + 0x3da9) % MOD),
    (0x0b2e, (0x5c1e + 0xe50b) % MOD),
    (0x319c, (0x23e1 + 0x0fb8) % MOD),
    (0xfcfa, (0x85f2 + 0x3cef) % MOD),
    (0xb0d6, (0xc1ea + 0x0654) % MOD),
    (0xcf5e, (0xd017 + 0x581a) % MOD),
    (0xbe05, (0x6c2c + 0xc149) % MOD),
    (0x1e0b, (0xf287 + 0x5651) % MOD),
    (0x3fa2, (0x0889 + 0x28b9) % MOD),
    (0x1cfc, (0xb5a6 + 0xcd84) % MOD),
    (0x57f7, (0x2c95 + 0xc3a6) % MOD),
    (0x6af7, (0xe5b2 + 0xbac7) % MOD),
    (0xd182, (0xea44 + 0xad9c) % MOD),
    (0x5d86, (0x43a0 + 0xb63e) % MOD),
    (0x4066, (0xca90 + 0x4247) % MOD),
    (0xc57e, (0x597b + 0xea29) % MOD),
    (0xca12, (0x2961 + 0x500f) % MOD),
    (0x4fdf, (0x0d14 + 0xec51) % MOD),
    (0x0b17, (0x3769 + 0x418c) % MOD),
    (0xbf61, (0x8326 + 0xcc21) % MOD),
    (0x194f, (0x191d + 0xe988) % MOD),
    (0xe354, (0x64ad + 0x398a) % MOD),
    (0x3f51, (0xeb97 + 0xb229) % MOD),
    (0xf0d5, (0x3543 + 0xd73d) % MOD),
    (0x754d, (0x7cd3 + 0x4a91) % MOD),
    (0x3945, (0xaac2 + 0xf1dd) % MOD),
    (0x3846, (0xff88 + 0x9f7a) % MOD),
    (0x978f, (0xe1ba + 0x222d) % MOD)
]

def invert_vm(r_final):
    """
    Inverts all 45 VM mixing steps backwards to recover the initial 5 64-bit registers.
    """
    r = list(r_final)
    
    # Step 44 inv
    r[3], r[4] = r[4], r[3]
    r[0] = ror64(r[0], 15)
    
    # Step 43 inv
    r[3] = (r[3] * pow(13537915256980136287, -1, 2**64)) & MASK64
    r[1] ^= r[2]
    
    # Step 42 inv
    r[2] = (r[2] - rol64(r[4], 45)) & MASK64
    r[0], r[1] = r[1], r[0]
    
    # Step 41 inv
    r[2] = ror64(r[2], 35)
    r[1] = (r[1] * pow(0xdb4f0b9175ae2165, -1, 2**64)) & MASK64
    
    # Step 40 inv
    r[3] ^= r[4]
    r[4] = (r[4] - rol64(r[0], 9)) & MASK64
    
    # Step 39 inv
    r[3], r[4] = r[4], r[3]
    r[1] = ror64(r[1], 49)
    
    # Step 38 inv
    r[4] = (r[4] * pow(14320364442791297827, -1, 2**64)) & MASK64
    r[2] ^= r[0]
    
    # Step 37 inv
    r[0] = (r[0] - rol64(r[3], 27)) & MASK64
    r[2], r[1] = r[1], r[2]
    
    # Step 36 inv
    r[4] = ror64(r[4], 21)
    r[1] = (r[1] * pow(0x9ddfea08eb382d69, -1, 2**64)) & MASK64
    
    # Step 35 inv
    r[0] ^= r[3]
    r[3] = (r[3] - rol64(r[2], 53)) & MASK64
    
    # Step 34 inv
    r[0], r[4] = r[4], r[0]
    r[3] = ror64(r[3], 29)
    
    # Step 33 inv
    r[4] = (r[4] * pow(16952864883938283877, -1, 2**64)) & MASK64
    r[2] ^= r[1]
    
    # Step 32 inv
    r[1] = (r[1] - rol64(r[0], 3)) & MASK64
    r[3], r[0] = r[0], r[3]
    
    # Step 31 inv
    r[2] = ror64(r[2], 13)
    r[0] = (r[0] * pow(0x1d8e4e27c47d124f, -1, 2**64)) & MASK64
    
    # Step 30 inv
    r[1] ^= r[4]
    r[4] = (r[4] - rol64(r[3], 47)) & MASK64
    
    # Step 29 inv
    r[1], r[3] = r[3], r[1]
    r[0] = ror64(r[0], 43)
    
    # Step 28 inv
    r[3] = (r[3] * pow(6384245875588680899, -1, 2**64)) & MASK64
    r[4] ^= r[2]
    
    # Step 27 inv
    r[2] = (r[2] - rol64(r[1], 19)) & MASK64
    r[4], r[2] = r[2], r[4]
    
    # Step 26 inv
    r[1] = ror64(r[1], 17)
    r[2] = (r[2] * pow(0x8ebc6af09c88c6e3, -1, 2**64)) & MASK64
    
    # Step 25 inv
    r[3] ^= r[0]
    r[0] = (r[0] - rol64(r[4], 37)) & MASK64
    
    # Step 24 inv
    r[1], r[4] = r[4], r[1]
    r[0] = ror64(r[0], 39)
    
    # Step 23 inv
    r[1] = (r[1] * pow(16646288086500911323, -1, 2**64)) & MASK64
    r[2] ^= r[3]
    
    # Step 22 inv
    r[3] = (r[3] - rol64(r[4], 11)) & MASK64
    r[3], r[4] = r[4], r[3]
    
    # Step 21 inv
    r[2] = ror64(r[2], 7)
    r[4] = (r[4] * pow(0xa0761d6478bd642f, -1, 2**64)) & MASK64
    
    # Step 20 inv
    r[0] ^= r[1]
    r[1] = (r[1] - rol64(r[3], 31)) & MASK64
    
    # Step 19 inv
    r[0], r[4] = r[4], r[0]
    r[3] = ror64(r[3], 53)
    
    # Step 18 inv
    r[4] = (r[4] * pow(15485907386658061715, -1, 2**64)) & MASK64
    r[1] ^= r[2]
    
    # Step 17 inv
    r[2] = (r[2] - rol64(r[0], 23)) & MASK64
    r[1], r[0] = r[0], r[1]
    
    # Step 16 inv
    r[2] = ror64(r[2], 9)
    r[0] = (r[0] * pow(0xbf58476d1ce4e5b9, -1, 2**64)) & MASK64
    
    # Step 15 inv
    r[3] ^= r[4]
    r[4] = (r[4] - rol64(r[1], 41)) & MASK64
    
    # Step 14 inv
    r[1], r[2] = r[2], r[1]
    r[3] = ror64(r[3], 47)
    
    # Step 13 inv
    r[1] = (r[1] * pow(10723151780598845931, -1, 2**64)) & MASK64
    r[4] ^= r[0]
    
    # Step 12 inv
    r[0] = (r[0] - rol64(r[2], 5)) & MASK64
    r[3], r[0] = r[0], r[3]
    
    # Step 11 inv
    r[4] = ror64(r[4], 37)
    r[0] = (r[0] * pow(0x27d4eb2f165667c5, -1, 2**64)) & MASK64
    
    # Step 10 inv
    r[1] ^= r[2]
    r[2] = (r[2] - rol64(r[3], 17)) & MASK64
    
    # Step 09 inv
    r[2], r[3] = r[3], r[2]
    r[1] = ror64(r[1], 23)
    
    # Step 08 inv
    r[3] = (r[3] * pow(9650029242287828579, -1, 2**64)) & MASK64
    r[0] ^= r[4]
    
    # Step 07 inv
    r[4] = (r[4] - rol64(r[2], 43)) & MASK64
    r[4], r[2] = r[2], r[4]
    
    # Step 06 inv
    r[0] = ror64(r[0], 11)
    r[2] = (r[2] * pow(0x165667b19e3779f9, -1, 2**64)) & MASK64
    
    # Step 05 inv
    r[3] ^= r[1]
    r[1] = (r[1] - rol64(r[4], 29)) & MASK64
    
    # Step 04 inv
    r[0], r[1] = r[1], r[0]
    r[2] = ror64(r[2], 31)
    
    # Step 03 inv
    r[1] = (r[1] * pow(14029467366897019727, -1, 2**64)) & MASK64
    r[4] ^= r[3]
    
    # Step 02 inv
    r[3] = (r[3] - rol64(r[0], 13)) & MASK64
    r[1], r[3] = r[3], r[1]
    
    # Step 01 inv
    r[3] = (r[3] * pow(0x9e3779b185ebca87, -1, 2**64)) & MASK64
    r[4] = 0x070707070707077d  # input[32] = '}' = 0x7d + 7 bytes of PKCS#7 0x07
    
    # Step 00 inv
    r[2] ^= r[0]
    r[0] = (r[0] - rol64(r[1], 7)) & MASK64
    
    return r

def main():
    # 1. Solve the 40 polynomial equations over GF(65521)
    B = solve_vandermonde(EQUATIONS)
    print(f"[+] Solved {len(B)} polynomial coefficients mod {MOD}")
    
    # 2. Pack the 40 bytes into 5 64-bit integers (little-endian)
    r_target = [0] * 5
    for i in range(5):
        val = 0
        for j in range(8):
            val |= (B[i*8 + j] << (j * 8))
        r_target[i] = val
    print(f"[+] Target state at Step 45: {[hex(x) for x in r_target]}")
    
    # 3. Invert the 45 mixing operations
    r_init = invert_vm(r_target)
    
    # 4. Unpack into 40 bytes
    raw_bytes = bytearray()
    for v in r_init:
        raw_bytes.extend(v.to_bytes(8, "little"))
        
    flag = raw_bytes[:33].decode("latin1")
    padding = list(raw_bytes[33:])
    
    print(f"[+] Extracted Flag: {flag}")
    print(f"[+] PKCS#7 Padding check: {padding} (expected [7, 7, 7, 7, 7, 7, 7])")
    assert padding == [7, 7, 7, 7, 7, 7, 7]
    assert flag.startswith("sun{") and flag.endswith("}")
    print("[+] Verification complete!")

if __name__ == "__main__":
    main()
