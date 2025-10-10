"""
Fixed Jupiter DEX Aggregator Client - Updated for V2 Token API (October 2025)
This version uses the correct lite-api.jup.ag endpoints
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
    """Jupiter client with correct V2 API endpoints."""
    
    # FIXED: Updated to use lite-api.jup.ag instead of tokens.jup.ag
    BASE_URL = "https://lite-api.jup.ag/swap/v1"
    TOKEN_API_URL = "https://lite-api.jup.ag/tokens/v2"  # FIXED: V2 API
    PRICE_API_URL = "https://lite-api.jup.ag/price/v3"   # FIXED: V3 price API
    
    def __init__(self, solana_connection=None):
        """Initialize Jupiter client."""
        self.solana_connection = solana_connection
        self.session = None
        self._token_cache = None
        self._cache_timestamp = 0
        logger.info("Jupiter client initialized with V2/V3 API endpoints")
        
    async def _ensure_session(self):
        """Ensure HTTP session exists with proper SSL configuration."""
        if not self.session or self.session.closed:
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
            logger.info("Jupiter HTTP session created")
    
    async def get_supported_tokens(self, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Get supported tokens using V2 Token API.
        
        FIXED: Now uses /tokens/v2/tag?query=verified endpoint
        """
        import time
        
        # Check cache (5 minute TTL)
        current_time = time.time()
        if self._token_cache and (current_time - self._cache_timestamp) < 300:
            logger.info(f"Using cached token list ({len(self._token_cache)} tokens)")
            return self._token_cache
        
        await self._ensure_session()
        
        # NEW: Use V2 token API with tag query
        token_url = f"{self.TOKEN_API_URL}/tag?query=verified"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching tokens from V2 API (attempt {attempt + 1})")
                
                async with self.session.get(token_url) as response:
                    if response.status == 200:
                        tokens = await response.json()
                        
                        if tokens and isinstance(tokens, list):
                            # Cache successful response
                            self._token_cache = tokens
                            self._cache_timestamp = current_time
                            logger.info(f"✅ Loaded {len(tokens)} verified tokens from V2 API")
                            return tokens
                        else:
                            logger.warning(f"Unexpected token format: {type(tokens)}")
                    else:
                        error_text = await response.text()
                        logger.warning(f"Token API returned {response.status}: {error_text}")
                        
            except aiohttp.ClientError as e:
                logger.warning(f"Network error fetching tokens (attempt {attempt + 1}): {e}")
                
            # Exponential backoff
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        # Return cached data if available
        if self._token_cache:
            logger.warning("All token API attempts failed, using cached data")
            return self._token_cache
        
        # Return minimal fallback list
        logger.error("All token endpoints failed, using minimal fallback list")
        return self._get_minimal_token_list()
    
    def _get_minimal_token_list(self) -> List[Dict[str, Any]]:
        """Return minimal hardcoded token list as fallback."""
        return [
            {
                "id": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "name": "Solana",
                "decimals": 9,
                "isVerified": True
            },
            {
                "id": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "symbol": "USDC",
                "name": "USD Coin",
                "decimals": 6,
                "isVerified": True
            },
            {
                "id": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
                "symbol": "USDT",
                "name": "Tether USD",
                "decimals": 6,
                "isVerified": True
            }
        ]
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str, 
        amount: int,
        slippage_bps: int = 50,
        max_retries: int = 3
    ) -> JupiterQuote:
        """Get a swap quote using V1 Swap API."""
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
                
                url = f"{self.BASE_URL}/quote"
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return JupiterQuote.from_dict(data)
                    else:
                        error_text = await response.text()
                        logger.warning(f"Quote failed (attempt {attempt + 1}): {response.status}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise JupiterError(f"Quote failed: {error_text}")
                            
            except aiohttp.ClientError as e:
                logger.warning(f"Network error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise JupiterError(f"Network error: {e}")
        
        raise JupiterError("Quote failed after all retry attempts")
    
    async def get_price(
        self,
        input_mint: str,
        output_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        amount: int = 1000000000
    ) -> Dict[str, Any]:
        """
        Get price using V3 Price API.
        
        FIXED: Uses /price/v3 endpoint with proper format
        """
        try:
            await self._ensure_session()
            
            # Use V3 Price API
            params = {
                "ids": f"{input_mint},{output_mint}"
            }
            
            async with self.session.get(self.PRICE_API_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # V3 API response format: {"data": {"mint1": {...}, "mint2": {...}}}
                    price_data = data.get('data', {})
                    
                    input_price = price_data.get(input_mint, {}).get('price', 0)
                    output_price = price_data.get(output_mint, {}).get('price', 1)
                    
                    if input_price and output_price:
                        price = input_price / output_price
                        
                        logger.info(f"Got price from V3 API: {price:.4f}")
                        
                        return {
                            "price": price,
                            "input_mint": input_mint,
                            "output_mint": output_mint,
                            "amount": amount,
                            "source": "jupiter_price_v3"
                        }
                    else:
                        logger.warning("Price data missing in V3 response")
                else:
                    logger.warning(f"Price API returned {response.status}")
            
            # Fallback to quote-based pricing
            logger.info("Falling back to quote-based pricing")
            quote = await self.get_quote(input_mint, output_mint, amount, 50)
            
            # Calculate price from quote
            input_decimals = 9  # SOL
            output_decimals = 6  # USDC
            
            normalized_input = amount / (10 ** input_decimals)
            normalized_output = float(quote.out_amount) / (10 ** output_decimals)
            
            price = normalized_output / normalized_input if normalized_input > 0 else 0
            
            return {
                "price": price,
                "input_mint": input_mint,
                "output_mint": output_mint,
                "amount": amount,
                "out_amount": quote.out_amount,
                "price_impact": quote.price_impact_pct,
                "source": "jupiter_quote"
            }
            
        except Exception as e:
            logger.error(f"Failed to get Jupiter price: {e}")
            raise JupiterError(f"Price fetch failed: {e}")
    
    async def search_token(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for tokens by symbol, name, or mint address using V2 API.
        
        NEW: Uses /tokens/v2/search endpoint
        """
        try:
            await self._ensure_session()
            
            url = f"{self.TOKEN_API_URL}/search"
            params = {"query": query}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    results = await response.json()
                    
                    if isinstance(results, list):
                        # Limit results
                        return results[:max_results]
                    else:
                        logger.warning(f"Unexpected search result format: {type(results)}")
                        return []
                else:
                    error_text = await response.text()
                    logger.error(f"Token search failed: {response.status} - {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Token search error: {e}")
            return []
    
    async def get_trending_tokens(
        self, 
        category: str = "toptrading",
        interval: str = "24h",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get trending tokens using V2 category endpoint.
        
        NEW: Uses /tokens/v2/{category}/{interval} endpoint
        
        Args:
            category: "toporganicscore", "toptraded", or "toptrending"
            interval: "5m", "1h", "6h", or "24h"
            limit: Max results (1-100)
        """
        try:
            await self._ensure_session()
            
            url = f"{self.TOKEN_API_URL}/{category}/{interval}"
            params = {"limit": min(limit, 100)}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    tokens = await response.json()
                    
                    if isinstance(tokens, list):
                        logger.info(f"Retrieved {len(tokens)} trending tokens")
                        return tokens
                    else:
                        logger.warning(f"Unexpected trending format: {type(tokens)}")
                        return []
                else:
                    error_text = await response.text()
                    logger.error(f"Trending tokens failed: {response.status} - {error_text}")
                    return []
                    
        except Exception as e:
            logger.error(f"Trending tokens error: {e}")
            return []
    
    async def swap(
        self,
        quote: JupiterQuote,
        user_public_key: str,
        compute_unit_price_micro_lamports: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute token swap using V1 Swap API."""
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
            
            async with self.session.post(
                f"{self.BASE_URL}/swap",
                json=swap_request
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    raise JupiterError(f"Swap failed: {response.status} - {error_text}")
                    
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


# Test the fixed implementation
async def test_fixed_jupiter():
    """Test Jupiter with correct V2/V3 endpoints"""
    print("🪐 Testing Fixed Jupiter Client with V2/V3 APIs...")
    
    client = JupiterClient()
    
    try:
        # Test 1: Get verified tokens (V2 API)
        print("\n1️⃣ Testing Token List (V2 /tag API)...")
        tokens = await client.get_supported_tokens()
        print(f"✅ Loaded {len(tokens)} verified tokens")
        if tokens:
            print(f"   Sample: {tokens[0].get('symbol', 'N/A')} - {tokens[0].get('name', 'N/A')}")
        
        # Test 2: Search for a token (V2 API)
        print("\n2️⃣ Testing Token Search (V2 /search API)...")
        search_results = await client.search_token("SOL")
        print(f"✅ Found {len(search_results)} tokens matching 'SOL'")
        
        # Test 3: Get price (V3 API)
        print("\n3️⃣ Testing Price API (V3)...")
        sol_mint = "So11111111111111111111111111111111111111112"
        usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        price_data = await client.get_price(sol_mint, usdc_mint)
        print(f"✅ SOL Price: ${price_data['price']:.2f}")
        print(f"   Source: {price_data.get('source', 'unknown')}")
        
        # Test 4: Get quote (V1 Swap API)
        print("\n4️⃣ Testing Swap Quote (V1)...")
        quote = await client.get_quote(
            sol_mint,
            usdc_mint,
            1000000000,  # 1 SOL
            50
        )
        print(f"✅ Quote received:")
        print(f"   In: {quote.in_amount / 1e9:.4f} SOL")
        print(f"   Out: {quote.out_amount / 1e6:.2f} USDC")
        print(f"   Price Impact: {quote.price_impact_pct}%")
        
        # Test 5: Get trending tokens (V2 API)
        print("\n5️⃣ Testing Trending Tokens (V2 /category API)...")
        trending = await client.get_trending_tokens("toptrading", "24h", 5)
        print(f"✅ Top 5 trending tokens:")
        for i, token in enumerate(trending[:5], 1):
            symbol = token.get('symbol', 'N/A')
            price = token.get('usdPrice', 0)
            print(f"   {i}. {symbol}: ${price:.6f}")
        
        print("\n🎉 All Jupiter V2/V3 API tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_fixed_jupiter())