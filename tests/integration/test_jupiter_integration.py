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
    with patch.object(jupiter_client.session, 'get') as mock_get:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 400
        mock_response_obj.text = AsyncMock(return_value="Bad Request")
        mock_get.return_value.__aenter__.return_value = mock_response_obj
        
        with pytest.raises(JupiterError):
            await jupiter_client.get_quote(
                input_mint="invalid_mint",
                output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                amount=1000000000
            )


@pytest.mark.asyncio
async def test_get_routes(jupiter_client):
    """Test getting swap routes."""
    mock_response = {
        "inputMint": "So11111111111111111111111111111111111111112",
        "inAmount": "1000000000",
        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "outAmount": "50000000",
        "routePlan": [
            {"swapInfo": {"label": "Raydium", "inputMint": "So11111111111111111111111111111111111111112"}},
            {"swapInfo": {"label": "Orca", "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"}}
        ],
        "priceImpactPct": "0.5"
    }
    
    with patch.object(jupiter_client.session, 'get') as mock_get:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_get.return_value.__aenter__.return_value = mock_response_obj
        
        routes = await jupiter_client.get_routes(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            amount=1000000000
        )
        
        assert len(routes) == 1
        route = routes[0]
        assert isinstance(route, JupiterRoute)
        assert route.input_mint == "So11111111111111111111111111111111111111112"
        assert route.output_mint == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


@pytest.mark.asyncio
async def test_get_price(jupiter_client):
    """Test price retrieval."""
    mock_response = {
        "inputMint": "So11111111111111111111111111111111111111112",
        "inAmount": "1000000",
        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "outAmount": "100000000",
        "routePlan": [],
        "priceImpactPct": "0.01",
        "slippageBps": 50,
        "otherAmountThreshold": "99000000",
        "swapMode": "ExactIn",
        "platformFee": None,
        "contextSlot": 123456789,
        "timeTaken": 0.1
    }
    
    with patch.object(jupiter_client, 'get_quote') as mock_get_quote:
        mock_quote = JupiterQuote.from_dict(mock_response)
        mock_get_quote.return_value = mock_quote
        
        price_data = await jupiter_client.get_price(
            input_mint="So11111111111111111111111111111111111111112",
            output_mint="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        )
        
        assert "price" in price_data
        assert price_data["input_mint"] == "So11111111111111111111111111111111111111112"
        assert price_data["output_mint"] == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


@pytest.mark.asyncio
async def test_get_supported_tokens(jupiter_client):
    """Test getting supported tokens."""
    mock_tokens = [
        {
            "address": "So11111111111111111111111111111111111111112",
            "symbol": "SOL",
            "name": "Wrapped SOL",
            "decimals": 9,
            "logoURI": "https://example.com/sol.png"
        },
        {
            "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "symbol": "USDC",
            "name": "USD Coin",
            "decimals": 6,
            "logoURI": "https://example.com/usdc.png"
        }
    ]
    
    with patch.object(jupiter_client.session, 'get') as mock_get:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_tokens)
        mock_get.return_value.__aenter__.return_value = mock_response_obj
        
        tokens = await jupiter_client.get_supported_tokens()
        
        assert len(tokens) == 2
        assert tokens[0]["symbol"] == "SOL"
        assert tokens[1]["symbol"] == "USDC"


@pytest.mark.asyncio
async def test_swap_execution_mock(jupiter_client):
    """Test swap execution with mock data."""
    from solana.publickey import PublicKey
    
    # Mock quote
    mock_quote_data = {
        "inputMint": "So11111111111111111111111111111111111111112",
        "inAmount": "1000000000",
        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "outAmount": "100000000",
        "otherAmountThreshold": "99000000",
        "swapMode": "ExactIn",
        "slippageBps": 50,
        "platformFee": None,
        "priceImpactPct": "0.01",
        "routePlan": [{"swapInfo": {"label": "Raydium"}}],
        "contextSlot": 123456789,
        "timeTaken": 0.123
    }
    
    mock_swap_response = {
        "swapTransaction": "base64_encoded_transaction",
        "lastValidBlockHeight": 123456890,
        "prioritizationFeeLamports": 5000
    }
    
    with patch.object(jupiter_client.session, 'post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_swap_response)
        mock_post.return_value.__aenter__.return_value = mock_response_obj
        
        quote = JupiterQuote.from_dict(mock_quote_data)
        user_key = PublicKey("11111111111111111111111111111111")
        
        swap_result = await jupiter_client.swap(quote, user_key)
        
        assert "swapTransaction" in swap_result
        assert swap_result["swapTransaction"] == "base64_encoded_transaction"


@pytest.mark.asyncio
async def test_jupiter_quote_creation():
    """Test JupiterQuote object creation and serialization."""
    quote_data = {
        "inputMint": "So11111111111111111111111111111111111111112",
        "inAmount": "1000000000",
        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "outAmount": "100000000",
        "otherAmountThreshold": "99000000",
        "swapMode": "ExactIn",
        "slippageBps": 50,
        "platformFee": None,
        "priceImpactPct": "0.01",
        "routePlan": [{"swapInfo": {"label": "Raydium"}}],
        "contextSlot": 123456789,
        "timeTaken": 0.123
    }
    
    # Test creation from dict
    quote = JupiterQuote.from_dict(quote_data)
    assert quote.input_mint == "So11111111111111111111111111111111111111112"
    assert quote.in_amount == 1000000000
    assert quote.out_amount == 100000000
    
    # Test serialization to dict
    serialized = quote.to_dict()
    assert serialized["inputMint"] == "So11111111111111111111111111111111111111112"
    assert serialized["inAmount"] == "1000000000"
    assert serialized["outAmount"] == "100000000"


@pytest.mark.asyncio
async def test_jupiter_route_creation():
    """Test JupiterRoute object creation."""
    route_data = {
        "inputMint": "So11111111111111111111111111111111111111112",
        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "inAmount": "1000000000",
        "outAmount": "100000000",
        "routePlan": [
            {"swapInfo": {"label": "Raydium"}},
            {"swapInfo": {"label": "Orca"}}
        ],
        "priceImpactPct": 0.5,
        "slippageBps": 50
    }
    
    route = JupiterRoute.from_dict(route_data)
    assert route.input_mint == "So11111111111111111111111111111111111111112"
    assert route.output_mint == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    assert route.amount_in == 1000000000
    assert route.amount_out == 100000000
    assert len(route.market_infos) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_client_session_management():
    """Test proper session management."""
    client = JupiterClient()
    
    # Should create session when needed
    await client._ensure_session()
    session1 = client.session
    assert session1 is not None
    assert not session1.closed
    
    # Should reuse existing session
    await client._ensure_session()
    session2 = client.session
    assert session1 is session2
    
    # Should handle session closure
    await client.close()
    assert client.session.closed
    
    # Should create new session after closure
    await client._ensure_session()
    session3 = client.session
    assert session3 is not session1
    assert not session3.closed
    
    await client.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])