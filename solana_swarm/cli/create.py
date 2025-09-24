"""
CLI commands for creating new Solana-specific components
"""

import os
import shutil
import click
import yaml
from typing import Optional

@click.group()
def create():
    """Create new Solana components"""
    pass

@create.command()
@click.argument('name')
@click.option('--role', default=None, help='Agent role (market_analyzer/strategy_optimizer/arbitrage_agent/yield_farmer)')
@click.option('--template', default='solana_agent_template', help='Template to use')
@click.option('--path', default='solana_swarm/agents', help='Where to create the agent')
@click.option('--dexes', default='jupiter,raydium,orca', help='Comma-separated list of preferred DEXs')
def agent(name: str, role: Optional[str], template: str, path: str, dexes: str):
    """Create a new Solana agent"""
    try:
        # Get template path
        template_path = os.path.join(
            os.path.dirname(__file__), 
            '../templates', 
            'solana_agent_template'
        )
        
        # Create agent directory
        agent_path = os.path.join(path, name)
        if os.path.exists(agent_path):
            click.echo(f"Agent {name} already exists")
            return
            
        # Create directories
        os.makedirs(agent_path, exist_ok=True)
        
        # Copy template files individually if template exists
        if os.path.exists(template_path):
            for item in os.listdir(template_path):
                source = os.path.join(template_path, item)
                dest = os.path.join(agent_path, item)
                
                if os.path.isfile(source):
                    shutil.copy2(source, dest)
                elif os.path.isdir(source):
                    shutil.copytree(source, dest)
        
        # Parse DEX preferences
        preferred_dexes = [dex.strip() for dex in dexes.split(',')]
        
        # Update configuration with Solana-specific settings
        config_path = os.path.join(agent_path, 'agent.yaml')
        config = {
            'name': name,
            'role': role or 'market_analyzer',
            'description': f'Solana DeFi agent for {name}',
            'version': '0.1.0',
            'environment': 'development',
            'log_level': 'INFO',
            'llm': {
                'provider': '${LLM_PROVIDER}',
                'api_key': '${LLM_API_KEY}',
                'model': '${LLM_MODEL}',
                'temperature': 0.7,
                'max_tokens': 1500,
                'api_url': '${LLM_API_URL}'
            },
            'capabilities': [],
            'custom_settings': {
                'min_confidence_threshold': 0.7,
                'max_retries': 3,
                'timeout': 30,
                'preferred_dexes': preferred_dexes,
                'max_slippage': 0.01,
                'min_liquidity': 100000
            }
        }
        
        # Set role-specific configuration
        if role:
            if role == 'market_analyzer':
                config['capabilities'] = [
                    'price_monitoring',
                    'dex_analysis', 
                    'trend_analysis',
                    'market_assessment'
                ]
                config['llm']['system_prompt'] = """You are a Solana market analysis agent specializing in DeFi protocols.
Your role is to analyze token prices across Solana DEXs, assess liquidity conditions, and identify market trends.

Focus on:
1. SOL and SPL token price movements across Jupiter, Raydium, and Orca
2. DEX liquidity analysis and arbitrage opportunities  
3. Network performance impact on trading
4. DeFi protocol risk assessment

Always provide clear reasoning and confidence levels for your Solana market analysis."""
                
            elif role == 'strategy_optimizer':
                config['capabilities'] = [
                    'strategy_optimization',
                    'dex_routing',
                    'yield_optimization',
                    'transaction_optimization'
                ]
                config['llm']['system_prompt'] = """You are a Solana strategy optimization agent for DeFi operations.
Your role is to optimize trading strategies, DEX routing, and yield farming across Solana protocols.

Focus on:
1. Jupiter route optimization vs direct DEX trading
2. Raydium and Orca liquidity pool strategies
3. Transaction cost optimization and MEV protection
4. Yield farming opportunity assessment

Always provide actionable Solana DeFi strategies with clear risk management."""

            elif role == 'arbitrage_agent':
                config['capabilities'] = [
                    'arbitrage_detection',
                    'cross_dex_analysis',
                    'price_discrepancy_monitoring',
                    'execution_optimization'
                ]
                config['llm']['system_prompt'] = """You are a Solana arbitrage detection agent specializing in cross-DEX opportunities.
Your role is to identify profitable arbitrage opportunities across Solana DEXs.

Focus on:
1. Price discrepancies between Jupiter, Raydium, Orca, and Serum
2. Transaction cost vs profit margin analysis
3. Liquidity depth assessment for arbitrage execution
4. MEV protection and optimal execution timing

Always provide profitable arbitrage opportunities with clear execution strategies."""

            elif role == 'yield_farmer':
                config['capabilities'] = [
                    'yield_farming',
                    'liquidity_provision',
                    'apr_analysis',
                    'impermanent_loss_calculation'
                ]
                config['llm']['system_prompt'] = """You are a Solana yield farming agent specializing in DeFi protocols.
Your role is to optimize yield farming strategies across Solana DeFi platforms.

Focus on:
1. High-yield opportunities on Raydium, Orca, and other Solana DEXs
2. Impermanent loss risk assessment
3. Liquidity mining reward optimization
4. Protocol risk evaluation

Always provide yield farming strategies with clear risk-reward analysis."""
        
        # Write updated configuration
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        # Update plugin.py with Solana-specific code
        plugin_path = os.path.join(agent_path, 'plugin.py')
        plugin_code = f'''"""
{name.title()} Plugin for Solana Swarm Intelligence
Solana DeFi agent for {config.get('description', 'DeFi operations')}
"""

import logging
import os
from typing import Dict, Any, Optional
from solana_swarm.plugins.base import AgentPlugin, PluginConfig
from solana_swarm.core.agent import AgentConfig
from solana_swarm.core.market_data import MarketDataManager
from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig

logger = logging.getLogger(__name__)

class {name.title().replace("-", "")}Plugin(AgentPlugin):
    """Solana {role or 'market_analyzer'} plugin for DeFi operations"""
    
    def __init__(self, agent_config: AgentConfig, plugin_config: PluginConfig):
        super().__init__(agent_config, plugin_config)
        self.min_confidence = float(self.plugin_config.custom_settings.get('min_confidence_threshold', 0.7))
        self.preferred_dexes = self.plugin_config.custom_settings.get('preferred_dexes', {preferred_dexes})
        self.max_slippage = float(self.plugin_config.custom_settings.get('max_slippage', 0.01))
        self.min_liquidity = float(self.plugin_config.custom_settings.get('min_liquidity', 100000))
        
        self.market_data = None
        self.solana_connection = None
        self.logger = logger
        
    async def initialize(self) -> None:
        """Initialize Solana {name} agent"""
        # Initialize market data manager
        self.market_data = MarketDataManager()
        
        # Initialize Solana connection
        solana_config = SolanaConfig(
            network=os.getenv('SOLANA_NETWORK', 'devnet'),
            wallet_path=os.getenv('SOLANA_WALLET_PATH')
        )
        self.solana_connection = SolanaConnection(solana_config)
        
        self.logger.info("Solana {name} agent initialized successfully")
        
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate Solana market conditions using {name} logic"""
        try:
            # Extract context information
            query = context.get('query', '')
            current_price = context.get('price', context.get('current_price', 0))
            network = context.get('network', 'solana')
            dex_data = context.get('dex_data', {{}})
            
            # Solana-specific analysis
            observation = f"Analyzing Solana DeFi conditions with {name} agent. Current SOL price: ${{current_price:.2f}} on {{network}}."
            
            reasoning = f"As a {{self.plugin_config.role}} on Solana, I evaluate: "
            reasoning += f"DEX liquidity across {{', '.join(self.preferred_dexes)}}, "
            reasoning += f"network performance, and DeFi protocol risks. "
            reasoning += f"Market conditions show {{'favorable' if current_price > 50 else 'challenging'}} trading environment."
            
            conclusion = f"Solana {{self.plugin_config.role}} analysis complete. "
            conclusion += f"Recommended approach: {{'aggressive' if current_price > 100 else 'conservative'}} DeFi strategy "
            conclusion += f"using {{self.preferred_dexes[0] if self.preferred_dexes else 'jupiter'}} for optimal execution."
            
            return {{
                'observation': observation,
                'reasoning': reasoning,
                'conclusion': conclusion,
                'confidence': 0.8,
                'agent': '{name}',
                'role': self.plugin_config.role,
                'network': 'solana',
                'preferred_dex': self.preferred_dexes[0] if self.preferred_dexes else 'jupiter',
                'risk_level': 'medium'
            }}
            
        except Exception as e:
            self.logger.error(f"Error in Solana {{name}} evaluation: {{str(e)}}")
            return {{'error': str(e)}}
            
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Solana DeFi actions for {name} agent"""
        try:
            action_type = action.get('type', 'unknown')
            
            if action_type == 'solana_defi_strategy':
                # Execute Solana DeFi strategy
                data = action.get('data', {{}})
                current_price = data.get('current_price', 0)
                
                # Simulate transaction based on strategy
                if current_price > 100:  # Example logic
                    # Simulate Jupiter swap
                    tx_result = await self.solana_connection.swap_tokens_jupiter(
                        'So11111111111111111111111111111111111111112',  # SOL
                        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                        0.1,  # 0.1 SOL
                        self.max_slippage
                    )
                    
                    return {{
                        'status': 'success',
                        'transaction': {{
                            'protocol': 'Jupiter',
                            'amount': 0.1,
                            'signature': tx_result.get('signature', 'demo_sig'),
                            'status': 'success'
                        }}
                    }}
                else:
                    return {{
                        'status': 'success',
                        'transaction': {{
                            'protocol': 'Hold',
                            'amount': 0,
                            'status': 'success',
                            'reason': 'Market conditions favor holding'
                        }}
                    }}
                    
            elif action_type == 'analyze':
                return {{'status': 'success', 'result': f'Analysis completed by Solana {{name}}'}}
            else:
                return {{'error': f'Unsupported action type: {{action_type}}'}}
                
        except Exception as e:
            self.logger.error(f"Error executing Solana {{name}} action: {{str(e)}}")
            return {{'error': str(e)}}
            
    async def cleanup(self) -> None:
        """Cleanup Solana {name} agent resources"""
        if self.market_data:
            await self.market_data.close()
        if self.solana_connection:
            await self.solana_connection.close()
        self.logger.info("Solana {name} agent cleanup completed")
'''
        
        with open(plugin_path, 'w') as f:
            f.write(plugin_code)
        
        # Create __init__.py
        with open(os.path.join(agent_path, '__init__.py'), 'w') as f:
            f.write(f'"""{name.title()} agent for Solana Swarm Intelligence"""\n')
        
        # Create test file
        test_dir = os.path.join('tests', 'agents')
        os.makedirs(test_dir, exist_ok=True)
        
        test_code = f'''"""
Tests for Solana {name} agent
"""

import pytest
from unittest.mock import AsyncMock, patch

from solana_swarm.agents.{name}.plugin import {name.title().replace("-", "")}Plugin
from solana_swarm.core.agent import AgentConfig
from solana_swarm.plugins.base import PluginConfig


@pytest.fixture
def agent_config():
    """Create test agent config."""
    return AgentConfig(name="test-{name}")


@pytest.fixture
def plugin_config():
    """Create test plugin config."""
    return PluginConfig(
        name="{name}",
        role="{role or 'market_analyzer'}",
        capabilities={config['capabilities']},
        custom_settings={{
            "min_confidence_threshold": 0.7,
            "preferred_dexes": {preferred_dexes}
        }}
    )


@pytest.fixture
async def {name.replace("-", "_")}_plugin(agent_config, plugin_config):
    """Create {name} plugin for testing."""
    plugin = {name.title().replace("-", "")}Plugin(agent_config, plugin_config)
    await plugin.initialize()
    return plugin


@pytest.mark.asyncio
async def test_{name.replace("-", "_")}_initialization({name.replace("-", "_")}_plugin):
    """Test {name} plugin initialization."""
    assert {name.replace("-", "_")}_plugin.min_confidence == 0.7
    assert {name.replace("-", "_")}_plugin.plugin_config.role == "{role or 'market_analyzer'}"
    assert {name.replace("-", "_")}_plugin.preferred_dexes == {preferred_dexes}


@pytest.mark.asyncio
async def test_{name.replace("-", "_")}_solana_evaluation({name.replace("-", "_")}_plugin):
    """Test {name} Solana evaluation functionality."""
    context = {{
        "query": "test Solana query",
        "current_price": 100.0,
        "network": "devnet",
        "dex_data": {{"jupiter_volume": 1000000}}
    }}
    
    result = await {name.replace("-", "_")}_plugin.evaluate(context)
    
    assert "error" not in result
    assert "observation" in result
    assert "reasoning" in result
    assert "confidence" in result
    assert result["network"] == "solana"
    assert result["confidence"] >= 0.0


@pytest.mark.asyncio
async def test_{name.replace("-", "_")}_solana_execute({name.replace("-", "_")}_plugin):
    """Test {name} Solana execution functionality."""
    action = {{
        "type": "solana_defi_strategy", 
        "data": {{
            "current_price": 100.0,
            "network": "devnet"
        }}
    }}
    
    with patch.object({name.replace("-", "_")}_plugin.solana_connection, 'swap_tokens_jupiter') as mock_swap:
        mock_swap.return_value = {{"signature": "test_sig", "status": "success"}}
        
        result = await {name.replace("-", "_")}_plugin.execute(action)
        
        assert "status" in result or "error" in result
        if result.get("status") == "success":
            assert "transaction" in result


@pytest.mark.asyncio  
async def test_{name.replace("-", "_")}_error_handling({name.replace("-", "_")}_plugin):
    """Test {name} error handling."""
    # Test with invalid context
    result = await {name.replace("-", "_")}_plugin.evaluate({{}})
    
    # Should handle gracefully
    assert isinstance(result, dict)
    assert "observation" in result or "error" in result


@pytest.mark.asyncio
async def test_{name.replace("-", "_")}_dex_preferences({name.replace("-", "_")}_plugin):
    """Test DEX preference handling."""
    assert {name.replace("-", "_")}_plugin.preferred_dexes == {preferred_dexes}
    assert len({name.replace("-", "_")}_plugin.preferred_dexes) > 0
    
    # Test evaluation uses preferred DEX
    context = {{"current_price": 100.0, "network": "devnet"}}
    result = await {name.replace("-", "_")}_plugin.evaluate(context)
    
    if "error" not in result:
        assert result.get("preferred_dex") in {preferred_dexes}
'''
        
        with open(os.path.join(test_dir, f'test_{name.replace("-", "_")}.py'), 'w') as f:
            f.write(test_code)
        
        click.echo(f"✅ Solana agent '{name}' created successfully!")
        click.echo(f"📁 Files created:")
        click.echo(f"   • solana_swarm/agents/{name}/agent.yaml")
        click.echo(f"   • solana_swarm/agents/{name}/plugin.py")
        click.echo(f"   • tests/agents/test_{name.replace('-', '_')}.py")
        click.echo(f"\n🔧 Next steps:")
        click.echo(f"   1. Implement your custom Solana logic in plugin.py")
        click.echo(f"   2. Update the system prompt in agent.yaml")
        click.echo(f"   3. Configure preferred DEXs: {', '.join(preferred_dexes)}")
        click.echo(f"   4. Run tests: pytest tests/agents/test_{name.replace('-', '_')}.py")
        click.echo(f"   5. Test with: solana-swarm chat --agent {name}")
        
    except Exception as e:
        click.echo(f"❌ Error creating Solana agent: {str(e)}", err=True)

