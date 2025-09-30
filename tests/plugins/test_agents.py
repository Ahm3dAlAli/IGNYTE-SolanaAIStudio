# test_agents.py
import asyncio
from solana_swarm.plugins.loader import PluginLoader

async def test_agents():
    """Test loading and running agents"""
    print("🤖 Testing Agents...")
    
    loader = PluginLoader()
    
    try:
        # Test loading price monitor
        print("📊 Loading price monitor agent...")
        price_agent = await loader.load_plugin('price-monitor')
        
        # Test evaluation
        context = {
            'token': 'sol',
            'current_price': 100.0,
            'network': 'devnet'
        }
        
        result = await price_agent.evaluate(context)
        
        if 'error' not in result:
            print(f"✅ Price Monitor Response:")
            print(f"   Observation: {result.get('observation', '')[:100]}...")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
        else:
            print(f"❌ Price Monitor Error: {result['error']}")
        
        # Test decision maker
        print("\n🎯 Loading decision maker agent...")
        decision_agent = await loader.load_plugin('decision-maker')
        
        context = {
            'market_analysis': result,
            'current_price': 100.0,
            'network': 'devnet'
        }
        
        decision = await decision_agent.evaluate(context)
        
        if 'error' not in decision:
            print(f"✅ Decision Maker Response:")
            print(f"   Strategy: {decision.get('reasoning', '')[:100]}...")
            print(f"   Confidence: {decision.get('confidence', 0):.2f}")
            print(f"   Action: {decision.get('action_type', 'unknown')}")
        else:
            print(f"❌ Decision Maker Error: {decision['error']}")
            
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
    finally:
        await loader.cleanup()

if __name__ == "__main__":
    asyncio.run(test_agents())