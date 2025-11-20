#!/bin/bash
# Process Spawner - Creates child processes
echo "Starting process spawner test..."
for i in {1..20}; do
    (sleep 5) &
done
wait
echo "Process spawner test completed"
