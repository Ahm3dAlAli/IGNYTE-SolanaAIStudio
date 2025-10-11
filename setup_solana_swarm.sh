#!/bin/bash
# Complete Setup Script for Solana Swarm
# Save as: setup_solana_swarm.sh
# Run: bash setup_solana_swarm.sh

set -e

echo "🚀 Solana Swarm - Complete Setup"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Python version
echo -e "${BLUE}1. Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi
echo ""

# Check if in virtual environment
echo -e "${BLUE}2. Checking virtual environment...${NC}"
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Not in virtual environment${NC}"
    
    if [ -d "venv" ]; then
        echo "Virtual environment found. Activating..."
        source venv/bin/activate
        echo -e "${GREEN}✅ Activated existing venv${NC}"
    else
        echo "Creating new virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        echo -e "${GREEN}✅ Created and activated new venv${NC}"
    fi
else
    echo -e "${GREEN}✅ Already in virtual environment: $VIRTUAL_ENV${NC}"
fi
echo ""

# Upgrade pip
echo -e "${BLUE}3. Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}✅ Pip upgraded${NC}"
echo ""

# Install dependencies
echo -e "${BLUE}4. Installing dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✅ Installed requirements.txt${NC}"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found, installing core packages...${NC}"
    pip install --quiet \
        solana>=0.30.0 \
        solders>=0.18.0 \
        aiohttp>=3.8.0 \
        pydantic>=2.0.0 \
        python-dotenv>=1.0.0 \
        rich>=13.0.0 \
        click>=8.0.0 \
        PyYAML>=6.0 \
        typer>=0.9.0
    echo -e "${GREEN}✅ Installed core packages${NC}"
fi
echo ""

# Install in development mode
echo -e "${BLUE}5. Installing Solana Swarm in development mode...${NC}"
pip install -e . --quiet
echo -e "${GREEN}✅ Installed solana-swarm${NC}"
echo ""

# Verify installation
echo -e "${BLUE}6. Verifying installation...${NC}"
if command -v solana-swarm &> /dev/null; then
    echo -e "${GREEN}✅ solana-swarm command available${NC}"
    solana-swarm --help | head -5
elif python -m solana_swarm.cli.main --help &> /dev/null; then
    echo -e "${YELLOW}⚠️  solana-swarm command not in PATH${NC}"
    echo -e "${YELLOW}   Use: python -m solana_swarm.cli.main${NC}"
    echo ""
    echo -e "${BLUE}Adding alias to your shell...${NC}"
    
    # Detect shell and add alias
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    else
        SHELL_RC="$HOME/.profile"
    fi
    
    # Add alias if not already present
    if ! grep -q "alias solana-swarm" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Solana Swarm CLI alias" >> "$SHELL_RC"
        echo "alias solana-swarm='python -m solana_swarm.cli.main'" >> "$SHELL_RC"
        echo -e "${GREEN}✅ Added alias to $SHELL_RC${NC}"
        echo -e "${YELLOW}   Run: source $SHELL_RC${NC}"
    fi
else
    echo -e "${RED}❌ Installation verification failed${NC}"
    exit 1
fi
echo ""

# Setup environment
echo -e "${BLUE}7. Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env from template${NC}"
    else
        echo -e "${YELLOW}⚠️  Creating basic .env file...${NC}"
        cat > .env << 'EOF'
# Solana Configuration
SOLANA_NETWORK=devnet
SOLANA_WALLET_PATH=~/.config/solana/id.json
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_COMMITMENT=confirmed

# LLM Configuration
LLM_PROVIDER=openrouter
LLM_API_KEY=your_api_key_here
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_API_URL=https://openrouter.ai/api/v1

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
DRY_RUN=true
EOF
        echo -e "${GREEN}✅ Created basic .env file${NC}"
    fi
    echo -e "${YELLOW}   Please edit .env and add your API keys${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi
echo ""

# Create necessary directories
echo -e "${BLUE}8. Creating directories...${NC}"
mkdir -p logs strategies data configs
echo -e "${GREEN}✅ Created project directories${NC}"
echo ""

# Check Solana CLI
echo -e "${BLUE}9. Checking Solana CLI...${NC}"
if command -v solana &> /dev/null; then
    SOLANA_VERSION=$(solana --version)
    echo -e "${GREEN}✅ Found: $SOLANA_VERSION${NC}"
    
    # Check wallet
    if [ -f "$HOME/.config/solana/id.json" ]; then
        echo -e "${GREEN}✅ Wallet found${NC}"
        WALLET_ADDRESS=$(solana address 2>/dev/null || echo "Error reading wallet")
        echo "   Address: $WALLET_ADDRESS"
        
        # Check balance
        BALANCE=$(solana balance 2>/dev/null || echo "0 SOL")
        echo "   Balance: $BALANCE"
        
        if [[ "$BALANCE" == "0 SOL" ]] || [[ "$BALANCE" == *"0.0"* ]]; then
            echo -e "${YELLOW}⚠️  Low balance. Request airdrop with: solana airdrop 2${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No wallet found${NC}"
        echo "   Create one with: solana-keygen new"
    fi
else
    echo -e "${YELLOW}⚠️  Solana CLI not found${NC}"
    echo "   Install from: https://docs.solana.com/cli/install-solana-cli-tools"
    echo "   Or run: sh -c \"\$(curl -sSfL https://release.solana.com/stable/install)\""
fi
echo ""

# Final verification
echo -e "${BLUE}10. Running verification test...${NC}"
python3 << 'PYTHON_EOF'
import sys
try:
    from solana_swarm.core.swarm_agent import SwarmAgent
    from solana_swarm.core.agent import AgentConfig
    print("✅ Core imports successful")
    sys.exit(0)
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All imports working${NC}"
else
    echo -e "${RED}❌ Import verification failed${NC}"
    exit 1
fi
echo ""

# Summary
echo "=================================="
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo "=================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Edit .env file with your API keys:"
echo "   nano .env"
echo ""
echo "2. Test the installation:"
if command -v solana-swarm &> /dev/null; then
    echo "   solana-swarm --help"
else
    echo "   python -m solana_swarm.cli.main --help"
    echo "   OR run: source ~/.zshrc (then use 'solana-swarm')"
fi
echo ""
echo "3. Verify setup:"
echo "   python quicktest.py"
echo ""
echo "4. Start using:"
echo "   python -m solana_swarm.cli.main wallet"
echo "   python -m solana_swarm.cli.main price sol"
echo "   python -m solana_swarm.cli.main chat"
echo ""
echo "=================================="
echo ""

# Create a quick command reference
cat > QUICK_COMMANDS.txt << 'EOF'
# Solana Swarm - Quick Command Reference

# If solana-swarm command doesn't work, use this format:
python -m solana_swarm.cli.main [command]

# Examples:
python -m solana_swarm.cli.main --help
python -m solana_swarm.cli.main wallet
python -m solana_swarm.cli.main status
python -m solana_swarm.cli.main price sol
python -m solana_swarm.cli.main run price-monitor --timeout 60
python -m solana_swarm.cli.main chat

# Or add this alias to ~/.zshrc:
alias solana-swarm='python -m solana_swarm.cli.main'

# Then reload:
source ~/.zshrc
EOF

echo -e "${GREEN}✅ Created QUICK_COMMANDS.txt for reference${NC}"
echo ""