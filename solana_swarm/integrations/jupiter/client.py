"""
Fixed Jupiter DEX Aggregator Client
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
    """Fixed Jupiter client with proper SSL handling."""
    
    # Correct current API endpoints
    BASE_URL = "https://quote-api.jup.ag/v6"
    TOKEN_LIST_URL = "https://tokens.jup.ag/tokens?tags=verified"  # Fixed: tokens (with 's')
    
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
                ssl=True,  # Enable SSL
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
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "Solana-Agent-Studio/1.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            logger.info("Jupiter client session initialized")
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str, 
        amount: int,
        slippage_bps: int = 50,
        max_retries: int = 3
    ) -> JupiterQuote:
        """Get a quote with retry logic."""
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
                        logger.warning(f"Jupiter quote failed (attempt {attempt + 1}): {response.status}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
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
        """Get price with proper decimal handling."""
        try:
            quote = await self.get_quote(input_mint, output_mint, amount)
            
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
        """Get supported tokens with caching and retry."""
        import time
        
        # Check cache (5 minute TTL)
        current_time = time.time()
        if self._token_cache and (current_time - self._cache_timestamp) < 300:
            return self._token_cache
        
        await self._ensure_session()
        
        for attempt in range(max_retries):
            try:
                async with self.session.get(self.TOKEN_LIST_URL) as response:
                    if response.status == 200:
                        tokens = await response.json()
                        self._token_cache = tokens
                        self._cache_timestamp = current_time
                        logger.info(f"Loaded {len(tokens)} Jupiter tokens")
                        return tokens
                    else:
                        logger.warning(f"Token list fetch failed (attempt {attempt + 1}): {response.status}")
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            raise JupiterError(f"Token list fetch failed: {response.status}")
                            
            except aiohttp.ClientError as e:
                logger.warning(f"Network error fetching tokens (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    # Return cached data if available
                    if self._token_cache:
                        logger.warning("Using cached token list due to network error")
                        return self._token_cache
                    raise JupiterError(f"Token list fetch failed: {e}")
        
        raise JupiterError("Failed to get token list after all retries")
    
    async def swap(
        self,
        quote: JupiterQuote,
        user_public_key: str,
        compute_unit_price_micro_lamports: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute token swap (requires transaction signing)."""
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