"""
Custom exceptions for the Solana Swarm Intelligence Framework.
"""

class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass

class SolanaError(Exception):
    """Exception for Solana blockchain interaction errors."""
    pass

class LLMError(Exception):
    """Exception for LLM-related errors."""
    pass

class ConfigError(Exception):
    """Exception for configuration-related errors."""
    pass

class MarketDataError(Exception):
    """Exception for market data-related errors."""
    pass

class PluginError(Exception):
    """Exception for plugin-related errors."""
    pass

class DEXError(SolanaError):
    """Exception for DEX-related errors."""
    pass

class JupiterError(DEXError):
    """Exception for Jupiter aggregator errors."""
    pass

class RaydiumError(DEXError):
    """Exception for Raydium DEX errors."""
    pass

class OrcaError(DEXError):
    """Exception for Orca DEX errors."""
    pass
''')

    def write_plugin_files(self):
        """Write plugin system files"""
        
        # Plugin base classes
        self.write_file("solana_swarm/plugins/__init__.py", '''"""
Plugin System for Solana Swarm Intelligence
Provides extensibility for custom agents while maintaining core functionality
"""

from typing import Dict, Type
from .base import AgentPlugin
from .loader import PluginLoader

# Global plugin registry
_plugin_registry: Dict[str, Type[AgentPlugin]] = {}

def register_plugin(name: str, plugin_class: Type[AgentPlugin]) -> None:
    """Register a new agent plugin"""
    _plugin_registry[name] = plugin_class

def get_plugin(name: str) -> Type[AgentPlugin]:
    """Get a registered plugin by name"""
    if name not in _plugin_registry:
        raise ValueError(f"Plugin '{name}' not found")
    return _plugin_registry[name]

def list_plugins() -> Dict[str, Type[AgentPlugin]]:
    """List all registered plugins"""
    return dict(_plugin_registry)

__all__ = [
    'AgentPlugin',
    'PluginLoader',
    'register_plugin',
    'get_plugin',
    'list_plugins',
]