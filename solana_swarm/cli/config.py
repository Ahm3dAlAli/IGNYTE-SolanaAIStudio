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
        self.config_file = Path.cwd() / "swarm.yaml"
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
        """Get default configuration."""
        return {
            "name": "solana-swarm-project",
            "version": "0.1.0",
            "environment": "development",
            "llm": {
                "provider": "openrouter",
                "model": "anthropic/claude-3.5-sonnet",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "solana": {
                "network": "devnet",
                "rpc_url": "https://api.devnet.solana.com",
                "commitment": "confirmed"
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
            "logging": {
                "level": "INFO",
                "file": "logs/solana_swarm.log"
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
                    table.add_row(full_key, f"[{len(value)} items]", "list")
                else:
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    table.add_row(full_key, value_str, type(value).__name__)
        
        add_config_rows(self.config)
        console.print(table)

async def manage_config(action: str, key: Optional[str] = None, value: Optional[str] = None):
    """Manage configuration settings."""
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
    
    elif action == "env":
        # Show environment variables
        table = Table(title="Environment Variables")
        table.add_column("Variable", style="cyan")
        table.add_column("Value", style="bold")
        table.add_column("Set", style="dim")
        
        env_vars = [
            "LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL",
            "SOLANA_NETWORK", "SOLANA_RPC_URL", "SOLANA_WALLET_PATH",
            "ENVIRONMENT", "LOG_LEVEL"
        ]
        
        for var in env_vars:
            value = os.getenv(var, "")
            is_set = "✅" if value else "❌"
            display_value = value if len(value) < 30 else value[:27] + "..."
            if var == "LLM_API_KEY" and value:
                display_value = value[:10] + "..." + value[-5:] if len(value) > 15 else "*" * len(value)
            
            table.add_row(var, display_value, is_set)
        
        console.print(table)
    
    else:
        rprint(f"❌ [red]Unknown action: {action}[/red]")
        rprint("Available actions: show, set, list, env")
