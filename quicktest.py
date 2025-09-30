#!/usr/bin/env python3
"""
Quick Start Test Script for Solana Integration
Run this first to verify everything is working
"""

import asyncio
import os
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig
    from solana_swarm.core.market_data import MarketDataManager
    from solana_swarm.integrations.jupiter.client import JupiterClient
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Run: pip install -e .")
    sys.exit(1)

async def test_basic_functionality():
    """Test basic functionality step by step"""
    
    print("\n🚀 Starting Solana Integration Tests")
    print("=" * 50)
    
    # Test 1: Environment Check
    print("\n1️⃣ Checking Environment...")
    
    required_vars = ['SOLANA_NETWORK', 'SOLANA_WALLET_PATH']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Missing environment variables: {missing_vars}")
        print("Please check your .env file or set these variables")
    
    # Test 2: Solana Connection
    print("\n2️⃣ Testing Solana Connection...")
    
    try:
        config = SolanaConfig(
            network=os.getenv('SOLANA_NETWORK', 'devnet'),
            wallet_path=os.getenv('SOLANA_WALLET_PATH', '~/.config/solana/id.json')
        )
        
        async with SolanaConnection(config) as connection:
            print(f"   ✅ Connected to {config.network}")
            print(f"   📍 Wallet: {connection.public_key}")
            
            balance = await connection.get_balance()
            print(f"   💰 Balance: {balance} SOL")
            
            if balance < 0.1:
                print("   ⚠️ Low balance - consider requesting airdrop:")
                print("     solana airdrop 2")
            
            # Test network stats
            stats = await connection.get_network_stats()
            print(f"   📊 Network TPS: {stats.get('tps', 'Unknown')}")
            
    except Exception as e:
        print(f"   ❌ Solana connection failed: {e}")
        print("   💡 Try: solana-keygen new --outfile ~/.config/solana/id.json")
    
    # Test 3: Market Data
    print("\n3️⃣ Testing Market Data...")
    
    try:
        async with MarketDataManager() as market:
            # Test SOL price
            sol_data = await market.get_token_price('sol')
            print(f"   ✅ SOL Price: ${sol_data['price']:.2f}")
            print(f"   📈 24h Change: {sol_data.get('price_change_24h', 0):.2f}%")
            print(f"   📡 Source: {sol_data.get('source', 'Unknown')}")
            
    except Exception as e:
        print(f"   ❌ Market data failed: {e}")
        print("   💡 This might be due to API rate limits or network issues")
    
    # Test 4: Jupiter Integration
    print("\n4️⃣ Testing Jupiter DEX...")
    
    try:
        client = JupiterClient()
        
        # Test supported tokens
        tokens = await client.get_supported_tokens()
        print(f"   ✅ Jupiter supports {len(tokens)} tokens")
        
        # Test price quote (simplified)
        sol_mint = "So11111111111111111111111111111111111111112"  # SOL
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
        
        try:
            price_data = await client.get_price(sol_mint, usdc_mint)
            print(f"   💱 Jupiter Price (SOL/USDC): {price_data['price']:.2f}")
        except Exception as e:
            print(f"   ⚠️ Jupiter price test failed: {e}")
        
        await client.close()
        
    except Exception as e:
        print(f"   ❌ Jupiter test failed: {e}")
    
    # Test 5: Agent System
    print("\n5️⃣ Testing Agent System...")
    
    try:
        from solana_swarm.plugins.loader import PluginLoader
        
        loader = PluginLoader()
        
        # Try to load a basic agent
        try:
            agent = await loader.load_plugin('price-monitor')
            print(f"   ✅ Loaded price-monitor agent")
            
            # Simple evaluation test
            context = {
                'token': 'sol',
                'current_price': 100.0,
                'network': 'devnet'
            }
            
            result = await agent.evaluate(context)
            if 'error' not in result:
                print(f"   ✅ Agent evaluation successful")
                print(f"   🎯 Confidence: {result.get('confidence', 0):.2f}")
            else:
                print(f"   ⚠️ Agent evaluation error: {result['error']}")
                
        except Exception as e:
            print(f"   ⚠️ Agent loading failed: {e}")
            print("   💡 This might be due to missing configuration files")
        
        await loader.cleanup()
        
    except Exception as e:
        print(f"   ❌ Agent system test failed: {e}")
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print("✅ = Working correctly")
    print("⚠️  = Working with warnings") 
    print("❌ = Failed (needs attention)")
    
    print(f"\n🎯 Next Steps:")
    print(f"   1. Fix any ❌ errors above")
    print(f"   2. Make sure you have devnet SOL (solana airdrop 2)")
    print(f"   3. Set your API keys in .env file")
    print(f"   4. Try running: python -m solana_swarm.cli.main chat")

async def test_simple_trading_simulation():
    """Test a simple trading simulation"""
    print("\n🎮 Running Trading Simulation...")
    print("=" * 40)
    
    try:
        from solana_swarm.plugins.loader import PluginLoader
        
        loader = PluginLoader()
        
        # Load agents
        price_agent = await loader.load_plugin('price-monitor')
        decision_agent = await loader.load_plugin('decision-maker')
        
        print("✅ Loaded trading agents")
        
        # Simulate market analysis
        print("\n📊 Step 1: Market Analysis")
        market_context = {
            'token': 'sol',
            'current_price': 98.50,
            'network': 'devnet',
            'dex_liquidity': {'jupiter': 100000000, 'raydium': 50000000}
        }
        
        analysis = await price_agent.evaluate(market_context)
        
        if 'error' not in analysis:
            print(f"   📈 Analysis: {analysis.get('conclusion', 'No conclusion')[:80]}...")
            print(f"   🎯 Confidence: {analysis.get('confidence', 0):.1%}")
        
        # Simulate decision making
        print("\n🤔 Step 2: Strategy Decision")
        decision_context = {
            'market_analysis': analysis,
            'current_price': 98.50,
            'wallet_balance': 1.5,
            'network': 'devnet'
        }
        
        decision = await decision_agent.evaluate(decision_context)
        
        if 'error' not in decision:
            print(f"   💭 Strategy: {decision.get('conclusion', 'No strategy')[:80]}...")
            print(f"   🎯 Confidence: {decision.get('confidence', 0):.1%}")
            print(f"   🚀 Action: {decision.get('action_type', 'no action')}")
        
        # Simulate execution (dry run)
        print(f"\n🎭 Step 3: Execution Simulation")
        if decision.get('confidence', 0) > 0.75:
            print(f"   ✅ High confidence - would execute trade")
            print(f"   💰 Amount: 0.1 SOL (simulation)")
            print(f"   🏪 DEX: {decision.get('preferred_dex', 'jupiter')}")
        else:
            print(f"   ⏳ Confidence too low - holding position")
        
        await loader.cleanup()
        print(f"\n🎉 Trading simulation completed!")
        
    except Exception as e:
        print(f"❌ Trading simulation failed: {e}")

def main():
    """Main entry point"""
    print("🚀 Solana Swarm Quick Test")
    print("This will test all major components")
    print()
    
    try:
        # Run basic tests
        asyncio.run(test_basic_functionality())
        
        # Ask user if they want to run trading simulation
        print("\n" + "="*50)
        response = input("Run trading simulation test? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            asyncio.run(test_simple_trading_simulation())
        
    except KeyboardInterrupt:
        print(f"\n👋 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print(f"💡 Try running: pip install -e . && python quick_test.py")

if __name__ == "__main__":
    main()