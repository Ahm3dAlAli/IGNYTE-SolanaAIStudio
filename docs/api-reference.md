# API Reference

## Core Classes

### SwarmAgent

The main agent class that implements swarm intelligence.

```python
class SwarmAgent:
    def __init__(self, config: SwarmConfig)
    async def initialize() -> None
    async def join_swarm(peers: List[SwarmAgent]) -> None
    async def propose_action(action_type: str, params: Dict) -> Dict
    async def evaluate_proposal(proposal: Dict) -> Dict
    async def cleanup() -> None
```

### AgentPlugin

Base class for all agent plugins.

```python
class AgentPlugin(ABC):
    def __init__(self, agent_config: AgentConfig, plugin_config: PluginConfig)
    async def initialize() -> None
    async def evaluate(context: Dict[str, Any]) -> Dict[str, Any]
    async def execute(operation: str, **kwargs) -> Any
    async def cleanup() -> None
```

## Configuration Classes

### SwarmConfig

```python
@dataclass
class SwarmConfig:
    role: str
    min_confidence: float = 0.7
    min_votes: int = 2
    timeout: float = 60.0
    llm: Optional[LLMConfig] = None
```

### AgentConfig  

```python
class AgentConfig(BaseModel):
    name: str
    llm: Optional[LLMSettings] = None
    solana: Optional[SolanaSettings] = None
    environment: str = "development"
    log_level: str = "INFO"
```

## Market Data Classes

### MarketDataManager

```python
class MarketDataManager:
    async def get_token_price(symbol: str) -> PriceData
    async def get_dex_data(dex_name: str) -> DexData
    async def get_market_overview() -> Dict[str, Any]
```

### PriceData

```python
@dataclass
class PriceData:
    symbol: str
    price: Decimal
    volume_24h: Decimal
    change_24h: float
    timestamp: datetime
    source: DataSource
```

## Solana Integration Classes

### SolanaConnection

```python
class SolanaConnection:
    def __init__(self, config: SolanaConfig)
    async def get_balance(address: PublicKey = None) -> Decimal
    async def transfer_sol(recipient: PublicKey, amount: Decimal) -> str
    async def swap_tokens(input_mint: PublicKey, output_mint: PublicKey, 
                         amount: Decimal, slippage: float = 0.01) -> Dict
```

## Jupiter Integration

### JupiterClient

```python
class JupiterClient:
    async def get_quote(input_mint: str, output_mint: str, 
                       amount: int, slippage_bps: int = 50) -> JupiterQuote
    async def swap(quote: JupiterQuote, user_public_key: PublicKey) -> Dict
    async def get_price(input_mint: str, output_mint: str) -> Dict
```

## Plugin Development

### Creating Custom Plugins

```python
from solana_swarm.plugins.base import AgentPlugin

class CustomPlugin(AgentPlugin):
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Your evaluation logic
        return {
            'observation': 'Market observation',
            'reasoning': 'Analysis reasoning', 
            'conclusion': 'Final conclusion',
            'confidence': 0.85
        }
```

## CLI Commands

### Basic Commands

```bash
# Initialize project
solana-swarm init my-project

# Verify setup
solana-swarm verify

# Start monitoring
solana-swarm monitor --token SOL

# Interactive chat
solana-swarm chat
```

### Configuration Commands

```bash
# View configuration
solana-swarm config show

# Set configuration
solana-swarm config set llm.temperature 0.8

# View environment variables  
solana-swarm config env
```

## Error Handling

### Exception Hierarchy

```python
class AgentError(Exception): pass
class SolanaError(Exception): pass
class LLMError(Exception): pass
class MarketDataError(Exception): pass
class PluginError(Exception): pass
class DEXError(SolanaError): pass
class JupiterError(DEXError): pass
```

### Error Response Format

```python
{
    "error": "Error description",
    "error_type": "ErrorClass", 
    "timestamp": "2024-01-01T00:00:00Z",
    "context": {...}
}
```
