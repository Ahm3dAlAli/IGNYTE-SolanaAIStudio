"""
Solana Swarm CLI
Main entry point for the command line interface
"""

import click
import asyncio
from .plugins import plugins
from .create import create
from .config import config
from ..plugins import PluginLoader
from ..core.market_data import MarketDataManager
from ..core.solana_integration import SolanaConnection, SolanaConfig
import os
import yaml
import time

@click.group()
def cli():
    """Solana Swarm Intelligence CLI"""
    pass

@cli.command()
@click.argument('plugin_name')
@click.option('--operation', '-o', help='Operation to execute')
@click.option('--config', '-c', help='Path to plugin configuration file')
def execute(plugin_name: str, operation: str = None, config: str = None):
    """Execute a plugin or strategy"""
    try:
        async def run_plugin():
            # Initialize plugin loader
            loader = PluginLoader()
            
            # Load and validate plugin
            plugin = await loader.load_plugin(plugin_name)
            if not plugin:
                click.echo(f"Plugin {plugin_name} not found")
                return
                
            # Load configuration if provided
            if config:
                plugin.load_config(config)
                
            # Execute plugin
            click.echo(f"Executing plugin: {plugin_name}")
            if operation:
                click.echo(f"Operation: {operation}")
                await plugin.execute(operation=operation)
            else:
                await plugin.execute()
            click.echo("Execution completed")
            
            # Cleanup
            await loader.cleanup()
            
        asyncio.run(run_plugin())
        
    except Exception as e:
        click.echo(f"Error executing plugin: {str(e)}", err=True)

@cli.command()
@click.option('--tutorial', type=str, help='Start a guided tutorial (e.g., create-first-agent)')
def chat(tutorial: str = None):
    """Start interactive chat assistant"""
    from .chat import start_chat
    start_chat(tutorial_mode=tutorial)

