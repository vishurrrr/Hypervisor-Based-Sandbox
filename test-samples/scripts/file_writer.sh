#!/bin/bash
# File Writer - Creates multiple files
echo "Starting file writer test..."
mkdir -p /tmp/sandbox_files
for i in {1..100}; do
    echo "Test data $i" > /tmp/sandbox_files/file_$i.txt
done
echo "File writer test completed"
ls /tmp/sandbox_files | wc -l
