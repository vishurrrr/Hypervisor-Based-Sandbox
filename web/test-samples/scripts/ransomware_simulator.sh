#!/bin/bash
# Fake Ransomware - Simulates encryption behavior (NO FILES ENCRYPTED)
echo "[*] Ransomware: Scanning for files..."
sleep 1
echo "[*] Simulating file encryption process..."
for i in {1..20}; do
    echo "[*] Encrypting file_$i (simulated)"
    sleep 0.2
done
echo "[*] Creating ransom note..."
cat > /tmp/RANSOM_NOTE_$$.txt << 'RANSOM'
Your files have been encrypted!
Send 5 BTC to recover them.
RANSOM
cat /tmp/RANSOM_NOTE_$$.txt
rm -f /tmp/RANSOM_NOTE_$$.txt
echo "[+] Ransomware simulation completed"
