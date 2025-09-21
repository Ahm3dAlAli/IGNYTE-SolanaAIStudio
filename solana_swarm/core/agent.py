"""
Solana Swarm Agent Core
Provides the base agent functionality and plugin integration
"""


from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

@dataclass
class LLMSettings:
    """LLM configuration settings"""
    provider: str = "openrouter"
    api_key: str = ""
    model: str = "anthropic/claude-3.5-sonnet"
    temperature: float = 0.7
    max_tokens: int = 2000
    api_url: str = "https://openrouter.ai/api/v1"
    system_prompt: Optional[str] = None

@dataclass
class SolanaSettings:
    """Solana configuration settings"""
    network: str = "devnet"
    rpc_url: str = "https://api.devnet.solana.com"
    wallet_path: Optional[str] = None
    private_key: Optional[str] = None
    commitment: str = "confirmed"

class AgentConfig(BaseModel):
    """Main agent configuration"""
    name: str = Field(..., description="Agent name")
    llm: Optional[LLMSettings] = Field(None, description="LLM configuration")
    solana: Optional[SolanaSettings] = Field(None, description="Solana configuration")
    environment: str = Field("development", description="Deployment environment")
    log_level: str = Field("INFO", description="Logging level")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Custom agent settings")

    class Config:
        """Pydantic config"""
        validate_assignment = True
        extra = "forbid"

class SwarmAgent:
    """Core swarm agent with plugin support"""
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize swarm agent"""
        self.config = config or AgentConfig(name="default_agent")
        self._plugins = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize agent and load plugins"""
        if self._initialized:
            return
            
        try:
            logger.info(f"Initialized SwarmAgent: {self.config.name}")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing SwarmAgent: {str(e)}")
            raise
    
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate using loaded plugins"""
        if not self._initialized:
            await self.initialize()
        
        results = {}
        for name, plugin in self._plugins.items():
            try:
                result = await plugin.evaluate(context)
                results[name] = result
            except Exception as e:
                logger.error(f"Error in plugin {name}: {str(e)}")
                results[name] = {"error": str(e)}
        
        return results
    
    async def cleanup(self) -> None:
        """Clean up agent and plugins"""
        if self._initialized:
            self._plugins = {}
            self._initialized = False
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
        return None