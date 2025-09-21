"""
Main CLI interface for Solana Swarm Intelligence Framework
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from solana_swarm.core.agent import AgentConfig
from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
from solana_swarm.plugins.loader import PluginLoader
from solana_swarm.core.market_data import MarketDataManager
from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig

app = typer.Typer(
    name="solana-swarm",
    help="Solana Swarm Intelligence Framework CLI",
    add_completion=False
)
console = Console()

@app.command()
def init(
    name: str = typer.Argument(..., help="Project name"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project path")
):
    """Initialize a new Solana Swarm project."""
    project_path = Path(path) if path else Path.cwd() / name
    
    try:
        # Create project structure
        project_path.mkdir(exist_ok=True)
        (project_path / "agents").mkdir(exist_ok=True)
        (project_path / "strategies").mkdir(exist_ok=True)
        (project_path / "logs").mkdir(exist_ok=True)
        
        # Create .env file
        env_content = """# Solana Swarm Configuration
LLM_PROVIDER=openrouter
LLM_API_KEY=your_openrouter_api_key_here
LLM_MODEL=anthropic/claude-3.5-sonnet
SOLANA_NETWORK=devnet
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_WALLET_PATH=~/.config/solana/id.json
"""
        (project_path / ".env").write_text(env_content)
        
        # Create sample configuration
        config_content = """# Solana Swarm Project Configuration
name: {name}
version: "0.1.0"
environment: development

agents:
  - name: price-monitor
    role: market_analyzer
    enabled: true
  - name: decision-maker
    role: strategy_optimizer
    enabled: true

strategies:
  - name: basic-arbitrage
    agents: [price-monitor, decision-maker]
    enabled: false
