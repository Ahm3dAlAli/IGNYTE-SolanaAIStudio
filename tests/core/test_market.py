import asyncio
from solana_swarm.core.market_data import MarketDataManager

async def test_market_data():
    """Test market data fetching"""
    print("📊 Testing Market Data...")
    
    async with MarketDataManager() as market:
        try:
            # Test SOL price
            sol_data = await market.get_token_price('sol')
            print(f"💰 SOL Price: ${sol_data['price']:.2f}")
            print(f"📈 24h Change: {sol_data.get('price_change_24h', 0):.2f}%")
            print(f"📡 Source: {sol_data.get('source', 'Unknown')}")
            
            # Test market overview
            overview = await market.get_market_overview()
            print(f"🌐 Market Overview:")
            for token, data in overview.get('tokens', {}).items():
                if 'error' not in data:
                    print(f"   {token}: ${data['price']:.2f}")
            
            print("✅ Market data test passed!")
            
        except Exception as e:
            print(f"❌ Market data test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_market_data())