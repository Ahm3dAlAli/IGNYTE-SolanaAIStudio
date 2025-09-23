"""
Tests for SwarmAgent core functionality
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
from solana_swarm.core.llm_provider import LLMConfig


@pytest.fixture
def swarm_config():
    """Create test swarm configuration."""
    return SwarmConfig(
        role="test_agent",
        min_confidence=0.7,
        min_votes=2,
        timeout=10.0,
        llm=LLMConfig(
            provider="openrouter",
            api_key="test_key", 
            model="anthropic/claude-3.5-sonnet",
            temperature=0.7
        )
    )


@pytest.fixture
async def swarm_agent(swarm_config):
    """Create initialized swarm agent."""
    agent = SwarmAgent(swarm_config)
    await agent.initialize()
    return agent


@pytest.mark.asyncio
async def test_swarm_agent_initialization(swarm_config):
    """Test swarm agent initialization."""
    agent = SwarmAgent(swarm_config)
    assert not agent._initialized
    
    await agent.initialize()
    assert agent._initialized
    assert agent._is_running
    assert agent.config.role == "test_agent"


@pytest.mark.asyncio
async def test_swarm_agent_join_swarm():
    """Test joining a swarm."""
    config1 = SwarmConfig(role="agent1")
    config2 = SwarmConfig(role="agent2")
    config3 = SwarmConfig(role="agent3")
    
    agent1 = SwarmAgent(config1)
    agent2 = SwarmAgent(config2)
    agent3 = SwarmAgent(config3)
    
    await agent1.initialize()
    await agent2.initialize()
    await agent3.initialize()
    
    # Agent1 joins with agent2 and agent3
    await agent1.join_swarm([agent2, agent3])
    
    assert len(agent1.swarm_peers) == 2
    assert agent2 in agent1.swarm_peers
    assert agent3 in agent1.swarm_peers
    
    # Check bidirectional connections
    assert agent1 in agent2.swarm_peers
    assert agent1 in agent3.swarm_peers


@pytest.mark.asyncio
async def test_evaluate_proposal(swarm_agent):
    """Test proposal evaluation."""
    proposal = {
        "type": "trade",
        "params": {"token": "SOL", "amount": 1.0},
        "proposer": "test_proposer"
    }
    
    with patch.object(swarm_agent, 'evaluate') as mock_evaluate:
        mock_evaluate.return_value = {
            "decision": "approve",
            "confidence": 0.8,
            "reasoning": "Test reasoning"
        }
        
        result = await swarm_agent.evaluate_proposal(proposal)
        
        assert result["decision"] == "approve"
        assert result["confidence"] == 0.8
        assert "reasoning" in result


@pytest.mark.asyncio
async def test_propose_action_consensus():
    """Test action proposal with consensus."""
    # Create multiple agents
    configs = [
        SwarmConfig(role="market_analyzer", min_confidence=0.7),
        SwarmConfig(role="risk_manager", min_confidence=0.8),
        SwarmConfig(role="decision_maker", min_confidence=0.75)
    ]
    
    agents = []
    for config in configs:
        agent = SwarmAgent(config)
        await agent.initialize()
        agents.append(agent)
    
    # Form swarm
    await agents[0].join_swarm(agents[1:])
    
    # Mock evaluation responses
    mock_votes = [
        {"decision": "approve", "confidence": 0.8, "reasoning": "Good market conditions"},
        {"decision": "approve", "confidence": 0.85, "reasoning": "Low risk assessment"},
        {"decision": "approve", "confidence": 0.9, "reasoning": "Optimal strategy"}
    ]
    
    for i, agent in enumerate(agents):
        with patch.object(agent, 'evaluate_proposal') as mock_eval:
            mock_eval.return_value = mock_votes[i]
    
    # Propose action
    proposal_params = {
        "token_pair": "SOL/USDC",
        "amount": 100,
        "direction": "buy"
    }
    
    result = await agents[0].propose_action("trade", proposal_params)
    
    assert result["consensus"] is True
    assert result["approval_rate"] >= 0.8
    assert result["total_votes"] == 2  # Peers only, not self
    assert len(result["reasons"]) == 2


@pytest.mark.asyncio
async def test_propose_action_no_consensus():
    """Test action proposal without consensus."""
    configs = [
        SwarmConfig(role="agent1", min_confidence=0.8),
        SwarmConfig(role="agent2", min_confidence=0.8)
    ]
    
    agents = []
    for config in configs:
        agent = SwarmAgent(config)
        await agent.initialize()
        agents.append(agent)
    
    await agents[0].join_swarm([agents[1]])
    
    # Mock mixed votes (no consensus)
    mock_votes = [
        {"decision": "reject", "confidence": 0.9, "reasoning": "High risk"},
    ]
    
    with patch.object(agents[1], 'evaluate_proposal') as mock_eval:
        mock_eval.return_value = mock_votes[0]
    
    result = await agents[0].propose_action("trade", {"amount": 1000})
    
    assert result["consensus"] is False
    assert result["approval_rate"] < 0.8


@pytest.mark.asyncio
async def test_agent_cleanup(swarm_agent):
    """Test agent cleanup."""
    assert swarm_agent._initialized
    assert swarm_agent._is_running
    
    await swarm_agent.cleanup()
    
    assert not swarm_agent._initialized
    assert not swarm_agent._is_running
    assert len(swarm_agent.swarm_peers) == 0


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager functionality."""
    config = SwarmConfig(role="test_agent")
    
    async with SwarmAgent(config) as agent:
        assert agent._initialized
        assert agent._is_running
    
    # Should be cleaned up after context exit
    assert not agent._initialized
    assert not agent._is_running


