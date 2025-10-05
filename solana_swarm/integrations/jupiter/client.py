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

from .types import JupiterRoute, JupiterQuote, TokenInfo, TokenTag, TokenCategory, TimeInterval
from ...core.exceptions import JupiterError

logger = logging.getLogger(__name__)
class JupiterClient:
    """Enhanced Jupiter client with complete V2/V3 API support"""
    
    # API Endpoints
    BASE_URL = "https://lite-api.jup.ag/swap/v1"
    TOKEN_API_URL = "https://lite-api.jup.ag/tokens/v2"
    PRICE_API_URL = "https://lite-api.jup.ag/price/v3"
    
    def __init__(self, solana_connection=None):
        """Initialize Jupiter client"""
        self.solana_connection = solana_connection
        self.session = None
        self._token_cache = {}
        self._cache_timestamp = {}
        self._cache_ttl = 300  # 5 minutes
        logger.info("Enhanced Jupiter client initialized with V2/V3 APIs")
        
    async def _ensure_session(self):
        """Ensure HTTP session exists with proper configuration"""
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
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        import time
        if cache_key not in self._cache_timestamp:
            return False
        return (time.time() - self._cache_timestamp[cache_key]) < self._cache_ttl
    
    # ============================================================================
    # TOKEN API V2 - SEARCH FUNCTIONALITY
    # ============================================================================
    
    async def search_token(
        self, 
        query: str, 
        max_retries: int = 3
    ) -> List[TokenInfo]:
        """
        Search for tokens by symbol, name, or mint address.
        
        Args:
            query: Search query (symbol, name, or comma-separated mint addresses)
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of TokenInfo objects matching the search
            
        Examples:
            - search_token("SOL") - Search by symbol
            - search_token("Solana") - Search by name
            - search_token("So111...112,EPjF...t1v") - Search multiple mints
        """
        await self._ensure_session()
        
        url = f"{self.TOKEN_API_URL}/search"
        params = {"query": query}
        
        for attempt in range(max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if isinstance(data, list):
                            tokens = [TokenInfo.from_dict(token) for token in data]
                            logger.info(f"Found {len(tokens)} tokens matching '{query}'")
                            return tokens
                        else:
                            logger.warning(f"Unexpected search result format: {type(data)}")
                            return []
                    else:
                        error_text = await response.text()
                        logger.warning(f"Search failed (attempt {attempt + 1}): {response.status}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise JupiterError(f"Search failed: {error_text}")
                            
            except aiohttp.ClientError as e:
                logger.warning(f"Network error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise JupiterError(f"Search failed: {e}")
        
        return []
    
    # ============================================================================
    # TOKEN API V2 - TAG FUNCTIONALITY
    # ============================================================================
    
    async def get_tokens_by_tag(
        self, 
        tag: TokenTag,
        use_cache: bool = True,
        max_retries: int = 3
    ) -> List[TokenInfo]:
        """
        Get all tokens belonging to a specific tag.
        
        Args:
            tag: Token tag (LST or VERIFIED)
            use_cache: Whether to use cached results
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of all tokens with the specified tag
            
        Examples:
            - get_tokens_by_tag(TokenTag.VERIFIED) - All verified tokens
            - get_tokens_by_tag(TokenTag.LST) - All liquid staking tokens
        """
        cache_key = f"tag_{tag.value}"
        
        # Check cache
        if use_cache and self._is_cache_valid(cache_key):
            logger.info(f"Using cached tokens for tag: {tag.value}")
            return self._token_cache[cache_key]
        
        await self._ensure_session()
        
        url = f"{self.TOKEN_API_URL}/tag"
        params = {"query": tag.value}
        
        for attempt in range(max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if isinstance(data, list):
                            tokens = [TokenInfo.from_dict(token) for token in data]
                            
                            # Cache results
                            import time
                            self._token_cache[cache_key] = tokens
                            self._cache_timestamp[cache_key] = time.time()
                            
                            logger.info(f"Retrieved {len(tokens)} tokens for tag: {tag.value}")
                            return tokens
                        else:
                            logger.warning(f"Unexpected tag result format: {type(data)}")
                            return []
                    else:
                        error_text = await response.text()
                        logger.warning(f"Tag query failed (attempt {attempt + 1}): {response.status}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise JupiterError(f"Tag query failed: {error_text}")
                            
            except aiohttp.ClientError as e:
                logger.warning(f"Network error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise JupiterError(f"Tag query failed: {e}")
        
        return []
    
    async def get_verified_tokens(self, use_cache: bool = True) -> List[TokenInfo]:
        """Convenience method to get all verified tokens"""
        return await self.get_tokens_by_tag(TokenTag.VERIFIED, use_cache)
    
    async def get_lst_tokens(self, use_cache: bool = True) -> List[TokenInfo]:
        """Convenience method to get all liquid staking tokens"""
        return await self.get_tokens_by_tag(TokenTag.LST, use_cache)
    
    # ============================================================================
    # TOKEN API V2 - CATEGORY FUNCTIONALITY
    # ============================================================================
    
    async def get_tokens_by_category(
        self,
        category: TokenCategory,
        interval: TimeInterval,
        limit: int = 50,
        max_retries: int = 3
    ) -> List[TokenInfo]:
        """
        Get top tokens by category and time interval.
        
        Args:
            category: Token category (toporganicscore, toptraded, toptrending)
            interval: Time interval (5m, 1h, 6h, 24h)
            limit: Maximum number of results (1-100, default 50)
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of top tokens for the specified category and interval
            
        Examples:
            - get_tokens_by_category(TokenCategory.TOP_TRENDING, TimeInterval.TWENTY_FOUR_HOURS)
            - get_tokens_by_category(TokenCategory.TOP_TRADED, TimeInterval.ONE_HOUR, limit=20)
        """
        await self._ensure_session()
        
        # Validate limit
        limit = max(1, min(100, limit))
        
        url = f"{self.TOKEN_API_URL}/{category.value}/{interval.value}"
        params = {"limit": limit}
        
        for attempt in range(max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if isinstance(data, list):
                            tokens = [TokenInfo.from_dict(token) for token in data]
                            logger.info(f"Retrieved {len(tokens)} {category.value} tokens for {interval.value}")
                            return tokens
                        else:
                            logger.warning(f"Unexpected category result format: {type(data)}")
                            return []
                    else:
                        error_text = await response.text()
                        logger.warning(f"Category query failed (attempt {attempt + 1}): {response.status}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise JupiterError(f"Category query failed: {error_text}")
                            
            except aiohttp.ClientError as e:
                logger.warning(f"Network error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise JupiterError(f"Category query failed: {e}")
        
        return []
    
    async def get_trending_tokens(
        self,
        interval: TimeInterval = TimeInterval.TWENTY_FOUR_HOURS,
        limit: int = 50
    ) -> List[TokenInfo]:
        """Convenience method to get trending tokens"""
        return await self.get_tokens_by_category(
            TokenCategory.TOP_TRENDING,
            interval,
            limit
        )
    
    async def get_top_traded_tokens(
        self,
        interval: TimeInterval = TimeInterval.TWENTY_FOUR_HOURS,
        limit: int = 50
    ) -> List[TokenInfo]:
        """Convenience method to get most traded tokens"""
        return await self.get_tokens_by_category(
            TokenCategory.TOP_TRADED,
            interval,
            limit
        )
    
    async def get_top_organic_score_tokens(
        self,
        interval: TimeInterval = TimeInterval.TWENTY_FOUR_HOURS,
        limit: int = 50
    ) -> List[TokenInfo]:
        """Convenience method to get tokens with highest organic score"""
        return await self.get_tokens_by_category(
            TokenCategory.TOP_ORGANIC_SCORE,
            interval,
            limit
        )
    
    # ============================================================================
    # TOKEN API V2 - RECENT TOKENS
    # ============================================================================
    
    async def get_recent_tokens(self, max_retries: int = 3) -> List[TokenInfo]:
        """
        Get recently created tokens (tokens with newly created pools).
        
        Returns:
            List of up to 30 recently created tokens
        """
        await self._ensure_session()
        
        url = f"{self.TOKEN_API_URL}/recent"
        
        for attempt in range(max_retries):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if isinstance(data, list):
                            tokens = [TokenInfo.from_dict(token) for token in data]
                            logger.info(f"Retrieved {len(tokens)} recent tokens")
                            return tokens
                        else:
                            logger.warning(f"Unexpected recent tokens format: {type(data)}")
                            return []
                    else:
                        error_text = await response.text()
                        logger.warning(f"Recent tokens query failed (attempt {attempt + 1}): {response.status}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise JupiterError(f"Recent tokens query failed: {error_text}")
                            
            except aiohttp.ClientError as e:
                logger.warning(f"Network error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise JupiterError(f"Recent tokens query failed: {e}")
        
        return []
    
    # ============================================================================
    # PRICE API V3
    # ============================================================================
    
    async def get_token_prices(
        self,
        token_ids: List[str],
        max_retries: int = 3
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get prices for multiple tokens using V3 Price API.
        
        Args:
            token_ids: List of token mint addresses
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary mapping mint addresses to price data
            
        Example:
            prices = await client.get_token_prices([
                "So11111111111111111111111111111111111111112",  # SOL
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC
            ])
        """
        await self._ensure_session()
        
        # Join token IDs with commas
        ids_param = ",".join(token_ids)
        
        params = {"ids": ids_param}
        
        for attempt in range(max_retries):
            try:
                async with self.session.get(self.PRICE_API_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # V3 API response format: {"data": {"mint1": {...}, "mint2": {...}}}
                        price_data = data.get('data', {})
                        
                        logger.info(f"Retrieved prices for {len(price_data)} tokens")
                        return price_data
                    else:
                        error_text = await response.text()
                        logger.warning(f"Price API failed (attempt {attempt + 1}): {response.status}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise JupiterError(f"Price API failed: {error_text}")
                            
            except aiohttp.ClientError as e:
                logger.warning(f"Network error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    raise JupiterError(f"Price API failed: {e}")
        
        return {}
    
    async def get_price(
        self,
        input_mint: str,
        output_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        amount: int = 1000000000
    ) -> Dict[str, Any]:
        """
        Get price for a token pair using V3 Price API with quote fallback.
        
        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address (default: USDC)
            amount: Amount in base units (default: 1 token)
            
        Returns:
            Dictionary with price information
        """
        try:
            # Try V3 Price API first
            price_data = await self.get_token_prices([input_mint, output_mint])
            
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
                    "input_price_usd": input_price,
                    "output_price_usd": output_price,
                    "source": "jupiter_price_v3"
                }
            
            # Fallback to quote-based pricing
            logger.info("Falling back to quote-based pricing")
            quote = await self.get_quote(input_mint, output_mint, amount, 50)
            
            # Calculate price from quote
            input_decimals = 9  # Default SOL
            output_decimals = 6  # Default USDC
            
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
    
    # ============================================================================
    # SWAP API V1 (EXISTING FUNCTIONALITY)
    # ============================================================================
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
        max_retries: int = 3
    ) -> JupiterQuote:
        """Get a swap quote using V1 Swap API"""
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
    
    async def swap(
        self,
        quote: JupiterQuote,
        user_public_key: str,
        compute_unit_price_micro_lamports: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute token swap using V1 Swap API"""
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
    
    # ============================================================================
    # LEGACY SUPPORT (Deprecated but maintained for compatibility)
    # ============================================================================
    
    async def get_supported_tokens(self, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Legacy method - Get supported tokens.
        Uses V2 verified tokens endpoint for compatibility.
        """
        tokens = await self.get_verified_tokens(use_cache=True)
        
        # Convert to legacy format
        return [
            {
                "id": token.id,
                "symbol": token.symbol,
                "name": token.name,
                "decimals": token.decimals,
                "isVerified": token.is_verified or True
            }
            for token in tokens
        ]
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    async def get_token_info(self, mint_address: str) -> Optional[TokenInfo]:
        """
        Get detailed information for a single token.
        
        Args:
            mint_address: Token mint address
            
        Returns:
            TokenInfo object or None if not found
        """
        results = await self.search_token(mint_address)
        
        if results and len(results) > 0:
            return results[0]
        
        return None
    
    async def get_market_overview(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get a comprehensive market overview.
        
        Returns:
            Dictionary with trending, top traded, and recent tokens
        """
        try:
            # Fetch multiple datasets concurrently
            trending, top_traded, recent = await asyncio.gather(
                self.get_trending_tokens(TimeInterval.TWENTY_FOUR_HOURS, limit),
                self.get_top_traded_tokens(TimeInterval.TWENTY_FOUR_HOURS, limit),
                self.get_recent_tokens(),
                return_exceptions=True
            )
            
            return {
                "trending": trending if not isinstance(trending, Exception) else [],
                "top_traded": top_traded if not isinstance(top_traded, Exception) else [],
                "recent": recent if not isinstance(recent, Exception) else [],
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get market overview: {e}")
            return {
                "trending": [],
                "top_traded": [],
                "recent": [],
                "error": str(e)
            }
    
    async def close(self):
        """Close HTTP session properly"""
        if self.session and not self.session.closed:
            await self.session.close()
            await asyncio.sleep(0.1)
            logger.info("Jupiter client session closed")

