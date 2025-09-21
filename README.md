

# 🚀 Solana Swarm Intelligence Framework

A powerful multi-agent framework for building AI-powered trading strategies on Solana. Inspired by swarm intelligence, this framework enables autonomous agents to collaborate, make decisions, and execute trades across the Solana DeFi ecosystem.

## 🌟 Features

### 🤖 Multi-Agent Architecture
- **Specialized Agents**: Market analyzers, risk managers, strategy optimizers
- **Swarm Intelligence**: Collaborative decision-making with consensus mechanisms
- **Plugin System**: Extensible architecture for custom agent behaviors

### 🔗 Solana Integration
- **Native Solana Support**: Direct blockchain interaction via solana-py
- **DEX Integration**: Jupiter, Raydium, Orca, and other major DEXs
- **SPL Token Support**: Full support for Solana Program Library tokens
- **Real-time Data**: Live market data and network statistics

### 🧠 AI-Powered Decision Making
- **LLM Integration**: Support for multiple AI providers (OpenRouter, OpenAI)
- **Context-Aware**: Agents understand market conditions and network state
- **Risk Management**: Built-in risk assessment and position sizing
- **Strategy Optimization**: Automated parameter tuning and performance tracking

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/solana-swarm/solana-swarm.git
cd solana-swarm

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Configuration

1. **Create environment file**:
```bash
cp .env.example .env
```

2. **Set up your API keys**:
```env
LLM_API_KEY=your_openrouter_api_key
SOLANA_WALLET_PATH=~/.config/solana/id.json
```

3. **Create Solana wallet** (if needed):
```bash
./scripts/create_solana_wallet.sh
```

### Basic Usage

```python
import asyncio
from solana_swarm import SwarmAgent, SwarmConfig, AgentConfig
from solana_swarm.core.llm_provider import LLMConfig

async def main():
    # Configure LLM
    llm_config = LLMConfig(
        provider="openrouter",
        api_key="your_api_key",
        model="anthropic/claude-3.5-sonnet"
    )
    
    # Create swarm configuration
    swarm_config = SwarmConfig(
        role="market_analyzer",
        min_confidence=0.8,
        llm=llm_config
    )
    
    # Initialize agent
    async with SwarmAgent(swarm_config) as agent:
        # Analyze market conditions
        context = {"token": "sol", "action": "analyze"}
        result = await agent.evaluate(context)
        print(f"Market analysis: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 🏗️ Architecture

### Agent Roles

- **🔍 Market Analyzer**: Monitors token prices, liquidity, and market trends
- **⚖️ Risk Manager**: Assesses risks and manages position sizing
- **🎯 Strategy Optimizer**: Optimizes trading strategies and execution
- **🤝 Decision Maker**: Coordinates agent decisions and executes trades

### Core Components

```
solana_swarm/
├── core/                   # Core framework components
│   ├── agent.py           # Base agent implementation
│   ├── swarm_agent.py     # Swarm intelligence logic
│   ├── consensus.py       # Consensus mechanisms
│   ├── market_data.py     # Market data integration
│   ├── solana_integration.py # Solana blockchain integration
│   └── llm_provider.py    # LLM provider abstraction
├── agents/                # Pre-built agent implementations
│   ├── price_monitor/     # Price monitoring agent
│   ├── decision_maker/    # Decision making agent
│   └── portfolio_manager/ # Portfolio management agent
├── plugins/               # Plugin system
└── cli/                  # Command-line interface
```

## 🛠️ Usage Examples

### 1. Price Monitoring

```python
from solana_swarm.agents.price_monitor import PriceMonitorPlugin

async def monitor_sol_price():
    plugin = PriceMonitorPlugin(agent_config, plugin_config)
    await plugin.initialize()
    
    result = await plugin.evaluate({"token": "sol"})
    print(f"SOL Price: ${result['price']}")
    print(f"24h Change: {result['change_24h']:.2f}%")
```

### 2. Multi-Agent Decision Making

```python
async def swarm_decision():
    # Create multiple agents
    agents = [
        SwarmAgent(SwarmConfig(role="market_analyzer")),
        SwarmAgent(SwarmConfig(role="risk_manager")),
        SwarmAgent(SwarmConfig(role="strategy_optimizer"))
    ]
    
    # Initialize agents
    for agent in agents:
        await agent.initialize()
        
    # Join swarm
    await agents[0].join_swarm(agents[1:])
    
    # Propose action
    proposal = {
        "type": "trade",
        "params": {
            "token_pair": "SOL/USDC",
            "amount": 10,
            "direction": "buy"
        }
    }
    
    result = await agents[0].propose_action("trade", proposal["params"])
    print(f"Consensus reached: {result['consensus']}")
