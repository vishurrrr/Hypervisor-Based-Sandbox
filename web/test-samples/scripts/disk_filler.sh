#!/bin/bash
# Disk Filler - Limited disk write test
echo "Starting disk filler test..."
dd if=/dev/zero bs=1M count=100 of=/tmp/disk_test.bin 2>/dev/null
echo "Disk filler test completed"
du -h /tmp/disk_test.bin
rm -f /tmp/disk_test.bin