@cli.command()
@click.argument('agents', nargs=-1, required=True)
@click.option('--timeout', default=60, help='Timeout in seconds')
@click.option('--network', default='devnet', help='Solana network (devnet/testnet/mainnet-beta)')
def run(agents, timeout, network):
    """Run multiple agents together on Solana"""
    try:
        if not agents:
            click.echo("Please specify at least one agent to run")
            return
            
        click.echo(f"Starting Solana agents on {network}: {', '.join(agents)}")
        
        async def run_agents():
            loader = PluginLoader()
            market_data = MarketDataManager()
            loaded_agents = []
            
            # Solana-specific search paths
            def get_config_paths(agent):
                return [
                    f"solana_swarm/agents/{agent}/agent.yaml",
                    f"agents/{agent}/agent.yaml",
                    f"solana_swarm/examples/{agent}.yaml",
                    f"plugins/{agent}/agent.yaml",
                    f"{agent}/agent.yaml",
                    f"agent.yaml"
                ]
            
            # Load and validate each agent
            for agent in agents:
                config_paths = get_config_paths(agent)
                config_file = None
                
                # Find first existing config file
                for path in config_paths:
                    if os.path.exists(path):
                        config_file = path
                        break
                
                if not config_file:
                    click.echo(f"❌ Agent not found: {agent}")
                    click.echo("Looked in:")
                    for path in config_paths:
                        click.echo(f"- {path}")
                    return
                    
                # Load and validate config
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    
                    # Validate required fields
                    if not config:
                        click.echo(f"❌ Invalid configuration for agent: {agent}")
                        return
                        
                    # Validate role field
                    if 'role' not in config:
                        click.echo(f"❌ Missing required 'role' field in configuration for agent: {agent}")
                        click.echo("Please specify a role (e.g., market_analyzer, strategy_optimizer)")
                        return
                    
                    # Validate role value for Solana
                    valid_roles = ['market_analyzer', 'strategy_optimizer', 'arbitrage_agent', 
                                 'yield_farmer', 'portfolio_manager', 'defi_monitor']
                    if config['role'] not in valid_roles:
                        click.echo(f"❌ Invalid role '{config['role']}' for agent: {agent}")
                        click.echo(f"Valid Solana roles: {', '.join(valid_roles)}")
                        return
                
                # Load agent plugin
                plugin = await loader.load_plugin(agent)
                if not plugin:
                    click.echo(f"❌ Failed to load agent: {agent}")
                    return
                    
                loaded_agents.append(plugin)
                click.echo(f"✅ Loaded Solana agent: {agent} (role: {config['role']})")
            
            click.echo(f"\n🤖 Solana agents running on {network}:")
            
            # Initialize Solana connection
            solana_config = SolanaConfig(
                network=network,
                wallet_path=os.getenv('SOLANA_WALLET_PATH', '~/.config/solana/id.json')
            )
            
            try:
                async with SolanaConnection(solana_config) as solana:
                    wallet_balance = await solana.get_balance()
                    network_stats = await solana.get_network_stats()
                    
                    click.echo(f"💰 Wallet Balance: {wallet_balance:.4f} SOL")
                    click.echo(f"🌐 Network TPS: {network_stats.get('tps', 0):,.0f}")
                    
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        # Get current SOL market data
                        sol_data = await market_data.get_token_price('sol')
                        sol_price = sol_data['price']
                        click.echo(f"\n📊 Current SOL Price: ${sol_price:.2f}")
                        
                        # Market analyzer agent
                        if loaded_agents[0].role == "market_analyzer":
                            click.echo("\n🔍 Solana Market Analyzer processing...")
                            
                            analysis = await loaded_agents[0].evaluate({
                                "price": sol_price,
                                "network": network,
                                "timestamp": time.time(),
                                "dex_data": {
                                    "jupiter_volume": 5000000,
                                    "raydium_tvl": 150000000,
                                    "orca_pools": 250
                                },
                                "request": """Analyze current Solana DeFi market conditions:
                                1. Evaluate SOL price action and DEX liquidity
                                2. Assess Jupiter, Raydium, and Orca market conditions
                                3. Consider network performance and transaction costs
                                4. Provide Solana-specific trading recommendations
                                
                                Focus on DEX arbitrage opportunities and DeFi yield prospects."""
                            })
                            
                            if analysis and 'error' not in analysis:
                                click.echo(f"\n📝 Solana Market Analysis:")
                                click.echo(f"  • Market Observation: {analysis.get('observation', 'Analyzing Solana markets...')}")
                                click.echo(f"  • DEX Analysis: {analysis.get('reasoning', 'Evaluating DEX conditions...')}")
                                click.echo(f"  • Recommendation: {analysis.get('conclusion', 'Strategy complete')}")
                                click.echo(f"  • Confidence: {analysis.get('confidence', 0):.0%}")
                                click.echo(f"  • Risk Assessment: {analysis.get('risk_level', 'medium').title()}")
                                
                                # Strategy optimizer agent
                                if len(loaded_agents) > 1 and loaded_agents[1].role == "strategy_optimizer":
                                    click.echo("\n🎯 Solana Strategy Optimizer evaluating...")
                                    
                                    decision = await loaded_agents[1].evaluate({
                                        "market_analysis": analysis,
                                        "current_price": sol_price,
                                        "network": network,
                                        "wallet_balance": wallet_balance,
                                        "request": """Optimize Solana DeFi strategy based on market analysis:
                                        1. Evaluate DEX routing efficiency (Jupiter vs direct DEX)
                                        2. Consider transaction costs and MEV protection
                                        3. Assess yield farming opportunities on Raydium/Orca
                                        4. Recommend specific Solana protocol interactions
                                        
                                        Provide actionable Solana DeFi strategy with risk management."""
                                    })
                                    
                                    if decision and 'error' not in decision:
                                        click.echo(f"\n📋 Solana Strategy Decision:")
                                        click.echo(f"  • Strategy Context: {decision.get('observation', 'Analyzing opportunities...')}")
                                        click.echo(f"  • Optimization Logic: {decision.get('reasoning', 'Evaluating strategies...')}")
                                        click.echo(f"  • Recommended Action: {decision.get('conclusion', 'Strategy finalized')}")
                                        click.echo(f"  • Execution Confidence: {decision.get('confidence', 0):.0%}")
                                        click.echo(f"  • Preferred Protocol: {decision.get('preferred_dex', 'jupiter').title()}")
                                        
                                        if decision.get("confidence", 0) > 0.8:
                                            click.echo(f"\n✨ High Confidence Solana Strategy:")
                                            click.echo(f"  {decision.get('conclusion', 'Execute optimized strategy')}")
                                            
                                            # Execute the decision on Solana
                                            execution_result = await loaded_agents[1].execute({
                                                'type': 'solana_defi_strategy',
                                                'data': {
                                                    'market_analysis': analysis,
                                                    'current_price': sol_price,
                                                    'network': network,
                                                    'wallet_balance': wallet_balance
                                                }
                                            })
                                            
                                            # Show Solana transaction details
                                            if execution_result and 'transaction' in execution_result:
                                                tx = execution_result['transaction']
                                                if tx.get('status') == 'success':
                                                    click.echo(f"\n🔄 Solana Transaction Executed:")
                                                    click.echo(f"  • Protocol: {tx.get('protocol', 'Jupiter')}")
                                                    click.echo(f"  • Amount: {tx.get('amount', 0.1)} SOL")
                                                    click.echo(f"  • Signature: {tx.get('signature', 'demo_sig')}")
                                                    click.echo(f"  • Explorer: https://explorer.solana.com/tx/{tx.get('signature', 'demo')}?cluster={network}")
                                                    click.echo(f"  • Network: {network.title()}")
                                                else:
                                                    click.echo(f"\n❌ Solana Transaction Failed: {tx.get('error', 'Unknown error')}")
                        
                        click.echo(f"\n⏳ Next Solana market scan in 60 seconds...")
                        await asyncio.sleep(60)
                        
            except KeyboardInterrupt:
                click.echo("\n👋 Stopping Solana agents gracefully...")
            finally:
                # Cleanup
                for agent in loaded_agents:
                    await agent.cleanup()
                await loader.cleanup()
                await market_data.close()
                
        asyncio.run(run_agents())
        
    except Exception as e:
        click.echo(f"❌ Error running Solana agents: {str(e)}")

