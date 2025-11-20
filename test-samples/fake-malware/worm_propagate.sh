#!/bin/bash
# Fake Worm - Simulates self-propagation (NO NETWORK SPREAD)
echo "[*] Worm: Initiating self-propagation..."
sleep 1
echo "[*] Scanning for network shares..."
ls -la /mnt 2>/dev/null | head -3
echo "[*] Attempting to spread to connected systems..."
ping -c 1 192.168.1.1 2>/dev/null || true
echo "[*] Creating child processes..."
for i in {1..5}; do
    (sleep 2) &
done
wait
echo "[+] Worm simulation completed"