```

### 3. Solana DeFi Integration

```python
from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig

async def defi_interaction():
    config = SolanaConfig(
        network="devnet",
        wallet_path="~/.config/solana/id.json"
    )
    
    async with SolanaConnection(config) as connection:
        # Check balance
        balance = await connection.get_balance()
        print(f"Wallet balance: {balance} SOL")
        
        # Swap tokens via Jupiter
        result = await connection.swap_tokens_jupiter(
            input_mint="So11111111111111111111111111111111111111112",  # SOL
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            amount=1.0,
            slippage=0.5
        )
        print(f"Swap result: {result}")
```

## 🔧 CLI Usage

### Interactive Chat Mode
```bash
# Start interactive chat with agents
swarm-chat

# Chat with specific agent
swarm-chat --agent price-monitor

# Load custom configuration
swarm-chat --config ./my_config.yaml
```

### Command Line Operations
```bash
# Run price monitoring
solana-swarm monitor --token SOL --interval 60

# Execute strategy
solana-swarm strategy run --name arbitrage --config strategy.yaml

# Check agent status
solana-swarm status

# Verify setup
solana-swarm verify
```

## 🔌 Plugin Development

Create custom agents by extending the base plugin:

```python
from solana_swarm.plugins.base import AgentPlugin, PluginConfig
from solana_swarm.core.agent import AgentConfig

class CustomAgent(AgentPlugin):
    def __init__(self, agent_config: AgentConfig, plugin_config: PluginConfig):
        super().__init__(agent_config, plugin_config)
    
    async def initialize(self) -> None:
        # Initialize your agent
        pass
    
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Implement your logic
        return {"decision": "approve", "confidence": 0.9}
    
    async def execute(self, operation: str = None, **kwargs) -> Any:
        # Execute operations
        pass
    
    async def cleanup(self) -> None:
        # Cleanup resources
        pass
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=solana_swarm

# Run specific test file
pytest tests/core/test_swarm_agent.py

# Run integration tests
pytest tests/integration/
```

## 📚 Documentation

- [Core Concepts](docs/core-concepts.md)
- [API Reference](docs/api-reference.md)
- [Tutorial](docs/tutorial.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/solana-swarm/solana-swarm.git
cd solana-swarm

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r dev-requirements.txt
pip install -e .

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## ⚠️ Security & Disclaimer

- **Not Financial Advice**: This framework is for educational and research purposes
- **Use at Your Own Risk**: Always test on devnet before mainnet
- **Secure Your Keys**: Never commit private keys or seed phrases
- **Review Code**: Audit any strategies before deploying significant funds

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Solana Foundation](https://solana.org/) for the amazing blockchain platform
- [Jupiter](https://jup.ag/) for DEX aggregation
- [Raydium](https://raydium.io/) and [Orca](https://orca.so/) for DEX infrastructure
- The open-source community for inspiration and tools

## 📞 Support

- **GitHub Issues**: [Bug reports and feature requests](https://github.com/solana-swarm/solana-swarm/issues)
- **Discord**: [Join our community](https://discord.gg/solana-swarm)
- **Documentation**: [docs.solana-swarm.com](https://docs.solana-swarm.com)

---

**Built with ❤️ for the Solana ecosystem**
```

### CONTRIBUTING.md
```markdown
# Contributing to Solana Swarm Intelligence Framework

Thank you for your interest in contributing to the Solana Swarm Intelligence Framework! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Solana CLI tools (optional, for blockchain testing)
- Basic understanding of Solana, DeFi, and AI concepts

### Development Setup

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/solana-swarm.git
   cd solana-swarm
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -r dev-requirements.txt
   pip install -e .
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Verify installation**
   ```bash
   # Run tests to ensure everything works
   pytest
   
   # Check code formatting
   black --check solana_swarm tests
   isort --check-only solana_swarm tests
   ```

## 🎯 How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/solana-swarm/solana-swarm/issues)
2. If not, create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS, etc.)
   - Code snippets or logs if applicable

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue with:
   - Clear description of the feature
   - Use case and motivation
   - Proposed implementation approach
   - Any relevant examples or mockups

### Code Contributions

#### Types of Contributions Welcomed

- **Bug fixes**: Fix existing issues
- **New agents**: Implement specialized trading agents
- **Plugin development**: Create new plugins for different strategies
- **Documentation**: Improve docs, examples, and tutorials
- **Testing**: Add test coverage and integration tests
- **Performance**: Optimize existing code
- **Solana integrations**: Add support for new protocols/DEXs

#### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding standards (see below)
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Run all tests
   pytest
   
   # Check code quality
   black solana_swarm tests
   isort solana_swarm tests
   flake8 solana_swarm tests
   
   # Type checking
   mypy solana_swarm
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new trading strategy agent"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

## 📏 Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 88 characters (Black default)
- **Imports**: Use isort for import organization
- **Type hints**: Required for all public functions
- **Docstrings**: Google-style docstrings for all modules, classes, and functions

### Example Code Style

```python
"""
Example module demonstrating coding style.
"""

