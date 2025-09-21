#!/bin/bash
# Create a new Solana wallet for development

set -e

echo "🔑 Creating Solana Development Wallet"
echo "====================================="

# Set network to devnet
solana config set --url https://api.devnet.solana.com

# Generate new keypair
echo "Generating new keypair..."
solana-keygen new --outfile ~/.config/solana/id.json --force

# Get wallet address
wallet_address=$(solana address)
echo "✅ Wallet created: $wallet_address"

# Request devnet SOL
echo "💰 Requesting devnet SOL..."
solana airdrop 2

# Check balance
balance=$(solana balance)
echo "✅ Wallet balance: $balance"

# Update .env file if it exists
if [ -f .env ]; then
    # Update or add SOLANA_WALLET_PATH
    if grep -q "SOLANA_WALLET_PATH" .env; then
        sed -i.bak 's|^SOLANA_WALLET_PATH=.*|SOLANA_WALLET_PATH=~/.config/solana/id.json|' .env
    else
        echo "SOLANA_WALLET_PATH=~/.config/solana/id.json" >> .env
    fi
    echo "✅ Updated .env file with wallet path"
fi

echo ""
echo "🎉 Solana wallet setup completed!"
echo "Wallet address: $wallet_address"
echo "Network: devnet"
echo "Balance: $balance"
echo ""
echo "⚠️  This is a DEVELOPMENT wallet. Never use it on mainnet!"