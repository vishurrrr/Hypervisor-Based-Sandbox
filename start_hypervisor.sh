#!/bin/bash
# SafeBox Hypervisor Sandbox - Quick Start Script

echo "🔒 SafeBox Hypervisor Sandbox - Setup"
echo "===================================="

# Navigate to web directory
cd /home/ubuntu/SafeBox/web

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install Flask==2.3.3 Flask-CORS==4.0.0 psutil==5.9.5 -q

# Create sandbox reports directory
echo "📁 Creating sandbox directories..."
mkdir -p ../sandbox-reports/{reports,quarantine}

# Start the hypervisor dashboard
echo ""
echo "🚀 Starting SafeBox Hypervisor Dashboard..."
echo ""
echo "=========================================="
echo "📊 Dashboard: http://localhost:5000"
echo "📋 Features:"
echo "   - 🟢 Real-time CPU Monitoring"
echo "   - 🔬 Malware Sandbox"
echo "   - 🔍 Threat Analysis"
echo "   - 📊 Process Management"
echo "=========================================="
echo ""

python3 app_hypervisor.py
