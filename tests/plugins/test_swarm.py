# test_swarm.py
import asyncio
from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
from solana_swarm.core.llm_provider import LLMConfig
import os
async def test_swarm():
    """Test agent swarm functionality"""
    print("🐝 Testing Agent Swarm...")
    
    # Configure LLM (required for swarm agents)
    llm_config = LLMConfig(
        provider="openrouter",
        api_key=os.getenv('LLM_API_KEY', 'demo_key'),
        model="anthropic/claude-3.5-sonnet"
    )
    
    # Create agents
    agents = []
    roles = ['market_analyzer', 'risk_manager', 'strategy_optimizer']
    
    try:
        for role in roles:
            config = SwarmConfig(
                role=role,
                min_confidence=0.7,
                llm=llm_config
            )
            agent = SwarmAgent(config)
            await agent.initialize()
            agents.append(agent)
            print(f"✅ Created {role} agent")
        
        # Form swarm
        await agents[0].join_swarm(agents[1:])
        print(f"🔗 Formed swarm with {len(agents)} agents")
        
        # Test proposal
        proposal_params = {
            "token": "SOL",
            "action": "analyze_market",
            "amount": 1.0
        }
        
        result = await agents[0].propose_action("analysis", proposal_params)
        
        print(f"🗳️  Swarm Decision:")
        print(f"   Consensus: {'✅ Yes' if result['consensus'] else '❌ No'}")
        print(f"   Approval Rate: {result['approval_rate']:.1%}")
        print(f"   Total Votes: {result['total_votes']}")
        
    except Exception as e:
        print(f"❌ Swarm test failed: {e}")
    finally:
        for agent in agents:
            await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(test_swarm())