""".format(name=name)
        (project_path / "swarm.yaml").write_text(config_content)
        
        rprint(f"✅ [green]Project '{name}' initialized successfully![/green]")
        rprint(f"📁 Project path: {project_path}")
        rprint(f"🔧 Next steps:")
        rprint(f"   1. cd {project_path}")
        rprint(f"   2. Edit .env with your API keys")
        rprint(f"   3. Run: solana-swarm verify")
        
    except Exception as e:
        rprint(f"❌ [red]Error initializing project: {e}[/red]")
        sys.exit(1)

@app.command()
def verify():
    """Verify system setup and configuration."""
    console.print("🔍 Verifying Solana Swarm setup...\n")
    
    async def run_verification():
        checks = []
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 8):
            checks.append(("Python Version", "✅", f"Python {python_version.major}.{python_version.minor}"))
        else:
            checks.append(("Python Version", "❌", f"Python {python_version.major}.{python_version.minor} (3.8+ required)"))
        
        # Check environment variables
        env_vars = ["LLM_API_KEY", "SOLANA_NETWORK"]
        for var in env_vars:
            value = os.getenv(var)
            if value:
                checks.append((f"ENV: {var}", "✅", "Set"))
            else:
                checks.append((f"ENV: {var}", "❌", "Not set"))
        
        # Check Solana wallet
        wallet_path = os.getenv("SOLANA_WALLET_PATH", "~/.config/solana/id.json")
        wallet_path = os.path.expanduser(wallet_path)
        if os.path.exists(wallet_path):
            checks.append(("Solana Wallet", "✅", f"Found at {wallet_path}"))
        else:
            checks.append(("Solana Wallet", "❌", f"Not found at {wallet_path}"))
        
        # Test market data connection
        try:
            async with MarketDataManager() as market_data:
                price_data = await market_data.get_token_price("sol")
                checks.append(("Market Data", "✅", f"SOL: ${price_data['price']:.2f}"))
        except Exception as e:
            checks.append(("Market Data", "❌", f"Error: {str(e)[:50]}"))
        
        # Test Solana connection (if wallet exists)
        if os.path.exists(wallet_path):
            try:
                config = SolanaConfig(
                    network=os.getenv("SOLANA_NETWORK", "devnet"),
                    wallet_path=wallet_path
                )
                async with SolanaConnection(config) as connection:
                    balance = await connection.get_balance()
                    checks.append(("Solana Connection", "✅", f"Balance: {balance:.4f} SOL"))
            except Exception as e:
                checks.append(("Solana Connection", "❌", f"Error: {str(e)[:50]}"))
        
        # Display results
        table = Table(title="System Verification Results")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details", style="dim")
        
        for component, status, details in checks:
            table.add_row(component, status, details)
        
        console.print(table)
        
        # Summary
        passed = sum(1 for _, status, _ in checks if status == "✅")
        total = len(checks)
        
        if passed == total:
            rprint(f"\n🎉 [green]All checks passed! ({passed}/{total})[/green]")
            rprint("Your Solana Swarm setup is ready!")
        else:
            rprint(f"\n⚠️ [yellow]{passed}/{total} checks passed[/yellow]")
            rprint("Please fix the issues above before proceeding.")
    
    asyncio.run(run_verification())

@app.command()
def monitor(
    token: str = typer.Option("sol", "--token", "-t", help="Token to monitor"),
    interval: int = typer.Option(60, "--interval", "-i", help="Update interval in seconds"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Specific agent to use")
):
    """Monitor token prices and market conditions."""
    
    async def run_monitoring():
        rprint(f"🔍 [cyan]Starting price monitoring for {token.upper()}[/cyan]")
        rprint(f"📊 Update interval: {interval} seconds")
        rprint("Press Ctrl+C to stop\n")
        
        # Load price monitor plugin
        loader = PluginLoader()
        try:
            plugin = await loader.load_plugin("price-monitor")
            
            while True:
                try:
                    result = await plugin.evaluate({"token": token})
                    
                    if "error" not in result:
                        price = result.get("price", 0)
                        change = result.get("change_24h", 0)
                        confidence = result.get("confidence", 0)
                        
                        change_color = "green" if change >= 0 else "red"
                        arrow = "↗️" if change >= 0 else "↘️"
                        
                        rprint(f"{arrow} [bold]{token.upper()}[/bold]: ${price:.2f} "
                              f"([{change_color}]{change:+.2f}%[/{change_color}]) "
                              f"- Confidence: {confidence:.1%}")
                    else:
                        rprint(f"❌ [red]Error: {result['error']}[/red]")
                    
                    await asyncio.sleep(interval)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    rprint(f"❌ [red]Monitoring error: {e}[/red]")
                    await asyncio.sleep(interval)
                    
        except Exception as e:
            rprint(f"❌ [red]Failed to load price monitor: {e}[/red]")
        finally:
            await loader.cleanup()
    
    try:
        asyncio.run(run_monitoring())
    except KeyboardInterrupt:
        rprint("\n👋 [yellow]Monitoring stopped[/yellow]")

@app.command()
def chat(
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Agent to chat with"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file")
):
    """Start interactive chat with agents."""
    from solana_swarm.cli.chat import start_chat
    
    try:
        asyncio.run(start_chat(agent, config))
    except KeyboardInterrupt:
        rprint("\n👋 [yellow]Chat session ended[/yellow]")

@app.command()
def status():
    """Show system and agent status."""
    
    async def show_status():
        rprint("📊 [cyan]Solana Swarm Status[/cyan]\n")
        
        # System info
        table = Table(title="System Information")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Details")
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        table.add_row("Python", "✅", python_version)
        
        # Environment
        env = os.getenv("ENVIRONMENT", "unknown")
        table.add_row("Environment", "✅", env)
        
        # Network
        network = os.getenv("SOLANA_NETWORK", "unknown")
        table.add_row("Solana Network", "✅", network)
        
        console.print(table)
        console.print()
        
        # Market data
        try:
            async with MarketDataManager() as market_data:
                sol_data = await market_data.get_token_price("sol")
                
                market_table = Table(title="Market Data")
                market_table.add_column("Token", style="cyan")
                market_table.add_column("Price", style="bold")
                market_table.add_column("24h Change", style="bold")
                market_table.add_column("Source")
                
                price = sol_data.get("price", 0)
                change = sol_data.get("change_24h", 0)
                source = sol_data.get("source", "unknown")
                
                change_color = "green" if change >= 0 else "red"
                change_text = f"[{change_color}]{change:+.2f}%[/{change_color}]"
                
                market_table.add_row("SOL", f"${price:.2f}", change_text, source)
                console.print(market_table)
                
        except Exception as e:
            rprint(f"❌ [red]Market data error: {e}[/red]")
        
        console.print()
        
        # Available agents
        loader = PluginLoader()
        try:
            agents = await loader.load_all_plugins()
            
            if agents:
                agent_table = Table(title="Available Agents")
                agent_table.add_column("Name", style="cyan")
                agent_table.add_column("Role", style="bold")
                agent_table.add_column("Status", style="bold")
                
                for name, agent in agents.items():
                    role = getattr(agent, "role", "unknown")
                    status = "✅ Ready" if hasattr(agent, "_is_initialized") else "❓ Unknown"
                    agent_table.add_row(name, role, status)
                
                console.print(agent_table)
            else:
                rprint("⚠️ [yellow]No agents loaded[/yellow]")
                
        except Exception as e:
            rprint(f"❌ [red]Agent loading error: {e}[/red]")
        finally:
            await loader.cleanup()
    
    asyncio.run(show_status())

@app.command()
def create(
    type: str = typer.Argument(..., help="Type to create (agent, strategy)"),
    name: str = typer.Argument(..., help="Name of the item to create"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Template to use")
):
    """Create new agents or strategies."""
    from solana_swarm.cli.create import create_item
    
    try:
        asyncio.run(create_item(type, name, template))
    except Exception as e:
        rprint(f"❌ [red]Creation failed: {e}[/red]")
        sys.exit(1)

@app.command()
def config(
    action: str = typer.Argument(..., help="Action (show, set, list)"),
    key: Optional[str] = typer.Argument(None, help="Configuration key"),
    value: Optional[str] = typer.Argument(None, help="Configuration value")
):
    """Manage configuration settings."""
    from solana_swarm.cli.config import manage_config
    
    try:
        asyncio.run(manage_config(action, key, value))
    except Exception as e:
        rprint(f"❌ [red]Configuration error: {e}[/red]")
        sys.exit(1)

@app.command()
def plugins(
    action: str = typer.Argument(..., help="Action (list, install, remove)"),
    name: Optional[str] = typer.Argument(None, help="Plugin name")
):
    """Manage plugins."""
    from solana_swarm.cli.plugins import manage_plugins
    
    try:
        asyncio.run(manage_plugins(action, name))
    except Exception as e:
        rprint(f"❌ [red]Plugin management error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    app()