@cli.command()
@click.option('--network', default='devnet', help='Solana network to validate against')
def validate(network):
    """Validate Solana agent configurations"""
    try:
        click.echo(f"🔍 Validating Solana configurations for {network}...")
        
        # Use same config path resolution as run command
        def find_agent_configs():
            configs = []
            search_dirs = [
                "solana_swarm/agents",
                "agents",
                "solana_swarm/examples",
                "plugins",
                "."
            ]
            
            for directory in search_dirs:
                if os.path.exists(directory):
                    # Check for agent.yaml in directory
                    if os.path.exists(os.path.join(directory, "agent.yaml")):
                        configs.append(os.path.join(directory, "agent.yaml"))
                    
                    # Check subdirectories
                    if os.path.isdir(directory):
                        for subdir in os.listdir(directory):
                            config_path = os.path.join(directory, subdir, "agent.yaml")
                            if os.path.exists(config_path):
                                configs.append(config_path)
            
            return configs
        
        configs = find_agent_configs()
        if not configs:
            click.echo("❌ No Solana agent configurations found")
            return
        
        for config_path in configs:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
                # Validate configuration
                if not config:
                    click.echo(f"❌ Invalid configuration in {config_path}")
                    continue
                
                # Check required fields
                required_fields = ['name', 'role']
                missing_fields = [field for field in required_fields if field not in config]
                if missing_fields:
                    click.echo(f"❌ Missing required fields in {config_path}: {', '.join(missing_fields)}")
                    continue
                
                # Validate Solana-specific roles
                valid_solana_roles = [
                    'market_analyzer', 'strategy_optimizer', 'arbitrage_agent',
                    'yield_farmer', 'portfolio_manager', 'defi_monitor'
                ]
                if config['role'] not in valid_solana_roles:
                    click.echo(f"❌ Invalid Solana role '{config['role']}' in {config_path}")
                    click.echo(f"Valid roles: {', '.join(valid_solana_roles)}")
                    continue
                
                # Check Solana-specific settings
                if 'custom_settings' in config:
                    settings = config['custom_settings']
                    if 'preferred_dexes' in settings:
                        valid_dexes = ['jupiter', 'raydium', 'orca', 'serum']
                        invalid_dexes = [dex for dex in settings['preferred_dexes'] if dex not in valid_dexes]
                        if invalid_dexes:
                            click.echo(f"⚠️  Invalid DEXes in {config_path}: {invalid_dexes}")
                
                click.echo(f"✅ Valid Solana configuration: {config_path} (role: {config['role']})")
        
    except Exception as e:
        click.echo(f"❌ Error validating Solana configurations: {str(e)}")

@cli.command()
@click.option('--network', default='devnet', help='Solana network (devnet/testnet/mainnet-beta)')
def wallet(network):
    """Show Solana wallet information"""
    try:
        async def show_wallet_info():
            click.echo(f"💰 Solana Wallet Information ({network})")
            click.echo("=" * 40)
            
            try:
                solana_config = SolanaConfig(
                    network=network,
                    wallet_path=os.getenv('SOLANA_WALLET_PATH', '~/.config/solana/id.json')
                )
                
                async with SolanaConnection(solana_config) as connection:
                    # Get wallet address
                    wallet_address = str(connection.public_key)
                    click.echo(f"Address: {wallet_address}")
                    
                    # Get balance
                    balance = await connection.get_balance()
                    click.echo(f"Balance: {balance:.4f} SOL")
                    
                    # Get network stats
                    network_stats = await connection.get_network_stats()
                    click.echo(f"Network: {network}")
                    click.echo(f"Current TPS: {network_stats.get('tps', 0):,.0f}")
                    click.echo(f"Current Slot: {network_stats.get('current_slot', 0):,}")
                    
                    # Show explorer link
                    explorer_url = f"https://explorer.solana.com/address/{wallet_address}?cluster={network}"
                    click.echo(f"Explorer: {explorer_url}")
                    
            except Exception as e:
                click.echo(f"❌ Error getting wallet info: {str(e)}")
                click.echo("\nTroubleshooting:")
                click.echo("1. Check SOLANA_WALLET_PATH environment variable")
                click.echo("2. Ensure wallet keypair file exists")
                click.echo("3. Verify network is accessible")
        
        asyncio.run(show_wallet_info())
        
    except Exception as e:
        click.echo(f"❌ Wallet command failed: {str(e)}")

