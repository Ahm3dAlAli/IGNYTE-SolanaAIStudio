"""
Configuration Schema Validation for Solana Swarm Intelligence
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

class NetworkType(str, Enum):
    """Supported Solana networks"""
    DEVNET = "devnet"
    TESTNET = "testnet"
    MAINNET = "mainnet"

class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENROUTER = "openrouter"
    OPENAI = "openai"

class AgentRole(str, Enum):
    """Supported agent roles"""
    MARKET_ANALYZER = "market_analyzer"
    RISK_MANAGER = "risk_manager"
    STRATEGY_OPTIMIZER = "strategy_optimizer"
    DECISION_MAKER = "decision_maker"
    PORTFOLIO_MANAGER = "portfolio_manager"
    ARBITRAGE_AGENT = "arbitrage_agent"
    YIELD_FARMER = "yield_farmer"

class LLMConfigSchema(BaseModel):
    """LLM configuration schema"""
    provider: LLMProvider = Field(default=LLMProvider.OPENROUTER)
    api_key: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2000, gt=0)
    api_url: str = Field(default="https://openrouter.ai/api/v1")
    system_prompt: Optional[str] = None

class SolanaConfigSchema(BaseModel):
    """Solana configuration schema"""
    network: NetworkType = Field(default=NetworkType.DEVNET)
    rpc_url: str = Field(..., regex=r'^https?://')
    wallet_path: Optional[str] = None
    private_key: Optional[str] = None
    commitment: str = Field(default="confirmed")
    
    @validator('wallet_path')
    def validate_wallet_or_key(cls, v, values):
        if not v and not values.get('private_key'):
            raise ValueError('Either wallet_path or private_key must be provided')
        return v

class AgentConfigSchema(BaseModel):
    """Agent configuration schema"""
    name: str = Field(..., min_length=1, max_length=50)
    role: AgentRole
    description: str = Field(..., min_length=1)
    version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    llm: LLMConfigSchema
    capabilities: List[str] = Field(default_factory=list)
    custom_settings: Dict[str, Any] = Field(default_factory=dict)

class PluginConfigSchema(BaseModel):
    """Plugin configuration schema"""
    name: str = Field(..., min_length=1)
    role: AgentRole
    capabilities: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    custom_settings: Dict[str, Any] = Field(default_factory=dict)

class SwarmConfigSchema(BaseModel):
    """Swarm configuration schema"""
    name: str = Field(..., min_length=1)
    version: str = Field(default="0.1.0")
    environment: str = Field(default="development")
    agents: List[Dict[str, Any]] = Field(default_factory=list)
    consensus: Dict[str, Any] = Field(default_factory=dict)
    logging: Dict[str, Any] = Field(default_factory=dict)

class StrategyConfigSchema(BaseModel):
    """Strategy configuration schema"""
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    agents: List[str] = Field(..., min_items=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_management: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=False)