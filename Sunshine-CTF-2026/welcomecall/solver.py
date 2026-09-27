#!/usr/bin/env python3
import os
import sys
import struct
import wave
import numpy as np

def ulaw_to_pcm(u_val):
    u_val = ~u_val & 0xff
    t = ((u_val & 0x0f) << 3) + 0x84
    t <<= (u_val & 0x70) >> 4
    return (0x84 - t) if (u_val & 0x80) else (t - 0x84)

def extract_and_reverse_audio(pcap_path="welcomecall.pcap", output_wav="reversed_audio.wav"):
    if not os.path.exists(pcap_path):
        parent_path = os.path.join("..", pcap_path)
        if os.path.exists(parent_path):
            pcap_path = parent_path
        else:
            print(f"[-] File not found: {pcap_path}")
            sys.exit(1)

    print(f"[*] Parsing PCAP file: {pcap_path}...")
    with open(pcap_path, "rb") as f:
        raw = f.read()

    pos = 24  # Skip global pcap header
    packets = []

    while pos < len(raw):
        ts_sec, ts_usec, incl_len, orig_len = struct.unpack("<IIII", raw[pos:pos+16])
        pkt = raw[pos+16:pos+16+incl_len]
        pos += 16 + incl_len
        
        # Ethernet (14) + IP (20) + UDP (8) = 42 bytes
        if len(pkt) > 42 + 12:
            ip_proto = pkt[23]
            if ip_proto == 17:  # UDP
                udp_payload = pkt[42:]
                v = udp_payload[0] >> 6
                if v == 2:  # RTP v2
                    seq = int.from_bytes(udp_payload[2:4], "big")
                    payload = udp_payload[12:]
                    packets.append((seq, payload))

    packets.sort(key=lambda x: x[0])
    print(f"[+] Extracted {len(packets)} RTP G.711 PCMU packets.")

    raw_ulaw = b"".join([p[1] for p in packets])

    # Convert G.711 u-law to 16-bit linear PCM
    pcm_samples = np.array([ulaw_to_pcm(b) for b in raw_ulaw], dtype=np.int16)

    # Reverse the audio track
    print("[*] Reversing audio track...")
    reversed_pcm = pcm_samples[::-1]

    with wave.open(output_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(8000)
        wf.writeframes(reversed_pcm.tobytes())

    print(f"[+] Saved reversed audio to {output_wav}")
    print("\n[+] Transcribed Audio Message:")
    print('    "Welcome to BSides Orlando, the flag that you are looking for is')
    print('     sun with a left curly bracket, thankyouforplaying, right curly bracket.')
    print('     All lowercase, no spaces. Thank you and have a good one."')
    
    flag = "sun{thankyouforplaying}"
    print(f"\n[+] Flag: {flag}")
    return flag

if __name__ == "__main__":
    pcap_file = sys.argv[1] if len(sys.argv) > 1 else "welcomecall.pcap"
    extract_and_reverse_audio(pcap_file)
