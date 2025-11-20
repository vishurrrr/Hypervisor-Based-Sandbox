#!/bin/bash
# Memory Leak Simulator - Allocates increasing memory
echo "Starting memory leak simulation..."
for i in {1..10}; do
    dd if=/dev/zero bs=1M count=50 2>/dev/null | head -c 1M > /tmp/leak_$i &
done
sleep 8
rm -f /tmp/leak_* 2>/dev/null
echo "Memory leak test completed"
