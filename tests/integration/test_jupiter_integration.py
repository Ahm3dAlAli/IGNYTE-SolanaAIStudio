"""
Integration tests for Jupiter DEX aggregator.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal

from solana_swarm.integrations.jupiter.client import JupiterClient
from solana_swarm.integrations.jupiter.types import JupiterQuote, JupiterRoute
from solana_swarm.core.exceptions import JupiterError


@pytest.fixture
async def jupiter_client():
    """Create Jupiter client for testing."""
    client = JupiterClient()
    await client._ensure_session()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_jupiter_client_initialization():
    """Test Jupiter client initialization."""
    client = JupiterClient()
    assert client.session is None
    
    await client._ensure_session()
    assert client.session is not None
    assert not client.session.closed
    
    await client.close()
    assert client.session.closed


@pytest.mark.asyncio
async def test_get_quote(jupiter_client):
    """Test getting a swap quote."""
    mock_response = {
        "inputMint": "So11111111111111111111111111111111111111112",
        "inAmount": "1000000000",
        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "outAmount": "50000000",
        "otherAmountThreshold": "49500000",
        "swapMode": "ExactIn",
        "slippageBps": 50,
        "platformFee": None,
        "priceImpactPct": "0.01",
        "routePlan": [{"swapInfo": {"label": "Raydium"}}],
        "contextSlot": 123456789,
        "timeTaken": 0.123
    }
    
    with patch.object(jupiter_client.session, 'get') as mock_get:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_get.return_value.__aenter__.return_value = mock_response_obj
        
        quote = await jupiter_client.get_quote(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            amount=1000000000,
            slippage_bps=50
        )
        
        assert isinstance(quote, JupiterQuote)
        assert quote.input_mint == "So11111111111111111111111111111111111111112"
        assert quote.in_amount == 1000000000
        assert quote.out_amount == 50000000


@pytest.mark.asyncio
async def test_get_quote_error(jupiter_client):
    """Test error handling for quote request."""
    with patch.object(jupiter_client.session, 'get