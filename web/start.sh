#!/bin/bash
# Start SafeBox CPU Monitor Web Dashboard

echo "🔒 SafeBox CPU Monitor - Web Dashboard"
echo "======================================"
echo

# Check if in correct directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Must run from /home/ubuntu/SafeBox/web/"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Start the server
echo
echo "✅ Starting web server..."
echo "🌐 Open: http://localhost:5000"
echo "⏹️  Press Ctrl+C to stop"
echo "======================================"
echo

python3 app.py
