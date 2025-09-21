"""
Create new agents and strategies for Solana Swarm
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from rich import print as rprint
from rich.prompt import Prompt, Confirm

async def create_item(item_type: str, name: str, template: Optional[str] = None):
    """Create new agent or strategy."""
    
    if item_type == "agent":
        await create_agent(name, template)
    elif item_type == "strategy":
        await create_strategy(name, template)
    else:
        rprint(f"❌ [red]Unknown type: {item_type}[/red]")
        rprint("Available types: agent, strategy")

async def create_agent(name: str, template: Optional[str] = None):
    """Create a new agent."""
    
    # Validate name
    if not name.isidentifier():
        rprint(f"❌ [red]Invalid agent name: {name}[/red]")
        rprint("Agent name must be a valid Python identifier")
        return
    
    # Check if agent already exists
    agent_dir = Path(f"solana_swarm/agents/{name}")
    if agent_dir.exists():
        if not Confirm.ask(f"Agent '{name}' already exists. Overwrite?"):
            return
    
    # Create agent directory
    agent_dir.mkdir(parents=True, exist_ok=True)
    
    # Get agent details
    role = Prompt.ask("Agent role", default="custom_analyzer")
    description = Prompt.ask("Agent description", default=f"Custom {name} agent")
    capabilities = Prompt.ask("Capabilities (comma-separated)", default="analysis,monitoring").split(",")
    capabilities = [cap.strip() for cap in capabilities]
    
    # Create agent.yaml
    agent_config = f"""name: {name}
role: {role}
description: "{description}"
version: "0.1.0"
environment: development
log_level: INFO

# LLM Configuration
llm:
  provider: ${{LLM_PROVIDER}}
  api_key: ${{LLM_API_KEY}}
  model: ${{LLM_MODEL}}
  temperature: 0.7
  max_tokens: 1500
  api_url: ${{LLM_API_URL}}
  system_prompt: |
    You are a specialized {role} agent for Solana DeFi operations.
    Your role is to {description.lower()}.
    
    Focus on:
    1. Solana ecosystem analysis
    2. DEX and DeFi protocols
    3. Risk assessment and management
    4. Clear reasoning and confidence levels
    
    Always provide detailed analysis with confidence scores.

# Agent capabilities  
capabilities:
{chr(10).join(f'  - {cap}' for cap in capabilities)}

# Custom settings
custom_settings:
  min_confidence_threshold: 0.7
  max_retries: 3
  timeout: 30
"""
    
    with open(agent_dir / "agent.yaml", "w") as f:
        f.write(agent_config)
    
    # Create plugin.py
    plugin_code = f'''"""
{name.title()} Plugin for Solana Swarm Intelligence
{description}
"""

import logging
from typing import Dict, Any, Optional
from solana_swarm.plugins.base import AgentPlugin, PluginConfig
from solana_swarm.core.agent import AgentConfig

logger = logging.getLogger(__name__)

class {name.title().replace("_", "")}Plugin(AgentPlugin):
    """Custom {name} plugin for Solana operations"""
    
    def __init__(self, agent_config: AgentConfig, plugin_config: PluginConfig):
        super().__init__(agent_config, plugin_config)
        self.min_confidence = float(self.plugin_config.custom_settings.get('min_confidence_threshold', 0.7))
        self.max_retries = int(self.plugin_config.custom_settings.get('max_retries', 3))
        self.timeout = int(self.plugin_config.custom_settings.get('timeout', 30))
        self.logger = logger
        
    async def initialize(self) -> None:
        """Initialize {name} agent"""
        self.logger.info("Solana {name} agent initialized successfully")
        
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate context using {name} logic"""
        try:
            # Extract context information
            query = context.get('query', '')
            market_context = context.get('market_context', {{}})
            
            # Implement your custom logic here
            observation = f"I am analyzing the request: {{query}}"
            
            reasoning = f"Based on my role as a {{self.plugin_config.role}}, I assess the current situation. "
            reasoning += "This is where you would implement your specific analysis logic."
            
            conclusion = "This is a template response. Implement your specific logic here."
            
            return {{
                'observation': observation,
                'reasoning': reasoning,
                'conclusion': conclusion,
                'confidence': 0.8,
                'agent': '{name}',
                'role': self.plugin_config.role
            }}
            
        except Exception as e:
            self.logger.error(f"Error in {name} evaluation: {{str(e)}}")
            return {{'error': str(e)}}
            
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actions for {name} agent"""
        try:
            action_type = action.get('type', 'unknown')
            
            if action_type == 'analyze':
                # Implement analysis action
                return {{'status': 'success', 'result': 'Analysis completed'}}
            else:
                return {{'error': f'Unsupported action type: {{action_type}}'}}
                
        except Exception as e:
            self.logger.error(f"Error executing action: {{str(e)}}")
            return {{'error': str(e)}}
            
    async def cleanup(self) -> None:
        """Cleanup {name} agent resources"""
        self.logger.info("{name.title()} agent cleanup completed")
'''
    
    with open(agent_dir / "plugin.py", "w") as f:
        f.write(plugin_code)
    
    # Create __init__.py
    with open(agent_dir / "__init__.py", "w") as f:
        f.write(f'"""{name.title()} agent for Solana Swarm Intelligence"""\n')
    
    # Create test file
    test_dir = Path(f"tests/agents")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_code = f'''"""
