!/bin/bash
# Interactive chat launcher for Solana Swarm

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Launching Solana Swarm Chat Interface${NC}"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Please run ./scripts/quickstart.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if package is installed
if ! python -c "import solana_swarm" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Solana Swarm not installed in development mode${NC}"
    echo "Installing..."
    pip install -e .
fi

# Check environment variables
if [ -z "$LLM_API_KEY" ]; then
    echo -e "${YELLOW}⚠️ LLM_API_KEY not set${NC}"
    echo "Please set your API key in .env file"
    echo "Example: LLM_API_KEY=your_openrouter_key_here"
fi

# Launch chat interface
echo -e "${GREEN}✅ Starting chat interface...${NC}"
echo ""

# Pass any command line arguments to the chat interface
python -m solana_swarm.cli.chat "$@"

echo ""
echo -e "${BLUE}👋 Chat session ended${NC}"
```

## 13. scripts/solana-swarm
```bash
#!/bin/bash
# Main CLI launcher for Solana Swarm

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Please run ./scripts/quickstart.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if package is installed
if ! python -c "import solana_swarm" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Installing Solana Swarm...${NC}"
    pip install -e .
fi

# Run the CLI with all passed arguments
python -m solana_swarm.cli.main "$@"