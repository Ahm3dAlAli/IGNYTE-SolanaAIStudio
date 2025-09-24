# .gitattributes (empty file as shown in documents)

# CONTRIBUTING.md
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.