Tests for {name} agent
"""

import pytest
from unittest.mock import AsyncMock, patch

from solana_swarm.agents.{name}.plugin import {name.title().replace("_", "")}Plugin
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
        role="{role}",
        capabilities={capabilities},
        custom_settings={{"min_confidence_threshold": 0.7}}
    )


@pytest.fixture
async def {name}_plugin(agent_config, plugin_config):
    """Create {name} plugin for testing."""
    plugin = {name.title().replace("_", "")}Plugin(agent_config, plugin_config)
    await plugin.initialize()
    return plugin


@pytest.mark.asyncio
async def test_{name}_initialization({name}_plugin):
    """Test {name} plugin initialization."""
    assert {name}_plugin.min_confidence == 0.7
    assert {name}_plugin.plugin_config.role == "{role}"


@pytest.mark.asyncio
async def test_{name}_evaluation({name}_plugin):
    """Test {name} evaluation functionality."""
    context = {{
        "query": "test query",
        "market_context": {{"test": "data"}}
    }}
    
    result = await {name}_plugin.evaluate(context)
    
    assert "error" not in result
    assert "observation" in result
    assert "reasoning" in result
    assert "confidence" in result
    assert result["confidence"] >= 0.0


@pytest.mark.asyncio
async def test_{name}_execute({name}_plugin):
    """Test {name} execution functionality."""
    action = {{"type": "analyze", "params": {{"test": "data"}}}}
    
    result = await {name}_plugin.execute(action)
    
    assert "status" in result or "error" in result


@pytest.mark.asyncio  
async def test_{name}_error_handling({name}_plugin):
    """Test {name} error handling."""
    # Test with invalid context
    result = await {name}_plugin.evaluate({{}})
    
    # Should handle gracefully
    assert isinstance(result, dict)
'''
    
    with open(test_dir / f"test_{name}.py", "w") as f:
        f.write(test_code)
    
    rprint(f"✅ [green]Agent '{name}' created successfully![/green]")
    rprint(f"📁 Files created:")
    rprint(f"   • solana_swarm/agents/{name}/agent.yaml")
    rprint(f"   • solana_swarm/agents/{name}/plugin.py")
    rprint(f"   • tests/agents/test_{name}.py")
    rprint(f"\n🔧 Next steps:")
    rprint(f"   1. Implement your custom logic in plugin.py")
    rprint(f"   2. Update the system prompt in agent.yaml")
    rprint(f"   3. Run tests: pytest tests/agents/test_{name}.py")
    rprint(f"   4. Test with: solana-swarm chat --agent {name}")

async def create_strategy(name: str, template: Optional[str] = None):
    """Create a new strategy."""
    
    # Validate name
    if not name.replace("_", "").replace("-", "").isalnum():
        rprint(f"❌ [red]Invalid strategy name: {name}[/red]")
        return
    
    # Check if strategy already exists
    strategy_file = Path(f"strategies/{name}.py")
    strategy_file.parent.mkdir(exist_ok=True)
    
    if strategy_file.exists():
        if not Confirm.ask(f"Strategy '{name}' already exists. Overwrite?"):
            return
    
    # Get strategy details
    description = Prompt.ask("Strategy description", default=f"Custom {name} strategy")
    target_agents = Prompt.ask("Target agents (comma-separated)", default="price-monitor,decision-maker").split(",")
    target_agents = [agent.strip() for agent in target_agents]
    
    # Create strategy file
    strategy_code = f'''
"""
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

