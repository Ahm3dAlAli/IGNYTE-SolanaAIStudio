"""
Example script demonstrating Solana Swarm Intelligence Framework
"""

import asyncio
import logging
from typing import Dict, Any

from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
from solana_swarm.core.llm_provider import LLMConfig
from solana_swarm.plugins.loader import PluginLoader
from solana_swarm.core.market_data import MarketDataManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_basic_example():
    """Run basic example of agent collaboration"""
    print("🚀 Starting Solana Swarm Intelligence Example")
    print("=" * 50)
    
    try:
        # Initialize plugin loader
        loader = PluginLoader()
        
        # Load agents
        print("📦 Loading agents...")
        agents = {}
        
        agent_names = ['price-monitor', 'decision-maker', 'portfolio-manager']
        for name in agent_names:
            try:
                agent = await loader.load_plugin(name)
                agents[name] = agent
                print(f"✅ Loaded: {name}")
            except Exception as e:
                print(f"❌ Failed to load {name}: {e}")
        
        if not agents:
            print("❌ No agents loaded. Please check your configuration.")
            return
        
        # Get market context
        print("\n📊 Getting market context...")
        async with MarketDataManager() as market_data:
            market_context = await market_data.get_market_context()
            sol_price = market_context.get('sol', {}).get('price', 0)
            print(f"💰 SOL Price: ${sol_price:.2f}")
        
        # Example scenario: Analyze market conditions
        print("\n🔍 Analyzing market conditions...")
        context = {
            "query": "Analyze current SOL market conditions for potential investment",
            "market_context": market_context,
            "amount": 1000,  # $1000 investment
            "risk_tolerance": "medium"
        }
        
        # Collect agent evaluations
        results = {}
        for name, agent in agents.items():
            try:
                print(f"🤖 Consulting {name}...")
                result = await agent.evaluate(context)
                results[name] = result
                
                if 'error' not in result:
                    confidence = result.get('confidence', 0)
                    print(f"   Confidence: {confidence:.1%}")
                else:
                    print(f"   Error: {result['error']}")
                    
            except Exception as e:
                print(f"   Error: {e}")
                results[name] = {"error": str(e)}
        
        # Aggregate results
        print("\n📋 Agent Consensus Summary:")
        print("-" * 30)
        
        total_confidence = 0
        valid_results = 0
        
        for name, result in results.items():
            if 'error' not in result:
                confidence = result.get('confidence', 0)
                conclusion = result.get('conclusion', 'No conclusion')[:100] + "..."
                print(f"🤖 {name}: {confidence:.1%} - {conclusion}")
                total_confidence += confidence
                valid_results += 1
            else:
                print(f"❌ {name}: {result['error']}")
        
        # Final recommendation
        if valid_results > 0:
            avg_confidence = total_confidence / valid_results
            print(f"\n🎯 Average Confidence: {avg_confidence:.1%}")
            
            if avg_confidence >= 0.8:
                recommendation = "STRONG BUY - High agent consensus"
            elif avg_confidence >= 0.6:
                recommendation = "BUY - Moderate agent consensus"
            elif avg_confidence >= 0.4:
                recommendation = "HOLD - Mixed agent opinions"
            else:
                recommendation = "WAIT - Low agent confidence"
            
            print(f"💡 Recommendation: {recommendation}")
        else:
            print("❌ Unable to generate recommendation due to agent errors")
        
        print("\n✅ Example completed successfully!")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"❌ Example failed: {e}")
    
    finally:
        # Cleanup
        await loader.cleanup()

async def run_advanced_example():
    """Run advanced example with swarm consensus"""
    print("🚀 Starting Advanced Swarm Consensus Example")
    print("=" * 50)
    
    try:
        # Create swarm agents with different roles
        agents = []
        
        # Market Analyzer
        market_config = SwarmConfig(
            role="market_analyzer",
            min_confidence=0.7,
            llm=LLMConfig(
                provider="openrouter",
                api_key="demo_key",
                model="anthropic/claude-3.5-sonnet"
            )
        )
        
        # Risk Manager  
        risk_config = SwarmConfig(
            role="risk_manager",
            min_confidence=0.8,
            llm=LLMConfig(
                provider="openrouter", 
                api_key="demo_key",
                model="anthropic/claude-3.5-sonnet"
            )
        )
        
        # Strategy Optimizer
        strategy_config = SwarmConfig(
            role="strategy_optimizer",
            min_confidence=0.75,
            llm=LLMConfig(
                provider="openrouter",
                api_key="demo_key", 
                model="anthropic/claude-3.5-sonnet"
            )
        )
        
        print("🤖 Creating swarm agents...")
        for i, config in enumerate([market_config, risk_config, strategy_config]):
            try:
                agent = SwarmAgent(config)
                await agent.initialize()
                agents.append(agent)
                print(f"✅ Created {config.role} agent")
            except Exception as e:
                print(f"❌ Failed to create {config.role}: {e}")
        
        if len(agents) < 2:
            print("❌ Need at least 2 agents for consensus")
            return
        
        # Form swarm
        print("\n🔗 Forming agent swarm...")
        await agents[0].join_swarm(agents[1:])
        print(f"✅ Swarm formed with {len(agents)} agents")
        
        # Propose trading action
        print("\n📝 Proposing trading action...")
        proposal = {
            "type": "trade",
            "params": {
                "token_pair": "SOL/USDC",
                "amount": 1000,
                "direction": "buy",
                "max_slippage": 0.005,
                "dex": "jupiter"
            }
        }
        
        # Get consensus
        result = await agents[0].propose_action("trade", proposal["params"])
        
        print(f"\n🗳️  Consensus Result:")
        print(f"   Consensus Reached: {'✅ Yes' if result['consensus'] else '❌ No'}")
        print(f"   Approval Rate: {result['approval_rate']:.1%}")
        print(f"   Total Votes: {result['total_votes']}")
        
        # Show individual agent reasoning
        print(f"\n🧠 Agent Reasoning:")
        for i, reason in enumerate(result.get('reasons', [])):
            role = agents[i].config.role if i < len(agents) else "unknown"
            print(f"   {role}: {reason[:100]}...")
        
        if result['consensus']:
            print("\n🎉 Trade approved by swarm consensus!")
        else:
            print("\n⚠️ Trade rejected by swarm - insufficient consensus")
        
        print("\n✅ Advanced example completed!")
        
    except Exception as e:
        logger.error(f"Advanced example failed: {e}")
        print(f"❌ Advanced example failed: {e}")
    
    finally:
        # Cleanup agents
        for agent in agents:
            try:
                await agent.cleanup()
            except:
                pass

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "advanced":
        asyncio.run(run_advanced_example())
    else:
        asyncio.run(run_basic_example())

if __name__ == "__main__":
    main()
