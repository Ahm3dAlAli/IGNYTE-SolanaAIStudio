#!/bin/bash
# Solana Swarm Intelligence Framework - Quick Start Script

set -e

echo "🚀 Solana Swarm Intelligence Framework - Quick Start"
echo "=================================================="

# Check if Python 3.8+ is installed
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ is required. Found Python $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "📥 Installing development dependencies..."
pip install -r dev-requirements.txt

# Install in development mode
echo "🔧 Installing Solana Swarm in development mode..."
pip install -e .

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p logs
mkdir -p strategies
mkdir -p data
mkdir -p keypairs

# Copy environment template
if [ ! -f .env ]; then
    echo "📋 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys and configuration"
fi

# Check if Solana CLI is installed
if command -v solana &> /dev/null; then
    echo "✅ Solana CLI found"
    
    # Check if wallet exists
    if [ ! -f ~/.config/solana/id.json ]; then
        echo "🔑 No Solana wallet found. Creating new wallet..."
        ./scripts/create_solana_wallet.sh
    else
        echo "✅ Solana wallet found"
    fi
else
    echo "⚠️  Solana CLI not found. Installing..."
    
    # Install Solana CLI
    sh -c "$(curl -sSfL https://release.solana.com/v1.16.0/install)"
    export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
    
    echo "✅ Solana CLI installed"
    echo "🔑 Creating Solana wallet..."
    ./scripts/create_solana_wallet.sh
fi

# Run verification
echo "🔍 Running system verification..."
python -m solana_swarm.cli.main verify

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: source venv/bin/activate"
echo "3. Test with: solana-swarm verify"
echo "4. Start chatting: swarm-chat"
echo ""
echo "For help: solana-swarm --help"
