#!/bin/bash
# Quick Setup Script for Solana Integration Testing

set -e

echo "🚀 Solana Swarm Quick Setup"
echo "============================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python installation...${NC}"
if python3 --version &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    echo -e "✅ Python ${PYTHON_VERSION} found"
    
    # Check if version is 3.10+
    if [[ $(echo "${PYTHON_VERSION} >= 3.10" | bc -l) == 1 ]] 2>/dev/null || python3 -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
        echo -e "✅ Python version is compatible"
    else
        echo -e "${YELLOW}⚠️  Python 3.10+ recommended, but will try to proceed${NC}"
    fi
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    echo -e "${YELLOW}⚠️  requirements.txt not found. Make sure you're in the project root directory${NC}"
fi

# Create virtual environment
echo -e "${BLUE}Setting up virtual environment...${NC}"
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    echo -e "✅ Virtual environment created"
else
    echo -e "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "✅ Virtual environment activated"

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip --quiet
echo -e "✅ Pip upgraded"

# Install requirements
echo -e "${BLUE}Installing Python dependencies...${NC}"
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt --quiet
    echo -e "✅ Core dependencies installed"
else
    echo -e "${YELLOW}⚠️  requirements.txt not found, installing minimal dependencies${NC}"
    pip install --quiet \
        solana>=0.30.0 \
        solders>=0.18.0 \
        aiohttp>=3.8.0 \
        pydantic>=2.0.0 \
        python-dotenv>=1.0.0 \
        rich>=13.0.0 \
        click>=8.0.0 \
        PyYAML>=6.0
fi

# Install development dependencies if available
if [[ -f "dev-requirements.txt" ]]; then
    echo -e "${BLUE}Installing development dependencies...${NC}"
    pip install -r dev-requirements.txt --quiet
    echo -e "✅ Development dependencies installed"
fi

# Install package in development mode
echo -e "${BLUE}Installing Solana Swarm in development mode...${NC}"
pip install -e . --quiet
echo -e "✅ Solana Swarm installed"

# Create .env file if it doesn't exist
echo -e "${BLUE}Setting up environment configuration...${NC}"
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        echo -e "✅ Created .env file from template"
    else
        # Create basic .env file
        cat > .env << EOF
# Solana Configuration
SOLANA_NETWORK=devnet
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_WALLET_PATH=~/.config/solana/id.json
SOLANA_COMMITMENT=confirmed

# LLM Configuration (Required for agents)
LLM_PROVIDER=openrouter
LLM_API_KEY=your_api_key_here
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Market Data (Optional)
COINGECKO_API_KEY=

# Development Settings
ENVIRONMENT=development
DEBUG=true
DRY_RUN=true
LOG_LEVEL=INFO
EOF
        echo -e "✅ Created basic .env file"
    fi
else
    echo -e "✅ .env file already exists"
fi

# Check for Solana CLI
echo -e "${BLUE}Checking Solana CLI...${NC}"
if command -v solana &> /dev/null; then
    SOLANA_VERSION=$(solana --version | head -n1)
    echo -e "✅ ${SOLANA_VERSION}"
    
    # Check current config
    CURRENT_URL=$(solana config get | grep "RPC URL" | awk '{print $3}')
    if [[ "$CURRENT_URL" == *"devnet"* ]]; then
        echo -e "✅ Already configured for devnet"
    else
        echo -e "${BLUE}Configuring Solana CLI for devnet...${NC}"
        solana config set --url https://api.devnet.solana.com
        echo -e "✅ Configured for devnet"
    fi
    
    # Check for wallet
    if [[ -f ~/.config/solana/id.json ]]; then
        WALLET_ADDRESS=$(solana address 2>/dev/null || echo "unknown")
        echo -e "✅ Wallet found: ${WALLET_ADDRESS}"
        
        # Check balance
        BALANCE=$(solana balance 2>/dev/null || echo "0 SOL")
        echo -e "💰 Balance: ${BALANCE}"
        
        if [[ "$BALANCE" == "0 SOL" ]] || [[ "$BALANCE" == *"0.0"* ]]; then
            echo -e "${YELLOW}⚠️  Low balance detected${NC}"
            echo -e "${BLUE}Requesting devnet airdrop...${NC}"
            if solana airdrop 2 2>/dev/null; then
                NEW_BALANCE=$(solana balance 2>/dev/null || echo "unknown")
                echo -e "✅ Airdrop successful: ${NEW_BALANCE}"
            else
                echo -e "${YELLOW}⚠️  Airdrop failed (rate limited). Try: solana airdrop 1${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  No wallet found${NC}"
        echo -e "${BLUE}Creating new devnet wallet...${NC}"
        mkdir -p ~/.config/solana
        solana-keygen new --outfile ~/.config/solana/id.json --no-bip39-passphrase --force
        WALLET_ADDRESS=$(solana address)
        echo -e "✅ New wallet created: ${WALLET_ADDRESS}"
        
        echo -e "${BLUE}Requesting devnet airdrop...${NC}"
        if solana airdrop 2; then
            BALANCE=$(solana balance)
            echo -e "✅ Airdrop successful: ${BALANCE}"
        else
            echo -e "${YELLOW}⚠️  Airdrop failed. Try manually: solana airdrop 1${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Solana CLI not found${NC}"
    echo -e "${BLUE}Installing Solana CLI...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # macOS or Linux
        sh -c "$(curl -sSfL https://release.solana.com/v1.16.0/install)"
        export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
        echo -e "✅ Solana CLI installed"
        
        # Configure and create wallet
        solana config set --url https://api.devnet.solana.com
        mkdir -p ~/.config/solana
        solana-keygen new --outfile ~/.config/solana/id.json --no-bip39-passphrase --force
        
        echo -e "${BLUE}Requesting devnet airdrop...${NC}"
        if solana airdrop 2; then
            BALANCE=$(solana balance)
            echo -e "✅ Setup complete: ${BALANCE}"
        fi
    else
        echo -e "${YELLOW}Please install Solana CLI manually from: https://docs.solana.com/cli/install-solana-cli-tools${NC}"
    fi
fi

# Create necessary directories
echo -e "${BLUE}Creating project directories...${NC}"
mkdir -p logs strategies data configs
echo -e "✅ Project directories created"

# Run quick verification
echo -e "${BLUE}Running verification tests...${NC}"
python3 -c "
import sys
try:
    import solana_swarm
    print('✅ Solana Swarm import successful')
    
    # Test basic imports
    from solana_swarm.core.solana_integration import SolanaConnection
    from solana_swarm.core.market_data import MarketDataManager
    print('✅ Core modules import successful')
    
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
" || echo -e "${RED}❌ Verification failed${NC}"

echo ""
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Edit .env file with your API keys:"
echo "   - Get OpenRouter API key: https://openrouter.ai/"
echo "   - (Optional) Get CoinGecko API key: https://coingecko.com/api"
echo ""
echo "2. Run quick test:"
echo "   python quick_test.py"
echo ""
echo "3. Start interactive chat:"
echo "   python -m solana_swarm.cli.main chat"
echo ""
echo "4. Or run agents directly:"
echo "   python -m solana_swarm.cli.main run price-monitor decision-maker"
echo ""
echo -e "${YELLOW}⚠️  Important Notes:${NC}"
echo "- Always test on devnet first"
echo "- Never use real funds for testing"
echo "- Keep your private keys secure"
echo ""
echo -e "${BLUE}Troubleshooting:${NC}"
echo "- If imports fail: pip install -e ."
echo "- If no devnet SOL: solana airdrop 1"
echo "- For help: python -m solana_swarm.cli.main --help"