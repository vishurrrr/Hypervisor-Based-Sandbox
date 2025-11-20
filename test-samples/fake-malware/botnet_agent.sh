#!/bin/bash
# Fake Botnet - Simulates bot agent behavior (NO ACTUAL C&C)
echo "[*] Botnet Agent: Starting command receiver..."
sleep 1
echo "[*] Connecting to C&C server..."
echo "REGISTER bot_$RANDOM" 
sleep 2
echo "[*] Listening for commands..."
echo "[*] Simulated command: DDoS attack (not executed)"
echo "[*] Simulated command: Credential theft (not executed)"
echo "[*] Simulated command: Spam campaign (not executed)"
sleep 3
echo "[+] Botnet simulation completed"
