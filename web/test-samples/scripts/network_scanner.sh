#!/bin/bash
# Network Scanner Simulator
echo "Starting network scanner simulation..."
echo "Scanning 192.168.1.0/24..."
for i in {1..10}; do
    echo "Attempting connection to 192.168.1.$i:22..."
done
echo "Network scanner test completed"
