# Writeup: welcomecall.pcap

## Challenge Overview
- **Category:** Network Forensics / Audio Analysis
- **File:** `welcomecall.pcap`

---

## Analysis & Walkthrough

1. **Protocol Analysis**:
   Opening `welcomecall.pcap` in Wireshark or with `tshark` shows a VoIP call session:
   - SIP negotiation (`INVITE`, `100 Trying`, `180 Ringing`, `200 OK`, `ACK`, `BYE`).
   - RTP audio stream using Payload Type 0 (**ITU-T G.711 PCMU** / $\mu$-law) at 8000 Hz sample rate.

2. **Extracting RTP Audio**:
   - Filter UDP packets containing RTP payload (`PT=0`).
   - Order the packets by RTP sequence number.
   - Decompress the 8-bit $\mu$-law samples to 16-bit linear PCM at 8 kHz mono.

3. **Audio Reversal**:
   - Listening to the extracted audio reveals a reversed voice message.
   - Reversing the PCM sample array (`samples[::-1]`) produces clear English speech.

4. **Speech Transcript**:
   > *"Welcome to BSides Orlando, the flag that you are looking for is sun with a left curly bracket, thankyouforplaying, right curly bracket. All lowercase, no spaces. Thank you and have a good one."*

---

## Solution Script

The automated extraction, PCM conversion, and audio reversal script is located at [`solver.py`](solver.py).

Run the solver:
```bash
python3 solver.py
```

### Flag
```text
sun{thankyouforplaying}
```