logger = logging.getLogger(__name__)

class {name.title().replace("_", "")}Strategy:
    """
    {description}
    
    This strategy coordinates multiple agents to:
    1. Analyze market conditions
    2. Assess risks and opportunities
    3. Make informed trading decisions
    4. Execute trades safely
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize {name} strategy."""
        self.config = config or self.get_default_config()
        self.agents = {{}}
        self.market_data = None
        self.is_running = False
        
    def get_default_config(self) -> Dict[str, Any]:
        """Get default strategy configuration."""
        return {{
            "name": "{name}",
            "description": "{description}",
            "target_agents": {target_agents},
            "min_confidence": 0.8,
            "max_position_size": 1000,  # USD
            "stop_loss": 0.05,  # 5%
            "take_profit": 0.10,  # 10%
            "update_interval": 300,  # 5 minutes
            "dry_run": True  # Safety first!
        }}
    
    async def initialize(self):
        """Initialize strategy and load agents."""
        try:
            logger.info(f"Initializing {{self.config['name']}} strategy")
            
            # Initialize market data
            self.market_data = MarketDataManager()
            
            # Load required agents
            loader = PluginLoader()
            for agent_name in self.config["target_agents"]:
                try:
                    agent = await loader.load_plugin(agent_name)
                    self.agents[agent_name] = agent
                    logger.info(f"Loaded agent: {{agent_name}}")
                except Exception as e:
                    logger.error(f"Failed to load agent {{agent_name}}: {{e}}")
            
            if not self.agents:
                raise ValueError("No agents loaded successfully")
            
            self.is_running = True
            logger.info("Strategy initialized successfully")
            
        except Exception as e:
            logger.error(f"Strategy initialization failed: {{e}}")
            raise
    
    async def analyze_opportunity(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trading opportunity using multiple agents."""
        try:
            # Get market context
            market_context = await self.market_data.get_market_context()
            
            # Combine contexts
            full_context = {{
                **context,
                "market_context": market_context,
                "strategy": self.config["name"],
                "timestamp": datetime.now().isoformat()
            }}
            
            # Collect agent evaluations
            agent_results = {{}}
            for agent_name, agent in self.agents.items, dep):
                raise ValueError(f"Invalid dependency name: {dep}")
        return v

# Validation functions
def validate_agent_config(config: Dict[str, Any]) -> AgentConfigSchema:
    """Validate agent configuration against schema."""
    return AgentConfigSchema(**config)

def validate_swarm_config(config: Dict[str, Any]) -> SwarmConfigSchema:
    """Validate swarm configuration against schema."""
    return SwarmConfigSchema(**config)

def validate_strategy_config(config: Dict[str, Any]) -> StrategyConfigSchema:
    """Validate strategy configuration against schema."""
    return StrategyConfigSchema(**config)

def validate_plugin_config(config: Dict[str, Any]) -> PluginConfigSchema:
    """Validate plugin configuration against schema."""
    return PluginConfigSchema(**config) '''