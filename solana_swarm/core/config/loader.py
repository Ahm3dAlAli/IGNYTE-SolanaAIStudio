"""
Configuration Loader for Solana Swarm Intelligence
Loads and validates configuration from multiple sources
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging

from solana_swarm.core.agent import AgentConfig, LLMSettings, SolanaSettings
from solana_swarm.plugins.base import PluginConfig
from solana_swarm.core.exceptions import ConfigError

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Loads and manages configuration from various sources"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(".")
        self.env_vars = self._load_env_variables()
        
    def _load_env_variables(self) -> Dict[str, str]:
        """Load environment variables for substitution"""
        return {
            "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "openrouter"),
            "LLM_API_KEY": os.getenv("LLM_API_KEY", ""),
            "LLM_MODEL": os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet"),
            "LLM_API_URL": os.getenv("LLM_API_URL", "https://openrouter.ai/api/v1"),
            "SOLANA_NETWORK": os.getenv("SOLANA_NETWORK", "devnet"),
            "SOLANA_RPC_URL": os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com"),
            "SOLANA_WALLET_PATH": os.getenv("SOLANA_WALLET_PATH", "~/.config/solana/id.json"),
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
        }
    
    def _substitute_env_vars(self, data: Union[Dict, str, Any]) -> Any:
        """Substitute environment variables in configuration"""
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            env_var = data[2:-1]
            return self.env_vars.get(env_var, data)
        return data
    
    def load_agent_config(self, agent_name: str) -> AgentConfig:
        """Load agent configuration from YAML file"""
        try:
            # Try multiple locations
            config_paths = [
                self.config_dir / "agents" / f"{agent_name}.yaml",
                self.config_dir / "solana_swarm" / "agents" / agent_name / "agent.yaml",
                Path("solana_swarm") / "agents" / agent_name / "agent.yaml"
            ]
            
            config_data = None
            for config_path in config_paths:
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config_data = yaml.safe_load(f)
                    break
            
            if not config_data:
                raise ConfigError(f"Agent configuration not found for: {agent_name}")
            
            # Substitute environment variables
            config_data = self._substitute_env_vars(config_data)
            
            # Create configurations
            llm_config = None
            if "llm" in config_data:
                llm_config = LLMSettings(**config_data["llm"])
            
            solana_config = None
            if "solana" in config_data:
                solana_config = SolanaSettings(**config_data["solana"])
            
            return AgentConfig(
                name=config_data["name"],
                llm=llm_config,
                solana=solana_config,
                environment=config_data.get("environment", "development"),
                log_level=config_data.get("log_level", "INFO"),
                custom_settings=config_data.get("custom_settings", {})
            )
            
        except Exception as e:
            logger.error(f"Error loading agent config for {agent_name}: {str(e)}")
            raise ConfigError(f"Failed to load agent config: {str(e)}")
    
    def load_plugin_config(self, agent_name: str) -> PluginConfig:
        """Load plugin configuration"""
        try:
            config_paths = [
                self.config_dir / "agents" / f"{agent_name}.yaml",
                self.config_dir / "solana_swarm" / "agents" / agent_name / "agent.yaml",
                Path("solana_swarm") / "agents" / agent_name / "agent.yaml"
            ]
            
            config_data = None
            for config_path in config_paths:
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config_data = yaml.safe_load(f)
                    break
            
            if not config_data:
                # Create default plugin config
                return PluginConfig(
                    name=agent_name,
                    role=agent_name.replace("-", "_"),
                    capabilities=[],
                    custom_settings={}
                )
            
            # Substitute environment variables
            config_data = self._substitute_env_vars(config_data)
            
            return PluginConfig(
                name=config_data["name"],
                role=config_data.get("role", agent_name),
                capabilities=config_data.get("capabilities", []),
                system_prompt=config_data.get("llm", {}).get("system_prompt"),
                custom_settings=config_data.get("custom_settings", {})
            )
            
        except Exception as e:
            logger.error(f"Error loading plugin config for {agent_name}: {str(e)}")
            raise ConfigError(f"Failed to load plugin config: {str(e)}")
    
    def load_default_config(self) -> Dict[str, Any]:
        """Load default framework configuration"""
        default_config_path = Path(__file__).parent / "swarm_config.json"
        
        try:
            with open(default_config_path, 'r') as f:
                config = json.load(f)
            return self._substitute_env_vars(config["default_config"])
        except Exception as e:
            logger.error(f"Error loading default config: {str(e)}")
            return {}