@cli.command()
@click.argument('token', default='sol')
@click.option('--dex', help='Specific DEX to query (jupiter/raydium/orca)')
def price(token, dex):
    """Get current token price on Solana DEXs"""
    try:
        async def get_price():
            click.echo(f"📊 Getting {token.upper()} price from Solana DEXs...")
            
            async with MarketDataManager() as market:
                try:
                    price_data = await market.get_token_price(token.lower())
                    
                    click.echo(f"\n💰 {token.upper()} Price Information:")
                    click.echo(f"  Current Price: ${price_data['price']:.4f}")
                    
                    if 'price_change_24h' in price_data:
                        change = price_data['price_change_24h']
                        color = 'green' if change >= 0 else 'red'
                        click.echo(click.style(f"  24h Change: {change:+.2f}%", fg=color))
                    
                    click.echo(f"  Data Source: {price_data.get('source', 'unknown').title()}")
                    
                    # If specific DEX requested, try to get DEX-specific data
                    if dex:
                        try:
                            dex_data = await market.get_dex_data(dex.lower())
                            click.echo(f"\n🏪 {dex.title()} DEX Information:")
                            click.echo(f"  TVL: ${dex_data.tvl:,.0f}")
                            click.echo(f"  24h Volume: ${dex_data.volume_24h:,.0f}")
                        except Exception as e:
                            click.echo(f"⚠️  Could not get {dex} specific data: {str(e)}")
                    
                except Exception as e:
                    click.echo(f"❌ Error getting {token} price: {str(e)}")
        
        asyncio.run(get_price())
        
    except Exception as e:
        click.echo(f"❌ Price command failed: {str(e)}")

@cli.command()
@click.option('--network', default='devnet', help='Solana network')
def status(network):
    """Show Solana network and system status"""
    try:
        async def show_status():
            click.echo(f"🌐 Solana System Status ({network})")
            click.echo("=" * 40)
            
            # Network status
            try:
                solana_config = SolanaConfig(
                    network=network,
                    wallet_path=os.getenv('SOLANA_WALLET_PATH', '~/.config/solana/id.json')
                )
                
                async with SolanaConnection(solana_config) as connection:
                    stats = await connection.get_network_stats()
                    
                    click.echo("📡 Network Status:")
                    click.echo(f"  • TPS: {stats.get('tps', 0):,.0f}")
                    click.echo(f"  • Slot: {stats.get('current_slot', 0):,}")
                    click.echo(f"  • Epoch: {stats.get('current_epoch', 0)}")
                    click.echo(f"  • Supply: {stats.get('total_supply', 0):,.0f} SOL")
                    
            except Exception as e:
                click.echo(f"❌ Network status error: {str(e)}")
            
            # Market status
            try:
                async with MarketDataManager() as market:
                    sol_data = await market.get_token_price('sol')
                    
                    click.echo("\n💹 Market Status:")
                    click.echo(f"  • SOL Price: ${sol_data['price']:.2f}")
                    if 'price_change_24h' in sol_data:
                        change = sol_data['price_change_24h']
                        color = 'green' if change >= 0 else 'red'
                        click.echo(click.style(f"  • 24h Change: {change:+.2f}%", fg=color))
                    
            except Exception as e:
                click.echo(f"❌ Market status error: {str(e)}")
            
            # Plugin status
            try:
                loader = PluginLoader()
                plugins = await loader.load_all_plugins()
                
                click.echo(f"\n🔌 Plugin Status:")
                click.echo(f"  • Available: {len(plugins)}")
                for name, plugin in plugins.items():
                    role = getattr(plugin, 'role', 'unknown')
                    click.echo(f"  • {name}: {role}")
                
                await loader.cleanup()
                
            except Exception as e:
                click.echo(f"❌ Plugin status error: {str(e)}")
        
        asyncio.run(show_status())
        
    except Exception as e:
        click.echo(f"❌ Status command failed: {str(e)}")

# Register commands
cli.add_command(plugins)
cli.add_command(create)
cli.add_command(config)
cli.add_command(run)
cli.add_command(validate)
cli.add_command(wallet)
cli.add_command(price)
cli.add_command(status)

if __name__ == '__main__':
    cli()