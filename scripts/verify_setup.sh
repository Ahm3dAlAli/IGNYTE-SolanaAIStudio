#!/bin/bash
# Verify Solana Swarm setup

set -e

echo "🔍 Verifying Solana Swarm Setup"
echo "==============================="

# Check Python installation
echo "Checking Python installation..."
python3 --version || { echo "❌ Python 3 not found"; exit 1; }
echo "✅ Python found"

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run ./scripts/quickstart.sh first"
    exit 1
fi
echo "✅ Virtual environment found"