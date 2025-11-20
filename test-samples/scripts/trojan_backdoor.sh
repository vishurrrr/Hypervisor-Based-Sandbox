#!/bin/bash
# Fake Trojan - Simulates backdoor behavior (NO ACTUAL HARM)
echo "[*] Trojan: Establishing backdoor..."
sleep 2
echo "[*] Creating fake persistence mechanism..."
touch /tmp/.trojan_marker_$$ 2>/dev/null
echo "[*] Attempting fake C&C communication..."
echo "GET /command HTTP/1.1" | nc -w 1 127.0.0.1 80 2>/dev/null || true
sleep 3
rm -f /tmp/.trojan_marker_$$ 2>/dev/null
echo "[+] Trojan simulation completed"