@create.command()
@click.argument('name')
@click.option('--template', default='solana_strategy_template', help='Template to use')
@click.option('--path', default='strategies', help='Where to create the strategy')
@click.option('--dexes', default='jupiter,raydium,orca', help='Target DEXs for strategy')
def strategy(name: str, template: str, path: str, dexes: str):
    """Create a new Solana DeFi strategy"""
    try:
        # Validate name
        if not name.replace("_", "").replace("-", "").isalnum():
            click.echo(f"❌ Invalid strategy name: {name}")
            return
        
        # Check if strategy already exists
        strategy_file = os.path.join(path, f"{name}.py")
        os.makedirs(path, exist_ok=True)
        
        if os.path.exists(strategy_file):
            if not click.confirm(f"Strategy '{name}' already exists. Overwrite?"):
                return
        
        # Parse DEX preferences
        target_dexes = [dex.strip() for dex in dexes.split(',')]
        
        # Get strategy details
        description = click.prompt("Strategy description", default=f"Solana DeFi strategy for {name}")
        target_agents = click.prompt("Target agents (comma-separated)", default="price-monitor,decision-maker").split(",")
        target_agents = [agent.strip() for agent in target_agents]
        
        # Create strategy file
        strategy_code = f'''"""
{name.title().replace("_", " ")} Strategy for Solana Swarm Intelligence
{description}
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
from solana_swarm.core.llm_provider import LLMConfig
from solana_swarm.plugins.loader import PluginLoader
from solana_swarm.core.market_data import MarketDataManager
from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig

logger = logging.getLogger(__name__)

class {name.title().replace("_", "")}Strategy:
    """
    {description}
    
    This Solana DeFi strategy coordinates multiple agents to:
    1. Analyze market conditions across Solana DEXs
    2. Assess risks and opportunities in DeFi protocols
    3. Make informed trading decisions with optimal DEX routing
    4. Execute trades safely on Solana with MEV protection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize {name} strategy for Solana."""
        self.config = config or self.get_default_config()
        self.agents = {{}}
        self.market_data = None
        self.solana_connection = None
        self.is_running = False
        
    def get_default_config(self) -> Dict[str, Any]:
        """Get default strategy configuration for Solana."""
        return {{
            "name": "{name}",
            "description": "{description}",
            "target_agents": {target_agents},
            "target_dexes": {target_dexes},
            "min_confidence": 0.8,
            "max_position_size": 1000,  # USD
            "stop_loss": 0.05,  # 5%
            "take_profit": 0.10,  # 10%
            "max_slippage": 0.01,  # 1%
            "update_interval": 300,  # 5 minutes
            "network": "devnet",  # Solana network
            "dry_run": True  # Safety first!
        }}
    
    async def initialize(self):
        """Initialize strategy and load Solana agents."""
        try:
            logger.info(f"Initializing Solana {{self.config['name']}} strategy")
            
            # Initialize market data
            self.market_data = MarketDataManager()
            
            # Initialize Solana connection
            solana_config = SolanaConfig(
                network=self.config.get("network", "devnet"),
                wallet_path=os.getenv('SOLANA_WALLET_PATH')
            )
            self.solana_connection = SolanaConnection(solana_config)
            await self.solana_connection.initialize()
            
            # Load required agents
            loader = PluginLoader()
            for agent_name in self.config["target_agents"]:
                try:
                    agent = await loader.load_plugin(agent_name)
                    self.agents[agent_name] = agent
                    logger.info(f"Loaded Solana agent: {{agent_name}}")
                except Exception as e:
                    logger.error(f"Failed to load agent {{agent_name}}: {{e}}")
            
            if not self.agents:
                raise ValueError("No Solana agents loaded successfully")
            
            self.is_running = True
            logger.info("Solana strategy initialized successfully")
            
        except Exception as e:
            logger.error(f"Solana strategy initialization failed: {{e}}")
            raise
    
    async def analyze_opportunity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Solana DeFi opportunity using multiple agents."""
        try:
            # Get Solana market context
            market_context = await self.market_data.get_market_overview()
            wallet_balance = await self.solana_connection.get_balance()
            
            # Combine contexts
            full_context = {{
                **context,
                "market_context": market_context,
                "wallet_balance": wallet_balance,
                "strategy": self.config["name"],
                "network": self.config["network"],
                "target_dexes": self.config["target_dexes"],
                "timestamp": datetime.now().isoformat()
            }}
            
            # Collect agent evaluations
            agent_results = {{}}
            for agent_name, agent in self.agents.items():
                try:
                    result = await agent.evaluate(full_context)
                    agent_results[agent_name] = result
                    logger.info(f"{{agent_name}} analysis: confidence={{result.get('confidence', 0):.2f}}")
                except Exception as e:
                    logger.error(f"Agent {{agent_name}} analysis failed: {{e}}")
                    agent_results[agent_name] = {{"error": str(e), "confidence": 0.0}}
            
            # Calculate consensus
            valid_results = [r for r in agent_results.values() if "error" not in r]
            if not valid_results:
                return {{
                    "decision": "skip",
                    "confidence": 0.0,
                    "reason": "No valid agent analysis available"
                }}
            
            avg_confidence = sum(r.get("confidence", 0) for r in valid_results) / len(valid_results)
            
            # Make strategy decision
            if avg_confidence >= self.config["min_confidence"]:
                # Find best DEX based on agent recommendations
                recommended_dex = self._select_optimal_dex(agent_results)
                
                decision = {{
                    "decision": "execute",
                    "confidence": avg_confidence,
                    "recommended_dex": recommended_dex,
                    "agent_results": agent_results,
                    "strategy": self.config["name"]
                }}
            else:
                decision = {{
                    "decision": "hold",
                    "confidence": avg_confidence,
                    "reason": f"Confidence {{avg_confidence:.2f}} below threshold {{self.config['min_confidence']}}",
                    "agent_results": agent_results
                }}
            
            return decision
            
        except Exception as e:
            logger.error(f"Solana opportunity analysis failed: {{e}}")
            return {{"decision": "error", "confidence": 0.0, "error": str(e)}}
    
    def _select_optimal_dex(self, agent_results: Dict[str, Any]) -> str:
        """Select optimal DEX based on agent recommendations."""
        # Count DEX preferences from agents
        dex_votes = {{}}
        for result in agent_results.values():
            if "error" not in result:
                preferred_dex = result.get("preferred_dex", "jupiter")
                dex_votes[preferred_dex] = dex_votes.get(preferred_dex, 0) + 1
        
        if not dex_votes:
            return self.config["target_dexes"][0]  # Default to first DEX
        
        # Return most voted DEX
        return max(dex_votes.items(), key=lambda x: x[1])[0]
    
    async def execute_strategy(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Solana DeFi strategy based on decision."""
        try:
            if decision.get("decision") != "execute":
                return {{
                    "status": "skipped",
                    "reason": decision.get("reason", "Decision was not to execute")
                }}
            
            recommended_dex = decision.get("recommended_dex", "jupiter")
            confidence = decision.get("confidence", 0)
            
            logger.info(f"Executing Solana strategy on {{recommended_dex}} with {{confidence:.2f}} confidence")
            
            # Check dry run mode
            if self.config.get("dry_run", True):
                logger.info("DRY RUN MODE: Simulating transaction")
                return {{
                    "status": "simulated",
                    "dex": recommended_dex,
                    "confidence": confidence,
                    "message": f"Strategy would execute on {{recommended_dex}} DEX"
                }}
            
            # Execute actual transaction
            if recommended_dex == "jupiter":
                result = await self.solana_connection.swap_tokens_jupiter(
                    'So11111111111111111111111111111111111111112',  # SOL
                    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                    0.1,  # 0.1 SOL
                    self.config["max_slippage"]
                )
            else:
                # For other DEXs, implement specific logic
                result = {{
                    "status": "success",
                    "message": f"Executed on {{recommended_dex}}",
                    "signature": f"demo_{{recommended_dex}}_tx"
                }}
            
            return {{
                "status": "executed",
                "dex": recommended_dex,
                "transaction": result,
                "confidence": confidence
            }}
            
        except Exception as e:
            logger.error(f"Solana strategy execution failed: {{e}}")
            return {{"status": "error", "error": str(e)}}
    
    async def run_continuous(self, duration: int = 3600):
        """Run strategy continuously for specified duration."""
        try:
            logger.info(f"Starting continuous Solana strategy for {{duration}} seconds")
            start_time = datetime.now()
            
            while (datetime.now() - start_time).total_seconds() < duration:
                try:
                    # Analyze current opportunity
                    context = {{
                        "query": "continuous strategy analysis",
                        "timestamp": datetime.now().isoformat()
                    }}
                    
                    decision = await self.analyze_opportunity(context)
                    logger.info(f"Strategy decision: {{decision.get('decision')}} (confidence: {{decision.get('confidence', 0):.2f}})")
                    
                    # Execute if decision is positive
                    if decision.get("decision") == "execute":
                        execution_result = await self.execute_strategy(decision)
                        logger.info(f"Execution result: {{execution_result.get('status')}}")
                    
                    # Wait for next cycle
                    await asyncio.sleep(self.config["update_interval"])
                    
                except Exception as e:
                    logger.error(f"Strategy cycle error: {{e}}")
                    await asyncio.sleep(60)  # Wait 1 minute before retry
            
            logger.info("Continuous strategy completed")
            
        except Exception as e:
            logger.error(f"Continuous strategy failed: {{e}}")
            raise
    
    async def cleanup(self):
        """Cleanup strategy resources."""
        try:
            if self.solana_connection:
                await self.solana_connection.close()
            
            if self.market_data:
                await self.market_data.close()
            
            for agent in self.agents.values():
                await agent.cleanup()
            
            self.is_running = False
            logger.info("Solana strategy cleanup completed")
            
        except Exception as e:
            logger.error(f"Strategy cleanup error: {{e}}")

# Example usage
async def main():
    """Example of running the Solana strategy."""
    strategy = {name.title().replace("_", "")}Strategy()
    
    try:
        await strategy.initialize()
        
        # Single analysis
        context = {{"query": "analyze current Solana DeFi opportunity"}}
        decision = await strategy.analyze_opportunity(context)
        print(f"Strategy decision: {{decision}}")
        
        # Execute if recommended
        if decision.get("decision") == "execute":
            result = await strategy.execute_strategy(decision)
            print(f"Execution result: {{result}}")
        
    finally:
        await strategy.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(strategy_file, 'w') as f:
            f.write(strategy_code)
        
        # Create strategy configuration file
        strategy_config = {
            "name": name,
            "description": description,
            "agents": target_agents,
            "target_dexes": target_dexes,
            "parameters": {
                "min_confidence": 0.8,
                "max_position_size": 1000,
                "max_slippage": 0.01,
                "network": "devnet"
            },
            "risk_management": {
                "stop_loss": 0.05,
                "take_profit": 0.10,
                "position_limit": 0.1,
                "dry_run": True
            }
        }
        
        config_file = os.path.join(path, f"{name}.yaml")
        with open(config_file, 'w') as f:
            yaml.dump(strategy_config, f, default_flow_style=False)
        
        click.echo(f"✅ Solana strategy '{name}' created successfully!")
        click.echo(f"📁 Files created:")
        click.echo(f"   • {strategy_file}")
        click.echo(f"   • {config_file}")
        click.echo(f"\n🔧 Strategy Configuration:")
        click.echo(f"   • Target DEXs: {', '.join(target_dexes)}")
        click.echo(f"   • Target Agents: {', '.join(target_agents)}")
        click.echo(f"   • Network: devnet (configurable)")
        click.echo(f"\n🚀 Next steps:")
        click.echo(f"   1. Customize strategy logic in {strategy_file}")
        click.echo(f"   2. Adjust parameters in {config_file}")
        click.echo(f"   3. Test with: python {strategy_file}")
        click.echo(f"   4. Deploy with: solana-swarm run {name}")
        
    except Exception as e:
        click.echo(f"❌ Error creating Solana strategy: {str(e)}", err=True)

@create.command()
@click.argument('name')
@click.option('--template', default='solana_project_template', help='Template to use')
def project(name: str, template: str):
    """Create a new Solana Swarm project"""
    try:
        # Create project directory
        if os.path.exists(name):
            click.echo(f"Directory {name} already exists")
            return
        
        os.makedirs(name)
        
        # Create project structure
        directories = [
            f"{name}/agents",
            f"{name}/strategies", 
            f"{name}/plugins",
            f"{name}/configs",
            f"{name}/logs",
            f"{name}/tests"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # Create main configuration
        main_config = {
            "name": name,
            "version": "0.1.0",
            "description": f"Solana Swarm Intelligence project: {name}",
            "network": "devnet",
            "agents": [],
            "strategies": [],
            "solana": {
                "network": "devnet",
                "rpc_url": "https://api.devnet.solana.com",
                "commitment": "confirmed"
            },
            "llm": {
                "provider": "openrouter",
                "model": "anthropic/claude-3.5-sonnet",
                "temperature": 0.7
            },
            "dexes": {
                "preferred": ["jupiter", "raydium", "orca"],
                "max_slippage": 0.01,
                "min_liquidity": 100000
            }
        }
        
        with open(f"{name}/solana_swarm.yaml", 'w') as f:
            yaml.dump(main_config, f, default_flow_style=False)
        
        # Create .env template
        env_content = """# Solana Swarm Configuration
LLM_PROVIDER=openrouter
LLM_API_KEY=your_api_key_here
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Solana Configuration  
SOLANA_NETWORK=devnet
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_WALLET_PATH=~/.config/solana/id.json
SOLANA_COMMITMENT=confirmed

# Market Data
COINGECKO_API_KEY=
MARKET_DATA_CACHE_TTL=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/solana_swarm.log

# Development
ENVIRONMENT=development
DEBUG=true
DRY_RUN=true
"""
        
        with open(f"{name}/.env.example", 'w') as f:
            f.write(env_content)
        
        # Create requirements.txt
        requirements = """# Solana Swarm Intelligence Framework
solana-swarm>=0.1.0

# Solana blockchain
solana>=0.30.0
solders>=0.18.0

# Core dependencies
pydantic>=2.0.0
aiohttp>=3.8.0
PyYAML>=6.0
click>=8.0.0
python-dotenv>=1.0.0
rich>=13.0.0

# Market data
ccxt>=4.1.0
pycoingecko>=3.1.0

# Development dependencies
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
"""
        
        with open(f"{name}/requirements.txt", 'w') as f:
            f.write(requirements)
        
        # Create README
        readme_content = f"""# {name.title()}

Solana Swarm Intelligence project for automated DeFi operations.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and Solana wallet path
```

3. Initialize Solana wallet (if needed):
```bash
solana-keygen new --outfile ~/.config/solana/id.json
solana airdrop 2  # For devnet testing
```

## Usage

### Create agents:
```bash
solana-swarm create agent my-trader --role market_analyzer
solana-swarm create agent my-optimizer --role strategy_optimizer
```

### Create strategies:
```bash
solana-swarm create strategy arbitrage-bot --dexes jupiter,raydium,orca
```

### Run agents:
```bash
solana-swarm run my-trader my-optimizer --network devnet
```

### Interactive chat:
```bash
solana-swarm chat
```

## Project Structure

- `agents/` - Custom agent configurations
- `strategies/` - Trading strategies
- `plugins/` - Custom plugins
- `configs/` - Configuration files
- `logs/` - Log files
- `tests/` - Test files

## Solana DEX Integration

This project supports:
- **Jupiter**: DEX aggregator for optimal routing
- **Raydium**: Automated Market Maker (AMM)
- **Orca**: Concentrated liquidity DEX
- **Serum**: Order book DEX

## Safety

- Always test on devnet first
- Use small amounts for initial testing
- Enable dry_run mode in production
- Monitor transaction fees and slippage
"""

        with open(f"{name}/README.md", 'w') as f:
            f.write(readme_content)
        
        click.echo(f"✅ Solana project '{name}' created successfully!")
        click.echo(f"📁 Project structure:")
        click.echo(f"   • {name}/")
        click.echo(f"     ├── agents/           # Agent configurations")
        click.echo(f"     ├── strategies/       # Trading strategies") 
        click.echo(f"     ├── plugins/          # Custom plugins")
        click.echo(f"     ├── configs/          # Configuration files")
        click.echo(f"     ├── logs/             # Log files")
        click.echo(f"     ├── tests/            # Test files")
        click.echo(f"     ├── solana_swarm.yaml # Main configuration")
        click.echo(f"     ├── .env.example      # Environment template")
        click.echo(f"     ├── requirements.txt  # Dependencies")
        click.echo(f"     └── README.md         # Documentation")
        click.echo(f"\n🚀 Next steps:")
        click.echo(f"   1. cd {name}")
        click.echo(f"   2. python -m venv venv")
        click.echo(f"   3. source venv/bin/activate  # or venv\\Scripts\\activate on Windows")
        click.echo(f"   4. pip install -r requirements.txt")
        click.echo(f"   5. cp .env.example .env")
        click.echo(f"   6. Edit .env with your API keys")
        click.echo(f"   7. solana-swarm chat --tutorial create-first-agent")
        
    except Exception as e:
        click.echo(f"❌ Error creating Solana project: {str(e)}", err=True)