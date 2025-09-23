"""
Integration tests for Solana Swarm components
"""

import pytest
import os
from unittest.mock import AsyncMock, patch

from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
from solana_swarm.core.market_data import MarketDataManager
from solana_swarm.plugins.loader import PluginLoader
from solana_swarm.core.llm_provider import LLMConfig


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_swarm_workflow():
    """Test complete swarm workflow with multiple agents."""
    # Create swarm configuration
    configs = [
        SwarmConfig(
            role="market_analyzer",
            min_confidence=0.7,
            llm=LLMConfig(provider="openrouter", api_key="test", model="test")
        ),
        SwarmConfig(
            role="risk_manager", 
            min_confidence=0.8,
            llm=LLMConfig(provider="openrouter", api_key="test", model="test")
        )
    ]
    
    agents = []
    
    try:
        # Initialize agents
        for config in configs:
            agent = SwarmAgent(config)
            
            # Mock LLM provider
            with patch('solana_swarm.core.llm_provider.create_llm_provider') as mock_create:
                mock_llm = AsyncMock()
                mock_llm.query.return_value = '{"decision": "approve", "confidence": 0.85, "reasoning": "Integration test"}'
                mock_create.return_value = mock_llm
                
                await agent.initialize()
                agents.append(agent)
        
        # Form swarm
        await agents[0].join_swarm(agents[1:])
        
        # Test market analysis workflow
        with patch('solana_swarm.core.market_data.MarketDataManager') as mock_market:
            mock_market_instance = AsyncMock()
            mock_market_instance.get_token_price.return_value = {
                "price": 100.0,
                "change_24h": 5.0,
                "source": "test"
            }
            mock_market.return_value = mock_market_instance
            
            # Propose trading action
            proposal = {
                "token": "SOL",
                "amount": 1.0,
                "action": "buy"
            }
            
            result = await agents[0].propose_action("trade", proposal)
            
            assert "consensus" in result
            assert "approval_rate" in result
            assert result["total_votes"] >= 1
    
    finally:
        # Cleanup
        for agent in agents:
            await agent.cleanup()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_plugin_loader_integration():
    """Test plugin loader with real plugin loading."""
    loader = PluginLoader()
    
    try:
        # Mock plugin files exist
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('importlib.util.spec_from_file_location') as mock_spec:
                # Mock plugin class
                class MockPlugin:
                    def __init__(self, agent_config, plugin_config):
                        self.agent_config = agent_config
                        self.plugin_config = plugin_config
                        self._is_initialized = False
                    
                    async def initialize(self):
                        self._is_initialized = True
                    
                    async def evaluate(self, context):
                        return {"result": "test"}
                    
                    async def execute(self, operation=None, **kwargs):
                        return {"status": "success"}
                    
                    async def cleanup(self):
                        self._is_initialized = False
                
                # Mock module
                mock_module = type('MockModule', (), {'MockPlugin': MockPlugin})
                
                mock_spec_instance = AsyncMock()
                mock_spec_instance.loader.exec_module = lambda m: setattr(m, 'MockPlugin', MockPlugin)
                mock_spec.return_value = mock_spec_instance
                
                with patch('importlib.util.module_from_spec') as mock_module_from_spec:
                    mock_module_from_spec.return_value = mock_module
                    
                    # Test loading plugin
                    plugin = await loader.load_plugin("test-plugin")
                    
                    assert plugin is not None
                    assert plugin._is_initialized
    
    finally:
        await loader.cleanup()


@pytest.mark.integration
@pytest.mark.asyncio 
async def test_market_data_integration():
    """Test market data integration with fallback sources."""
    market_manager = MarketDataManager()
    
    try:
        await market_manager.initialize()
        
        # Test with mocked external APIs
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Mock CoinGecko response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "market_data": {
                    "current_price": {"usd": 100.0},
                    "total_volume": {"usd": 1000000},
                    "price_change_percentage_24h": 5.0,
                    "market_cap": {"usd": 50000000}
                }
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            # Test price fetching
            price_data = await market_manager.get_token_price("SOL")
            
            assert price_data.symbol == "SOL"
            assert price_data.price > 0
            assert price_data.source.value in ["coingecko", "jupiter", "binance"]
    
    finally:
        await market_manager.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_recovery():
    """Test system error recovery and fallback mechanisms."""
    config = SwarmConfig(
        role="test_agent",
        llm=LLMConfig(provider="openrouter", api_key="invalid", model="test")
    )
    
    agent = SwarmAgent(config)
    
    # Test initialization with invalid LLM config
    with patch('solana_swarm.core.llm_provider.create_llm_provider') as mock_create:
        mock_create.side_effect = Exception("LLM initialization failed")
        
        # Should handle initialization error gracefully
        try:
            await agent.initialize()
        except Exception as e:
            assert "LLM initialization failed" in str(e)
    
    # Test evaluation with network errors
    agent._initialized = True
    agent._is_running = True
    
    with patch.object(agent, 'evaluate') as mock_eval:
        mock_eval.side_effect = Exception("Network error")
        
        result = await agent.evaluate_proposal({"type": "test"})
        
        assert result["decision"] == "reject"
        assert "failed" in result["reasoning"].lower()
    
    await agent.cleanup()


@pytest.mark.integration 
@pytest.mark.asyncio
async def test_concurrent_agent_operations():
    """Test concurrent operations with multiple agents."""
    import asyncio
    
    configs = [SwarmConfig(role=f"agent_{i}") for i in range(3)]
    agents = []
    
    try:
        # Initialize agents concurrently
        init_tasks = []
        for config in configs:
            agent = SwarmAgent(config)
            init_tasks.append(agent.initialize())
            agents.append(agent)
        
        await asyncio.gather(*init_tasks)
        
        # Form swarm network
        await agents[0].join_swarm(agents[1:])
        
        # Test concurrent evaluations
        contexts = [{"test": f"data_{i}"} for i in range(3)]
        
        with patch.object(SwarmAgent, 'evaluate') as mock_eval:
            mock_eval.return_value = {
                "decision": "approve",
                "confidence": 0.8,
                "reasoning": "Concurrent test"
            }
            
            eval_tasks = [
                agent.evaluate_proposal({"type": "test", "data": ctx})
                for agent, ctx in zip(agents, contexts)
            ]
            
            results = await asyncio.gather(*eval_tasks)
            
            assert len(results) == 3
            for result in results:
                assert "decision" in result
                assert "confidence" in result
    
    finally:
        cleanup_tasks = [agent.cleanup() for agent in agents]
        await asyncio.gather(*cleanup_tasks)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_long_running_swarm():
    """Test long-running swarm operations and memory management."""
    config = SwarmConfig(role="long_running_test")
    agent = SwarmAgent(config)
    
    try:
        await agent.initialize()
        
        # Simulate long-running operations
        for i in range(10):
            context = {"iteration": i, "timestamp": i * 1000}
            
            with patch.object(agent, 'evaluate') as mock_eval:
                mock_eval.return_value = {
                    "decision": "approve" if i % 2 == 0 else "reject",
                    "confidence": 0.7 + (i * 0.01),
                    "reasoning": f"Iteration {i}"
                }
                
                result = await agent.evaluate_proposal({
                    "type": "test",
                    "iteration": i
                })
                
                assert "decision" in result
                assert result["confidence"] > 0.7
            
            # Small delay to simulate real-world timing
            await asyncio.sleep(0.01)
        
        # Verify agent is still responsive
        assert agent._is_running
        assert agent._initialized
    
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])