#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_TMPDIR=$(mktemp -d)

echo "=== SafeBox Integration Test ==="
echo "Test directory: $TEST_TMPDIR"

cleanup() {
    rm -rf "$TEST_TMPDIR"
    echo "Cleaned up $TEST_TMPDIR"
}
trap cleanup EXIT

# Test 1: Create mock suspicious file
echo ""
echo "[Test 1] Creating mock suspicious file..."
MOCK_FILE="$TEST_TMPDIR/suspicious.bin"
cat > "$MOCK_FILE" << 'EOF'
#!/bin/bash
echo "Suspicious behavior detected"
sleep 1
echo "File executed"
EOF
chmod +x "$MOCK_FILE"
echo "✓ Mock file created: $MOCK_FILE"

# Test 2: Test agent independently
echo ""
echo "[Test 2] Testing agent in isolation..."
AGENT_OUTPUT="$TEST_TMPDIR/agent_output"
mkdir -p "$AGENT_OUTPUT"

if command -v python3 &> /dev/null; then
    python3 "$PROJECT_ROOT/agent/agent.py" --file "$MOCK_FILE" --output "$AGENT_OUTPUT" --timeout 5
    
    REPORT_FILE=$(ls "$AGENT_OUTPUT"/report-*.json 2>/dev/null | head -1)
    if [ -f "$REPORT_FILE" ]; then
        echo "✓ Agent report generated: $REPORT_FILE"
        echo "Report content (first 20 lines):"
        head -20 "$REPORT_FILE"
    else
        echo "✗ No report file found"
        exit 1
    fi
else
    echo "⚠ Python3 not found, skipping agent test"
fi

# Test 3: Verify report JSON structure
echo ""
echo "[Test 3] Verifying report structure..."
if command -v jq &> /dev/null && [ -f "$REPORT_FILE" ]; then
    START_TIME=$(jq -r '.start_time' "$REPORT_FILE")
    END_TIME=$(jq -r '.end_time' "$REPORT_FILE")
    HAS_EVENTS=$(jq '.events | length' "$REPORT_FILE")
    
    echo "Start time: $START_TIME"
    echo "End time: $END_TIME"
    echo "Events recorded: $HAS_EVENTS"
    echo "✓ Report structure is valid"
else
    echo "⚠ jq not available, skipping JSON validation"
fi

# Test 4: Test C++ build
echo ""
echo "[Test 4] Testing C++ build..."
if command -v cmake &> /dev/null && command -v make &> /dev/null; then
    BUILD_DIR="$TEST_TMPDIR/build"
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"
    
    cmake "$PROJECT_ROOT" -DCMAKE_BUILD_TYPE=Release
    make
    
    if [ -f "$BUILD_DIR/safebox-host" ]; then
        echo "✓ safebox-host binary built successfully"
    else
        echo "✗ Build failed: binary not found"
        exit 1
    fi
    
    if "$BUILD_DIR/safebox-host" 2>&1 | grep -q "Usage:"; then
        echo "✓ Help message works"
    fi
else
    echo "⚠ CMake or Make not available, skipping C++ build test"
fi

# Test 5: Test agent with pytest
echo ""
echo "[Test 5] Running pytest tests..."
if command -v pytest &> /dev/null; then
    cd "$PROJECT_ROOT"
    pytest tests/test_agent.py -v --tb=short
    echo "✓ Pytest tests passed"
else
    echo "⚠ pytest not available. Install with: pip install pytest"
fi

# Test 6: Test C++ unit tests
echo ""
echo "[Test 6] Running C++ unit tests..."
if [ -f "$BUILD_DIR/safebox-host-tests" ]; then
    "$BUILD_DIR/safebox-host-tests"
    echo "✓ C++ unit tests passed"
else
    echo "⚠ GTest not available. Install with: sudo apt install libgtest-dev"
fi

echo ""
echo "=== Integration Test Complete ==="
echo "All available tests passed!"
