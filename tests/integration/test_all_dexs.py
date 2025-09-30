import asyncio
from solana_swarm.core.market_data import MarketDataManager

async def test_all_dexs():
    """Test all DEX integrations"""
    print("🏪 Testing All DEX Integrations...")
    
    async with MarketDataManager() as market:
        # Test each DEX
        dexs = ['jupiter', 'raydium', 'orca']
        
        for dex_name in dexs:
            try:
                print(f"\n🔄 Testing {dex_name.title()}...")
                
                dex_data = await market.get_dex_data(dex_name)
                
                print(f"📊 {dex_name.title()} Stats:")
                print(f"   TVL: ${dex_data.tvl:,.0f}")
                print(f"   Volume 24h: ${dex_data.volume_24h:,.0f}")
                print(f"   Pools: {dex_data.pools_count}")
                print(f"✅ {dex_name.title()} test passed!")
                
            except Exception as e:
                print(f"❌ {dex_name.title()} test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_dexs())