@pytest.mark.asyncio
async def test_evaluate_with_llm_mock():
    """Test evaluation with mocked LLM."""
    config = SwarmConfig(
        role="market_analyzer",
        llm=LLMConfig(
            provider="openrouter",
            api_key="test_key",
            model="test_model"
        )
    )
    
    agent = SwarmAgent(config)
    
    with patch('solana_swarm.core.llm_provider.create_llm_provider') as mock_create:
        mock_llm = AsyncMock()
        mock_llm.query.return_value = '{"decision": "approve", "confidence": 0.85, "reasoning": "Test reasoning"}'
        mock_create.return_value = mock_llm
        
        await agent.initialize()
        
        context = {"test": "data"}
        result = await agent.evaluate(context)
        
        assert result["decision"] == "approve"
        assert result["confidence"] == 0.85
        assert "reasoning" in result


@pytest.mark.asyncio  
async def test_error_handling():
    """Test error handling in agent operations."""
    config = SwarmConfig(role="test_agent")
    agent = SwarmAgent(config)
    
    # Test evaluation before initialization
    result = await agent.evaluate_proposal({"type": "test"})
    assert result["decision"] == "reject"
    assert "not running" in result["reasoning"].lower()
    
    # Test with LLM error
    await agent.initialize()
    with patch.object(agent, 'evaluate') as mock_eval:
        mock_eval.side_effect = Exception("LLM Error")
        
        result = await agent.evaluate_proposal({"type": "test"})
        assert result["decision"] == "reject"
        assert "failed" in result["reasoning"].lower()


def test_swarm_config_validation():
    """Test SwarmConfig validation."""
    # Valid config
    config = SwarmConfig(role="test")
    assert config.role == "test"
    
    # Invalid confidence
    with pytest.raises(ValueError):
        SwarmConfig(role="test", min_confidence=1.5)
    
    # Invalid votes
    with pytest.raises(ValueError):
        SwarmConfig(role="test", min_votes=0)
    
    # Invalid timeout
    with pytest.raises(ValueError):
        SwarmConfig(role="test", timeout=-1)