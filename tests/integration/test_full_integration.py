import asyncio
import os
from solana_swarm.core.market_data import MarketDataManager
from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig
from solana_swarm.plugins.loader import PluginLoader

async def full_integration_test():
    """Complete integration test"""
    print("🚀 Running Full Integration Test...")
    
    # Test 1: Solana Connection
    print("\n1️⃣ Testing Solana Connection...")
    config = SolanaConfig(
        network='devnet',
        wallet_path=os.path.expanduser('~/.config/solana/id.json')
    )
    
    async with SolanaConnection(config) as solana:
        balance = await solana.get_balance()
        print(f"   Wallet Balance: {balance} SOL ✅")
    
    # Test 2: Market Data
    print("\n2️⃣ Testing Market Data...")
    async with MarketDataManager() as market:
        sol_price = await market.get_token_price('sol')
        print(f"   SOL Price: ${sol_price['price']:.2f} ✅")
    
    # Test 3: DEX Data
    print("\n3️⃣ Testing DEX Integration...")
    async with MarketDataManager() as market:
        for dex in ['jupiter', 'raydium']:
            try:
                dex_data = await market.get_dex_data(dex)
                print(f"   {dex.title()} TVL: ${dex_data.tvl:,.0f} ✅")
            except Exception as e:
                print(f"   {dex.title()}: ⚠️ {e}")
    
    # Test 4: Agent Loading
    print("\n4️⃣ Testing Agent System...")
    loader = PluginLoader()
    try:
        agent = await loader.load_plugin('price-monitor')
        print(f"   Price Monitor: ✅")
        
        # Quick evaluation test
        result = await agent.evaluate({'token': 'sol', 'price': 100})
        if 'error' not in result:
            print(f"   Agent Evaluation: ✅")
        else:
            print(f"   Agent Evaluation: ⚠️ {result['error']}")
            
    except Exception as e:
        print(f"   Agent Loading: ❌ {e}")
    finally:
        await loader.cleanup()
    
    print("\n🎉 Integration test completed!")

if __name__ == "__main__":
    asyncio.run(full_integration_test())