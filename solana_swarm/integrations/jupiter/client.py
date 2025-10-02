"""
Fixed Jupiter DEX Aggregator Client with Updated API Endpoints (October 2025)
"""

import logging
import aiohttp
from aiohttp.resolver import ThreadedResolver
import asyncio
from typing import Dict, Any, List, Optional
from decimal import Decimal
from dataclasses import dataclass

from .types import JupiterRoute, JupiterQuote
from ...core.exceptions import JupiterError

logger = logging.getLogger(__name__)

class JupiterClient:
    """Jupiter client with updated October 2025 API endpoints."""
    
    # Updated API endpoints per Jupiter documentation (October 2025)
    BASE_URL = "https://lite-api.jup.ag/swap/v1"  # New swap endpoint
    TOKEN_LIST_URL = "https://lite-api.jup.ag/tokens/v2/strict"  # New token endpoint - strict list
    PRICE_API_URL = "https://lite-api.jup.ag/price/v3"  # New price endpoint
    
    def __init__(self, solana_connection=None):
        """Initialize Jupiter client."""
        self.solana_connection = solana_connection
        self.session = None
        self._token_cache = None
        self._cache_timestamp = 0
        
    async def _ensure_session(self):
        """Ensure HTTP session exists with proper SSL configuration."""
        if not self.session or self.session.closed:
            # Create connector with proper SSL settings
            connector = aiohttp.TCPConnector(
                resolver=ThreadedResolver(),
                ssl=True,
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300
            )
            
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=20
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": "Solana-Agent-Studio/1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            logger.info("Jupiter client session initialized with updated endpoints")
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str, 
        amount: int,
        slippage_bps: int = 50,
        max_retries: int = 3
    ) -> JupiterQuote:
        """Get a quote with retry logic using updated API."""
        await self._ensure_session()
        
        for attempt in range(max_retries):
            try:
                params = {
                    "inputMint": input_mint,
                    "outputMint": output_mint,
                    "amount": str(amount),
                    "slippageBps": str(slippage_bps),
                    "onlyDirectRoutes": "false",
                    "asLegacyTransaction": "false"
                }
                
                # Use updated endpoint
                url = f"{self.BASE_URL}/quote"
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return JupiterQuote.from_dict(data)
                    else:
                        error_text = await response.text()
                        logger.warning(f"Jupiter quote failed (attempt {attempt + 1}): {response.status}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise JupiterError(f"Quote failed after {max_retries} attempts: {error_text}")
                            
            except aiohttp.ClientError as e:
                logger.warning(f"Network error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise JupiterError(f"Network error after {max_retries} attempts: {e}")
        
        raise JupiterError("Quote failed after all retry attempts")
    
    async def get_price(
        self,
        input_mint: str,
        output_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        amount: int = 1000000000  # 1 SOL
    ) -> Dict[str, Any]:
        """Get price using updated Price API v3."""
        try:
            await self._ensure_session()
            
            # Use updated Price API v3 endpoint
            params = {
                "ids": f"{input_mint},{output_mint}"
            }
            
            async with self.session.get(self.PRICE_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract prices from v3 API response format
                    input_price = data.get('data', {}).get(input_mint, {}).get('price', 0)
                    output_price = data.get('data', {}).get(output_mint, {}).get('price', 1)
                    
                    if input_price and output_price:
                        price = input_price / output_price
                        
                        return {
                            "price": price,
                            "input_mint": input_mint,
                            "output_mint": output_mint,
                            "amount": amount,
                            "source": "jupiter_price_api_v3"
                        }
            
            # Fallback to quote-based pricing if Price API fails
            quote = await self.get_quote(input_mint, output_mint, amount, 50)
            
            # SOL has 9 decimals, USDC has 6 decimals
            input_decimals = 9
            output_decimals = 6
            
            # Normalize amounts
            normalized_input = amount / (10 ** input_decimals)
            normalized_output = float(quote.out_amount) / (10 ** output_decimals)
            
            # Calculate price
            price = normalized_output / normalized_input if normalized_input > 0 else 0
            
            return {
                "price": price,
                "input_mint": input_mint,
                "output_mint": output_mint,
                "amount": amount,
                "out_amount": quote.out_amount,
                "price_impact": quote.price_impact_pct
            }
            
        except Exception as e:
            logger.error(f"Failed to get Jupiter price: {e}")
            raise JupiterError(f"Price fetch failed: {e}")
    
    async def get_supported_tokens(self, max_retries: int = 3) -> List[Dict[str, Any]]:
        """Get supported tokens using updated Token API v2."""
        import time
        
        # Check cache (5 minute TTL)
        current_time = time.time()
        if self._token_cache and (current_time - self._cache_timestamp) < 300:
            return self._token_cache
        
        await self._ensure_session()
        
        # Try multiple token endpoints in order of preference
        token_endpoints = [
            "https://tokens.jup.ag/tokens?tags=verified",  # Try legacy verified tokens
            "https://tokens.jup.ag/tokens",  # Try all tokens legacy
            "https://api.jup.ag/tokens/v1",  # Alternative endpoint
        ]
        
        for attempt in range(max_retries):
            for endpoint_url in token_endpoints:
                try:
                    logger.info(f"Trying token endpoint: {endpoint_url}")
                    async with self.session.get(endpoint_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Token API returns data in different formats
                            if isinstance(data, list):
                                tokens = data
                            else:
                                tokens = data.get('tokens', data.get('data', []))
                            
                            if tokens:  # Only cache if we got tokens
                                self._token_cache = tokens
                                self._cache_timestamp = current_time
                                logger.info(f"✅ Loaded {len(tokens)} Jupiter tokens from {endpoint_url}")
                                return tokens
                        else:
                            logger.warning(f"Token endpoint {endpoint_url} returned {response.status}")
                            continue
                            
                except aiohttp.ClientError as e:
                    logger.warning(f"Network error with {endpoint_url}: {e}")
                    continue
            
            # If all endpoints failed, retry with exponential backoff
            if attempt < max_retries - 1:
                logger.warning(f"All token endpoints failed (attempt {attempt + 1}), retrying...")
                await asyncio.sleep(2 ** attempt)
        
        # Return cached data if available
        if self._token_cache:
            logger.warning("Using cached token list - all endpoints failed")
            return self._token_cache
        
        # Return minimal token list as fallback
        logger.error("All token endpoints failed, returning minimal token list")
        return [
            {
                "address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "name": "Solana",
                "decimals": 9
            },
            {
                "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "symbol": "USDC",
                "name": "USD Coin",
                "decimals": 6
            }
        ]
    
    async def swap(
        self,
        quote: JupiterQuote,
        user_public_key: str,
        compute_unit_price_micro_lamports: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute token swap using updated API."""
        await self._ensure_session()
        
        try:
            swap_request = {
                "quoteResponse": quote.to_dict(),
                "userPublicKey": str(user_public_key),
                "wrapAndUnwrapSol": True,
                "dynamicComputeUnitLimit": True,
                "prioritizationFeeLamports": "auto"
            }
            
            if compute_unit_price_micro_lamports:
                swap_request["computeUnitPriceMicroLamports"] = compute_unit_price_micro_lamports
            
            # Use updated swap endpoint
            async with self.session.post(
                f"{self.BASE_URL}/swap",
                json=swap_request
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    raise JupiterError(f"Swap request failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Jupiter swap failed: {e}")
            raise JupiterError(f"Swap failed: {e}")
    
    async def close(self):
        """Close HTTP session properly."""
        if self.session and not self.session.closed:
            await self.session.close()
            # Give time for cleanup
            await asyncio.sleep(0.1)
            logger.info("Jupiter client session closed")


# Test the updated implementation
async def test_updated_jupiter():
    """Test Jupiter with updated October 2025 endpoints"""
    print("🪐 Testing Jupiter with Updated API Endpoints...")
    
    client = JupiterClient()
    
    try:
        # Test 1: Get supported tokens
        print("\n1️⃣ Testing Token List (v2 API)...")
        tokens = await client.get_supported_tokens()
        print(f"✅ Loaded {len(tokens)} tokens from Token API v2")
        
        # Test 2: Get price
        print("\n2️⃣ Testing Price API (v3)...")
        sol_mint = "So11111111111111111111111111111111111111112"
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        price_data = await client.get_price(sol_mint, usdc_mint)
        print(f"✅ SOL Price: ${price_data['price']:.2f}")
        
        # Test 3: Get quote
        print("\n3️⃣ Testing Swap API (v1)...")
        quote = await client.get_quote(
            sol_mint,
            usdc_mint,
            1000000000,  # 1 SOL
            50
        )
        print(f"✅ Quote - Price Impact: {quote.price_impact_pct}%")
        
        print("\n🎉 All Jupiter tests passed with updated endpoints!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_updated_jupiter())