import asyncio
from typing import Dict, Any, Optional, List
import logging

from solana_swarm.core.agent import AgentConfig
from solana_swarm.plugins.base import AgentPlugin

logger = logging.getLogger(__name__)


class ExampleAgent(AgentPlugin):
    """
    Example agent demonstrating proper code style.
    
    This agent serves as a template for implementing new trading agents
    in the Solana Swarm Intelligence Framework.
    
    Attributes:
        config: Agent configuration object
        is_initialized: Whether the agent has been initialized
    """
    
    def __init__(
        self, 
        agent_config: AgentConfig, 
        plugin_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the example agent.
        
        Args:
            agent_config: Core agent configuration
            plugin_config: Optional plugin-specific configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        super().__init__(agent_config, plugin_config)
        self.is_initialized = False
    
    async def initialize(self) -> None:
        """Initialize agent resources."""
        try:
            logger.info("Initializing example agent")
            # Initialization logic here
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
    
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate trading opportunity.
        
        Args:
            context: Market context and parameters
            
        Returns:
            Dictionary containing evaluation results
            
        Raises:
            RuntimeError: If agent is not initialized
        """
        if not self.is_initialized:
            raise RuntimeError("Agent not initialized")
        
        # Implementation here
        return {
            "decision": "approve",
            "confidence": 0.8,
            "reasoning": "Market conditions favorable"
        }
```

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(agents): add arbitrage detection agent
fix(market): resolve price data caching issue
docs(readme): update installation instructions
test(core): add integration tests for swarm consensus
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── core/              # Core functionality tests
├── agents/            # Agent-specific tests
├── integration/       # Integration tests
├── fixtures/          # Test data and fixtures
└── conftest.py       # Pytest configuration
```

### Writing Tests

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **Mock External Services**: Use mocks for blockchain calls, API requests
4. **Test Coverage**: Aim for >80% coverage on new code

### Example Test

```python
import pytest
from unittest.mock import AsyncMock, patch

from solana_swarm.agents.price_monitor import PriceMonitorPlugin


@pytest.fixture
async def price_monitor():
    """Create price monitor plugin for testing."""
    config = AgentConfig(name="test-monitor")
    plugin_config = PluginConfig(
        name="price-monitor",
        role="market_analyzer",
        capabilities=["price_monitoring"]
    )
    return PriceMonitorPlugin(config, plugin_config)


@pytest.mark.asyncio
async def test_price_evaluation(price_monitor):
    """Test price evaluation functionality."""
    # Mock market data
    with patch.object(price_monitor, 'get_price_data') as mock_get_price:
        mock_get_price.return_value = {
            "price": 100.0,
            "change_24h": 5.0,
            "source": "coingecko"
        }
        
        result = await price_monitor.evaluate({"token": "sol"})
        
        assert result["price"] == 100.0
        assert "reasoning" in result
        assert result["confidence"] > 0.7


@pytest.mark.asyncio
async def test_price_evaluation_error_handling(price_monitor):
    """Test error handling in price evaluation."""
    with patch.object(price_monitor, 'get_price_data') as mock_get_price:
        mock_get_price.side_effect = Exception("API Error")
        
        result = await price_monitor.evaluate({"token": "sol"})
        
        assert "error" in result
```

## 🔌 Plugin Development Guide

### Creating a New Agent Plugin

1. **Create plugin directory**
   ```bash
   mkdir -p solana_swarm/agents/my_agent
   touch solana_swarm/agents/my_agent/__init__.py
   ```

2. **Create agent configuration** (`agent.yaml`)
   ```yaml
   name: my-agent
   role: custom_analyzer
   description: "Custom analysis agent"
   version: "0.1.0"
   
   llm:
     provider: ${LLM_PROVIDER}
     api_key: ${LLM_API_KEY}
     model: ${LLM_MODEL}
     temperature: 0.7
   
   capabilities:
     - custom_analysis
     - data_processing
   
   custom_settings:
     threshold: 0.8
     max_retries: 3
   ```

3. **Implement plugin** (`plugin.py`)
   ```python
   from solana_swarm.plugins.base import AgentPlugin
   
   class MyAgent(AgentPlugin):
       async def evaluate(self, context):
           # Your logic here
           return {"decision": "approve"}
   ```

### Plugin Best Practices

- **Single Responsibility**: Each plugin should have one clear purpose
- **Configuration Driven**: Use YAML configuration for flexibility
- **Error Handling**: Graceful error handling and logging
- **Testing**: Comprehensive test coverage
- **Documentation**: Clear docstrings and examples

## 📖 Documentation Guidelines

### Documentation Types

1. **Code Documentation**: Docstrings in Google format
2. **API Documentation**: Auto-generated from docstrings
3. **Tutorials**: Step-by-step guides
4. **Examples**: Working code examples
5. **Architecture Docs**: High-level design documentation

### Writing Guidelines

- **Clear and Concise**: Easy to understand for different skill levels
- **Examples**: Include working code examples
- **Up-to-date**: Keep documentation synchronized with code
- **Searchable**: Use clear headings and structure

## 🚀 Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):
- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible

### Release Checklist

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Update documentation
5. Create release PR
6. Tag release after merge
7. Publish to PyPI (maintainers only)

## 🤝 Community Guidelines

### Code of Conduct

- **Be Respectful**: Treat all contributors with respect
- **Be Inclusive**: Welcome contributors from all backgrounds
- **Be Constructive**: Provide helpful feedback and suggestions
- **Be Patient**: Help newcomers learn and contribute

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Discord**: Real-time chat and community support
- **Email**: security@solana-swarm.com for security issues

## 🔒 Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email security@solana-swarm.com
2. Include detailed description
3. Provide steps to reproduce
4. Allow time for investigation and fix

### Security Best Practices

- **Never commit secrets**: Use environment variables
- **Validate inputs**: Sanitize all user inputs
- **Use secure defaults**: Conservative configuration defaults
- **Regular updates**: Keep dependencies updated
- **Code review**: All changes require review

## 📊 Performance Guidelines

### Optimization Principles

1. **Async First**: Use async/await for I/O operations
2. **Efficient Data Structures**: Choose appropriate data structures
3. **Caching**: Cache expensive operations appropriately
4. **Resource Management**: Proper cleanup of resources
5. **Monitoring**: Include performance metrics

### Benchmarking

```python
import time
import asyncio
from typing import Callable

async def benchmark_async(func: Callable, *args, **kwargs) -> float:
    """Benchmark async function execution time."""
    start_time = time.time()
    await func(*args, **kwargs)
    return time.time() - start_time

# Usage in tests
async def test_performance():
    execution_time = await benchmark_async(agent.evaluate, context)
    assert execution_time < 1.0  # Should complete within 1 second
```

## 🎓 Learning Resources

### Solana Development
- [Solana Documentation](https://docs.solana.com/)
- [Solana Cookbook](https://solanacookbook.com/)
- [Anchor Framework](https://project-serum.github.io/anchor/)

### Python Async Programming
- [AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [Real Python AsyncIO Tutorial](https://realpython.com/async-io-python/)

### AI/ML for Trading
- [Quantitative Trading Resources](https://github.com/wilsonfreitas/awesome-quant)
- [Machine Learning for Trading](https://github.com/stefan-jansen/machine-learning-for-trading)

## ❓ FAQ

**Q: How do I get started contributing?**
A: Look for issues labeled "good first issue" or "help wanted". These are designed for newcomers.

**Q: Can I contribute without deep Solana knowledge?**
A: Yes! We welcome contributions in documentation, testing, Python development, and general improvements.

**Q: How long do code reviews take?**
A: We aim to review PRs within 48 hours. Complex changes may take longer.

**Q: Can I work on multiple issues simultaneously?**
A: It's better to focus on one issue at a time to avoid conflicts and ensure quality.

**Q: Do you accept external plugin contributions?**
A: Yes! We encourage community plugins. Make sure they follow our guidelines and are well-tested.

## 🏆 Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- GitHub contributors section
- Community Discord hall of fame

Thank you for contributing to the Solana Swarm Intelligence Framework! 🚀


### LICENSE

MIT License

Copyright (c) 2024 Solana Swarm Intelligence Framework

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
