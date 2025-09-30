import asyncio
from solana_swarm.integrations.jupiter.client import JupiterClient

async def test_jupiter():
    """Test Jupiter DEX aggregator"""
    print("🪐 Testing Jupiter Integration...")
    
    client = JupiterClient()
    
    try:
        # Test supported tokens
        tokens = await client.get_supported_tokens()
        print(f"📝 Jupiter supports {len(tokens)} tokens")
        
        # Test price quote
        sol_mint = "So11111111111111111111111111111111111111112"  # SOL
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
        
        price_data = await client.get_price(
            input_mint=sol_mint,
            output_mint=usdc_mint,
            amount=1000000000  # 1 SOL (9 decimals)
        )
        
        print(f"💱 Jupiter Price (1 SOL): {price_data['price']:.2f} USDC")
        
        # Test quote
        quote = await client.get_quote(
            input_mint=sol_mint,
            output_mint=usdc_mint,
            amount=1000000000,  # 1 SOL
            slippage_bps=50  # 0.5% slippage
        )
        
        print(f"📊 Quote - In: {quote.in_amount}, Out: {quote.out_amount}")
        print(f"🎯 Price Impact: {quote.price_impact_pct}%")
        print("✅ Jupiter test passed!")
        
    except Exception as e:
        print(f"❌ Jupiter test failed: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_jupiter())