#!/bin/bash
# Solana Swarm CLI - Quick Reference Card
# Copy this to test_cli.sh and run: bash test_cli.sh

echo "🚀 Solana Swarm CLI Quick Test"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to run and display command
run_cmd() {
    echo -e "${BLUE}➜ $1${NC}"
    eval $1
    echo ""
}

echo "📋 ESSENTIAL COMMANDS TO TEST:"
echo ""

# 1. Basic Commands
echo -e "${GREEN}1. BASIC COMMANDS${NC}"
run_cmd "solana-swarm --help | head -20"

# 2. Configuration
echo -e "${GREEN}2. CONFIGURATION${NC}"
run_cmd "solana-swarm config env | head -10"

# 3. Solana Status
echo -e "${GREEN}3. SOLANA STATUS${NC}"
run_cmd "solana-swarm wallet --network devnet"
run_cmd "solana-swarm status --network devnet"

# 4. Market Data
echo -e "${GREEN}4. MARKET DATA${NC}"
run_cmd "solana-swarm price sol"

# 5. Agent Validation
echo -e "${GREEN}5. AGENT VALIDATION${NC}"
run_cmd "solana-swarm validate"

echo "================================"
echo "✅ Quick tests complete!"
echo ""
echo "📖 NEXT COMMANDS TO TRY:"
echo ""
echo -e "${YELLOW}Interactive Mode:${NC}"
echo "  solana-swarm chat"
echo ""
echo -e "${YELLOW}Run Agents (Press Ctrl+C to stop):${NC}"
echo "  solana-swarm run price-monitor --timeout 120"
echo "  solana-swarm run price-monitor decision-maker --timeout 300"
echo ""
echo -e "${YELLOW}Create Components:${NC}"
echo "  solana-swarm create agent my-trader --role market_analyzer"
echo "  solana-swarm create strategy my-strategy --dexes jupiter,raydium"
echo ""
echo -e "${YELLOW}Advanced Testing:${NC}"
echo "  python cli_test_suite.py      # Automated test suite"
echo "  python comp_test.py            # Full integration test"
echo "  python quicktest.py            # Quick functionality test"
echo ""
echo "📚 Full Reference: See CLI Command Reference artifact"
echo ""

# Create a test menu
echo "================================"
echo "🎮 INTERACTIVE TEST MENU"
echo "================================"
echo ""
echo "What would you like to test?"
echo ""
echo "1. Run Price Monitor (60 seconds)"
echo "2. Run Multi-Agent System (120 seconds)"
echo "3. Check Wallet & Balance"
echo "4. Get SOL Price"
echo "5. Create Test Agent"
echo "6. Start Chat Interface"
echo "7. Run Full Test Suite"
echo "8. Exit"
echo ""
read -p "Enter choice (1-8): " choice

case $choice in
    1)
        echo "Starting Price Monitor..."
        timeout 60 solana-swarm run price-monitor --network devnet || echo "Monitoring complete"
        ;;
    2)
        echo "Starting Multi-Agent System..."
        timeout 120 solana-swarm run price-monitor decision-maker --network devnet || echo "Monitoring complete"
        ;;
    3)
        echo "Checking Wallet..."
        solana-swarm wallet --network devnet
        solana balance
        ;;
    4)
        echo "Getting SOL Price..."
        solana-swarm price sol
        ;;
    5)
        echo "Creating Test Agent..."
        solana-swarm create agent test-trader --role market_analyzer --dexes jupiter
        ls -la solana_swarm/agents/test-trader/ 2>/dev/null || echo "Agent created in current directory"
        ;;
    6)
        echo "Starting Chat Interface..."
        solana-swarm chat
        ;;
    7)
        echo "Running Full Test Suite..."
        python cli_test_suite.py
        ;;
    8)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        ;;
esac

echo ""
echo "================================"
echo "✨ Testing session complete!"
echo "================================"