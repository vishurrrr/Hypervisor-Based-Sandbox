#!/bin/bash
# Fake Spyware - Simulates keylogger behavior (NO ACTUAL LOGGING)
echo "[*] Spyware: Installing keylogger hook..."
sleep 1
echo "[*] Intercepting keyboard events..."
sleep 2
echo "[*] Captured data:"
echo "user:password123"
echo "credit_card:1234-5678-9012-3456"
echo "[*] Encrypting stolen data..."
sleep 1
echo "[*] Sending to attacker: fake-attacker.com"
echo "POST /exfil HTTP/1.1" 
sleep 2
echo "[+] Spyware simulation completed"
