#!/usr/bin/env python3
"""
Workshop Verification Script
Verifies that all components are working for the Solana AI Workshop
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv


# Add project root to path
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()
load_dotenv()

async def verify_imports():
    """Verify all core imports work."""
    checks = []
    
    try:
        from solana_swarm.core.agent import AgentConfig
        checks.append(("Core Agent", "✅", "Import successful"))
    except Exception as e:
        checks.append(("Core Agent", "❌", str(e)))
    
    try:
        from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
        checks.append(("Swarm Agent", "✅", "Import successful"))
    except Exception as e:
        checks.append(("Swarm Agent", "❌", str(e)))
    
    try:
        from solana_swarm.core.market_data import MarketDataManager
        checks.append(("Market Data", "✅", "Import successful"))
    except Exception as e:
        checks.append(("Market Data", "❌", str(e)))
    
    try:
        from solana_swarm.plugins.loader import PluginLoader
        checks.append(("Plugin Loader", "✅", "Import successful"))
    except Exception as e:
        checks.append(("Plugin Loader", "❌", str(e)))
    
    try:
        from solana_swarm.core.llm_provider import LLMConfig, create_llm_provider
        checks.append(("LLM Provider", "✅", "Import successful"))
    except Exception as e:
        checks.append(("LLM Provider", "❌", str(e)))
    
    return checks

async def verify_agents():
    """Verify agent plugins can be loaded."""
    checks = []
    
    try:
        from solana_swarm.agents.price_monitor.plugin import PriceMonitorPlugin
        checks.append(("Price Monitor", "✅", "Plugin available"))
    except Exception as e:
        checks.append(("Price Monitor", "❌", str(e)))
    
    try:
        from solana_swarm.agents.decision_maker.plugin import DecisionMakerPlugin
        checks.append(("Decision Maker", "✅", "Plugin available"))
    except Exception as e:
        checks.append(("Decision Maker", "❌", str(e)))
    
    try:
        from solana_swarm.agents.portfolio_manager.plugin import PortfolioManagerPlugin
        checks.append(("Portfolio Manager", "✅", "Plugin available"))
    except Exception as e:
        checks.append(("Portfolio Manager", "❌", str(e)))
    
    return checks

async def verify_configuration():
    """Verify configuration files and environment."""
    checks = []
    
    # Check environment file
    if os.path.exists('.env'):
        checks.append(("Environment File", "✅", ".env exists"))
    else:
        checks.append(("Environment File", "❌", ".env not found"))
    
    # Check required environment variables
    required_vars = ['LLM_PROVIDER', 'LLM_API_KEY', 'SOLANA_NETWORK']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            checks.append((f"ENV: {var}", "✅", "Set"))
        else:
            checks.append((f"ENV: {var}", "❌", "Not set"))
    
    # Check agent configurations
    agent_configs = [
        'agents/price-monitor.yaml',
        'agents/decision-maker.yaml',
        'agents/portfolio-manager.yaml'
    ]
    
    for config_path in agent_configs:
        if os.path.exists(config_path):
            checks.append((f"Config: {os.path.basename(config_path)}", "✅", "Found"))
        else:
            checks.append((f"Config: {os.path.basename(config_path)}", "❌", "Missing"))
    
    return checks

async def verify_functionality():
    """Test basic functionality."""
    checks = []
    
    try:
        # Test SwarmAgent creation
        from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
        config = SwarmConfig(role="test_agent")
        agent = SwarmAgent(config)
        await agent.initialize()
        await agent.cleanup()
        checks.append(("SwarmAgent Creation", "✅", "Can create and initialize"))
    except Exception as e:
        checks.append(("SwarmAgent Creation", "❌", str(e)))
    
    try:
        # Test PluginLoader
        from solana_swarm.plugins.loader import PluginLoader
        loader = PluginLoader()
        # Just test instantiation
        await loader.cleanup()
        checks.append(("Plugin Loader", "✅", "Can instantiate"))
    except Exception as e:
        checks.append(("Plugin Loader", "❌", str(e)))
    
    try:
        # Test MarketDataManager
        from solana_swarm.core.market_data import MarketDataManager
        market_data = MarketDataManager()
        await market_data.close()  # Just test creation/cleanup
        checks.append(("Market Data Manager", "✅", "Can instantiate"))
    except Exception as e:
        checks.append(("Market Data Manager", "❌", str(e)))
    
    return checks

async def main():
    """Run all verification checks."""
    console.print("🔍 [cyan]Solana Swarm Workshop Verification[/cyan]")
    console.print("=" * 50)
    
    # Run all verification checks
    import_checks = await verify_imports()
    agent_checks = await verify_agents()
    config_checks = await verify_configuration()
    func_checks = await verify_functionality()
    
    all_checks = [
        ("Core Imports", import_checks),
        ("Agent Plugins", agent_checks), 
        ("Configuration", config_checks),
        ("Functionality", func_checks)
    ]
    
    # Display results
    for section_name, checks in all_checks:
        table = Table(title=section_name)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details", style="dim")
        
        for component, status, details in checks:
            table.add_row(component, status, details)
        
        console.print(table)
        console.print()
    
    # Summary
    total_checks = sum(len(checks) for _, checks in all_checks)
    passed_checks = sum(
        1 for _, checks in all_checks 
        for _, status, _ in checks 
        if status == "✅"
    )
    
    if passed_checks == total_checks:
        rprint(f"🎉 [green]All checks passed! ({passed_checks}/{total_checks})[/green]")
        rprint("✅ [green]Workshop environment is ready![/green]")
        return 0
    else:
        rprint(f"⚠️ [yellow]{passed_checks}/{total_checks} checks passed[/yellow]")
        rprint("❌ [red]Some issues need to be resolved[/red]")
        return 1

if __name__ == "__main__":
    import sys
    result = asyncio.run(main())
    sys.exit(result)