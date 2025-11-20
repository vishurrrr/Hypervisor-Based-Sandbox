#!/bin/bash
# CPU Hog - Consumes CPU resources
echo "Starting CPU hog test..."
for i in {1..5}; do
    (while true; do echo ""; done) &
done
sleep 10
pkill -P $$
echo "CPU hog test completed"
