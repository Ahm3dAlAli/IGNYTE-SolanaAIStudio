"""
Configuration management for Solana Swarm CLI
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

from rich import print as rprint
from rich.table import Table
from rich.console import Console

console = Console()

class ConfigManager:
    """Manages Solana Swarm configuration."""
    
    def __init__(self):
        self.config_file = Path.cwd() / "solana_swarm.yaml"
        self.env_file = Path.cwd() / ".env"
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception as e:
                rprint(f"❌ [red]Error loading config: {e}[/red]")
                self.config = {}
        else:
            self.config = self.get_default_config()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            rprint("✅ [green]Configuration saved[/green]")
        except Exception as e:
            rprint(f"❌ [red]Error saving config: {e}[/red]")
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Solana."""
        return {
            "name": "solana-swarm-project",
            "version": "0.1.0",
            "environment": "development",
            "network": "devnet",
            "llm": {
                "provider": "openrouter",
                "model": "anthropic/claude-3.5-sonnet",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "solana": {
                "network": "devnet",
                "rpc_url": "https://api.devnet.solana.com",
                "commitment": "confirmed",
                "wallet_path": "~/.config/solana/id.json"
            },
            "dexes": {
                "preferred": ["jupiter", "raydium", "orca"],
                "max_slippage": 0.01,
                "min_liquidity": 100000,
                "jupiter": {
                    "api_url": "https://quote-api.jup.ag/v6",
                    "enabled": True
                },
                "raydium": {
                    "api_url": "https://api.raydium.io/v2",
                    "enabled": True
                },
                "orca": {
                    "api_url": "https://api.mainnet.orca.so/v1",
                    "enabled": True
                }
            },
            "agents": [
                {
                    "name": "price-monitor",
                    "role": "market_analyzer",
                    "enabled": True
                },
                {
                    "name": "decision-maker",
                    "role": "strategy_optimizer", 
                    "enabled": True
                }
            ],
            "strategies": [],
            "risk_management": {
                "max_position_size": 1000,
                "daily_loss_limit": 0.05,
                "stop_loss_percentage": 0.05,
                "take_profit_percentage": 0.10,
                "dry_run": True
            },
            "logging": {
                "level": "INFO",
                "file": "logs/solana_swarm.log",
                "max_size": "10MB",
                "backup_count": 5
            }
        }
    
    def get_value(self, key: str) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def set_value(self, key: str, value: str):
        """Set configuration value by key."""
        keys = key.split('.')
        config = self.config
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set value (try to parse as appropriate type)
        final_key = keys[-1]
        parsed_value = self.parse_value(value)
        config[final_key] = parsed_value
    
    def parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type."""
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try list (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # Return as string
        return value
    
    def list_all(self):
        """List all configuration values."""
        table = Table(title="Solana Swarm Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold")
        table.add_column("Type", style="dim")
        
        def add_config_rows(config: Dict, prefix: str = ""):
            for key, value in config.items():
                full_key = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    add_config_rows(value, full_key)
                elif isinstance(value, list):
                    if len(value) <= 5:  # Show small lists
                        table.add_row(full_key, str(value), "list")
                    else:
                        table.add_row(full_key, f"[{len(value)} items]", "list")
                else:
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    table.add_row(full_key, value_str, type(value).__name__)
        
        add_config_rows(self.config)
        console.print(table)
    
    def validate_solana_config(self) -> bool:
        """Validate Solana-specific configuration."""
        issues = []
        
        # Check Solana network
        network = self.get_value("solana.network")
        if network not in ["devnet", "testnet", "mainnet-beta"]:
            issues.append(f"Invalid Solana network: {network}")
        
        # Check DEX configuration
        preferred_dexes = self.get_value("dexes.preferred")
        if preferred_dexes:
            valid_dexes = ["jupiter", "raydium", "orca", "serum"]
            invalid_dexes = [dex for dex in preferred_dexes if dex not in valid_dexes]
            if invalid_dexes:
                issues.append(f"Invalid DEXes: {invalid_dexes}")
        
        # Check slippage values
        max_slippage = self.get_value("dexes.max_slippage")
        if max_slippage and (max_slippage < 0 or max_slippage > 1):
            issues.append(f"Invalid max_slippage: {max_slippage} (should be 0-1)")
        
        # Check risk management
        stop_loss = self.get_value("risk_management.stop_loss_percentage")
        if stop_loss and (stop_loss < 0 or stop_loss > 1):
            issues.append(f"Invalid stop_loss_percentage: {stop_loss}")
        
        take_profit = self.get_value("risk_management.take_profit_percentage")
        if take_profit and (take_profit < 0 or take_profit > 1):
            issues.append(f"Invalid take_profit_percentage: {take_profit}")
        
        if issues:
            rprint("❌ [red]Configuration validation failed:[/red]")
            for issue in issues:
                rprint(f"   • {issue}")
            return False
        
        rprint("✅ [green]Solana configuration is valid[/green]")
        return True

async def manage_config(action: str, key: Optional[str] = None, value: Optional[str] = None):
    """Manage Solana configuration settings."""
    manager = ConfigManager()
    
    if action == "show" or action == "list":
        if key:
            # Show specific key
            config_value = manager.get_value(key)
            if config_value is not None:
                rprint(f"[cyan]{key}[/cyan]: {config_value}")
            else:
                rprint(f"❌ [red]Configuration key '{key}' not found[/red]")
        else:
            # Show all configuration
            manager.list_all()
    
    elif action == "set":
        if not key or value is None:
            rprint("❌ [red]Both key and value are required for 'set' action[/red]")
            return
        
        try:
            manager.set_value(key, value)
            manager.save_config()
            rprint(f"✅ [green]Set {key} = {value}[/green]")
        except Exception as e:
            rprint(f"❌ [red]Error setting configuration: {e}[/red]")
    
    elif action == "validate":
        # Validate Solana-specific configuration
        manager.validate_solana_config()
    
    elif action == "env":
        # Show environment variables
        table = Table(title="Solana Environment Variables")
        table.add_column("Variable", style="cyan")
        table.add_column("Value", style="bold") 
        table.add_column("Set", style="dim")
        table.add_column("Description", style="dim")
        
        env_vars = [
            ("LLM_PROVIDER", "LLM provider (openrouter/openai)"),
            ("LLM_API_KEY", "API key for LLM provider"),
            ("LLM_MODEL", "LLM model to use"),
            ("SOLANA_NETWORK", "Solana network (devnet/testnet/mainnet-beta)"),
            ("SOLANA_RPC_URL", "Solana RPC endpoint URL"),
            ("SOLANA_WALLET_PATH", "Path to Solana keypair file"),
            ("SOLANA_COMMITMENT", "Transaction commitment level"),
            ("COINGECKO_API_KEY", "CoinGecko API key (optional)"),
            ("ENVIRONMENT", "Environment (development/production)"),
            ("LOG_LEVEL", "Logging level (DEBUG/INFO/WARN/ERROR)"),
            ("DRY_RUN", "Enable dry run mode (true/false)")
        ]
        
        for var, description in env_vars:
            value = os.getenv(var, "")
            is_set = "✅" if value else "❌"
            
            # Mask sensitive values
            if var in ["LLM_API_KEY", "COINGECKO_API_KEY"] and value:
                if len(value) > 15:
                    display_value = value[:10] + "..." + value[-5:]
                else:
                    display_value = "*" * len(value)
            else:
                display_value = value if len(value) < 30 else value[:27] + "..."
            
            table.add_row(var, display_value, is_set, description)
        
        console.print(table)
    
    elif action == "init":
        # Initialize default configuration for Solana
        if manager.config_file.exists():
            if not console.input("Configuration file exists. Overwrite? (y/N): ").lower().startswith('y'):
                return
        
        manager.config = manager.get_default_config()
        manager.save_config()
        
        rprint("✅ [green]Initialized default Solana configuration[/green]")
        rprint("\nNext steps:")
        rprint("1. Set environment variables in .env file:")
        rprint("   • LLM_API_KEY=your_api_key")
        rprint("   • SOLANA_WALLET_PATH=/path/to/keypair.json")
        rprint("2. Configure preferred DEXes:")
        rprint("   • solana-swarm config set dexes.preferred jupiter,raydium,orca")
        rprint("3. Validate configuration:")
        rprint("   • solana-swarm config validate")
    
    elif action == "network":
        # Quick network switching
        if not key:
            current_network = manager.get_value("solana.network")
            rprint(f"Current Solana network: [cyan]{current_network}[/cyan]")
            rprint("Available networks: devnet, testnet, mainnet-beta")
            return
        
        valid_networks = ["devnet", "testnet", "mainnet-beta"]
        if key not in valid_networks:
            rprint(f"❌ [red]Invalid network: {key}[/red]")
            rprint(f"Valid networks: {', '.join(valid_networks)}")
            return
        
        # Update network and corresponding RPC URL
        manager.set_value("solana.network", key)
        
        if key == "devnet":
            manager.set_value("solana.rpc_url", "https://api.devnet.solana.com")
        elif key == "testnet":
            manager.set_value("solana.rpc_url", "https://api.testnet.solana.com")
        elif key == "mainnet-beta":
            manager.set_value("solana.rpc_url", "https://api.mainnet-beta.solana.com")
        
        manager.save_config()
        rprint(f"✅ [green]Switched to {key} network[/green]")
    
    elif action == "dex":
        # DEX configuration management
        if not key:
            preferred = manager.get_value("dexes.preferred")
            rprint(f"Preferred DEXes: [cyan]{', '.join(preferred) if preferred else 'None'}[/cyan]")
            
            # Show DEX status
            dex_table = Table(title="Solana DEX Configuration")
            dex_table.add_column("DEX", style="cyan")
            dex_table.add_column("Enabled", style="bold")
            dex_table.add_column("API URL", style="dim")
            
            for dex in ["jupiter", "raydium", "orca"]:
                enabled = manager.get_value(f"dexes.{dex}.enabled")
                api_url = manager.get_value(f"dexes.{dex}.api_url")
                status = "✅" if enabled else "❌"
                dex_table.add_row(dex.title(), status, str(api_url or "Not configured"))
            
            console.print(dex_table)
            return
        
        # Enable/disable DEX or set preferences
        if key == "enable" and value:
            valid_dexes = ["jupiter", "raydium", "orca"]
            if value in valid_dexes:
                manager.set_value(f"dexes.{value}.enabled", "true")
                manager.save_config()
                rprint(f"✅ [green]Enabled {value} DEX[/green]")
            else:
                rprint(f"❌ [red]Invalid DEX: {value}[/red]")
        elif key == "disable" and value:
            valid_dexes = ["jupiter", "raydium", "orca"]
            if value in valid_dexes:
                manager.set_value(f"dexes.{value}.enabled", "false")
                manager.save_config()
                rprint(f"✅ [green]Disabled {value} DEX[/green]")
            else:
                rprint(f"❌ [red]Invalid DEX: {value}[/red]")
        elif key == "prefer":
            if value:
                dexes = [dex.strip() for dex in value.split(',')]
                valid_dexes = ["jupiter", "raydium", "orca", "serum"]
                invalid_dexes = [dex for dex in dexes if dex not in valid_dexes]
                
                if invalid_dexes:
                    rprint(f"❌ [red]Invalid DEXes: {', '.join(invalid_dexes)}[/red]")
                    return
                
                manager.set_value("dexes.preferred", ','.join(dexes))
                manager.save_config()
                rprint(f"✅ [green]Set preferred DEXes: {', '.join(dexes)}[/green]")
            else:
                rprint("❌ [red]Please provide comma-separated DEX names[/red]")
    
    elif action == "agent":
        # Agent configuration management
        if not key:
            agents = manager.get_value("agents")
            if agents:
                agent_table = Table(title="Configured Agents")
                agent_table.add_column("Name", style="cyan")
                agent_table.add_column("Role", style="bold")
                agent_table.add_column("Enabled", style="dim")
                
                for agent in agents:
                    status = "✅" if agent.get("enabled", True) else "❌"
                    agent_table.add_row(
                        agent.get("name", "Unknown"),
                        agent.get("role", "Unknown"),
                        status
                    )
                console.print(agent_table)
            else:
                rprint("No agents configured")
            return
        
        # Add or configure agent
        if key == "add" and value:
            parts = value.split(':')
            if len(parts) != 2:
                rprint("❌ [red]Format: agent_name:role[/red]")
                return
                
            agent_name, role = parts
            valid_roles = ["market_analyzer", "strategy_optimizer", "arbitrage_agent", "yield_farmer"]
            
            if role not in valid_roles:
                rprint(f"❌ [red]Invalid role: {role}[/red]")
                rprint(f"Valid roles: {', '.join(valid_roles)}")
                return
            
            agents = manager.get_value("agents") or []
            # Check if agent already exists
            existing = next((a for a in agents if a.get("name") == agent_name), None)
            if existing:
                existing["role"] = role
                existing["enabled"] = True
            else:
                agents.append({
                    "name": agent_name,
                    "role": role,
                    "enabled": True
                })
            
            manager.set_value("agents", agents)
            manager.save_config()
            rprint(f"✅ [green]Added agent {agent_name} with role {role}[/green]")
    
    else:
        rprint(f"❌ [red]Unknown action: {action}[/red]")
        rprint("Available actions: show, set, list, env, validate, init, network, dex, agent")

# CLI command integration
@click.group()
def config():
    """Configuration management commands"""
    pass

@config.command()
@click.argument('action')
@click.argument('key', required=False)
@click.argument('value', required=False)
def manage(action: str, key: Optional[str] = None, value: Optional[str] = None):
    """Manage Solana Swarm configuration
    
    Actions:
    - show [key]     Show configuration (optionally specific key)
    - set key value  Set configuration value
    - validate       Validate configuration
    - env           Show environment variables
    - init          Initialize default configuration
    - network [name] Show/set Solana network
    - dex [action]   Manage DEX configuration
    - agent [action] Manage agent configuration
    """
    import asyncio
    asyncio.run(manage_config(action, key, value))

if __name__ == "__main__":
    config()