import asyncio
import os
from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig

async def test_solana_connection():
    """Test basic Solana connection"""
    print("🔗 Testing Solana Connection...")
    
    config = SolanaConfig(
        network='devnet',
        wallet_path=os.path.expanduser('~/.config/solana/id.json')
    )
    
    async with SolanaConnection(config) as connection:
        # Test wallet connection
        balance = await connection.get_balance()
        print(f"💰 Wallet Balance: {balance} SOL")
        
        # Test network stats
        stats = await connection.get_network_stats()
        print(f"📊 Network TPS: {stats.get('tps', 'Unknown')}")
        print(f"🌐 Network: {stats.get('network', 'Unknown')}")
        
        # Test account info
        account_info = await connection.get_account_info(connection.public_key)
        if account_info:
            print(f"📋 Account lamports: {account_info.get('lamports', 0)}")
        
        print("✅ Solana connection test passed!")

if __name__ == "__main__":
    asyncio.run(test_solana_connection())