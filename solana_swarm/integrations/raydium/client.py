"""
Raydium DEX Client for liquidity pools and swapping.
"""

import logging
import aiohttp
from typing import Dict, Any, List, Optional
from decimal import Decimal
from dataclasses import dataclass
from solana.rpc.api import Pubkey

from .types import RaydiumPool, RaydiumSwapParams
from ...core.exceptions import DEXError, RaydiumError

logger = logging.getLogger(__name__)

class RaydiumClient:
    """Client for Raydium DEX operations."""
    
    BASE_URL = "https://api.raydium.io/v2"
    PROGRAM_ID = PublicKey("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
    
    def __init__(self, solana_connection=None):
        """Initialize Raydium client."""
        self.solana_connection = solana_connection
        self.session = None
        self._pools_cache = {}
        self._cache_timestamp = 0
        
    async def _ensure_session(self):
        """Ensure HTTP session exists."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "Solana-Agent-Studio/1.0",
                    "Accept": "application/json"
                }
            )
    
    async def get_pools(self, mint_a: Optional[str] = None, mint_b: Optional[str] = None) -> List[RaydiumPool]:
        """Get available liquidity pools."""
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/main/pairs"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise RaydiumError(f"Failed to get pools: {response.status}")
                
                data = await response.json()
                pools = []
                
                for pool_data in data:
                    # Filter by mints if provided
                    if mint_a and mint_b:
                        pool_mints = [pool_data.get('baseMint'), pool_data.get('quoteMint')]
                        if mint_a not in pool_mints or mint_b not in pool_mints:
                            continue
                    
                    pool = RaydiumPool.from_dict(pool_data)
                    pools.append(pool)
                    
                    # Cache pool data
                    self._pools_cache[pool.id] = pool
                
                return pools
                
        except Exception as e:
            logger.error(f"Failed to get Raydium pools: {e}")
            raise RaydiumError(f"Pools fetch failed: {e}")
    
    async def get_pool_info(self, pool_id: str) -> RaydiumPool:
        """Get detailed pool information."""
        # Check cache first
        if pool_id in self._pools_cache:
            return self._pools_cache[pool_id]
        
        await self._ensure_session()
        
        try:
            url = f"{self.BASE_URL}/main/pool/{pool_id}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise RaydiumError(f"Failed to get pool info: {response.status}")
                
                data = await response.json()
                pool = RaydiumPool.from_dict(data)
                
                # Cache the pool
                self._pools_cache[pool_id] = pool
                
                return pool
                
        except Exception as e:
            logger.error(f"Failed to get pool info for {pool_id}: {e}")
            raise RaydiumError(f"Pool info fetch failed: {e}")
    
    async def calculate_swap(
        self,
        pool_id: str,
        input_mint: str,
        output_mint: str,
        amount_in: int,
        slippage_bps: int = 50
    ) -> Dict[str, Any]:
        """Calculate swap output amount."""
        try:
            pool = await self.get_pool_info(pool_id)
            
            # Determine direction
            is_base_to_quote = (input_mint == pool.base_mint)
            
            # Get reserves
            if is_base_to_quote:
                input_reserve = pool.base_reserve
                output_reserve = pool.quote_reserve
            else:
                input_reserve = pool.quote_reserve
                output_reserve = pool.base_reserve
            
            # Calculate output using constant product formula
            # x * y = k
            # (x + dx) * (y - dy) = k
            # dy = y - k/(x + dx)
            
            k = input_reserve * output_reserve
            amount_out_before_fee = output_reserve - (k / (input_reserve + amount_in))
            
            # Apply fee (0.25%)
            fee_rate = 0.0025
            amount_out = amount_out_before_fee * (1 - fee_rate)
            
            # Apply slippage
            min_amount_out = int(amount_out * (1 - slippage_bps / 10000))
            
            # Calculate price impact
            price_before = output_reserve / input_reserve
            price_after = (output_reserve - amount_out) / (input_reserve + amount_in)
            price_impact = abs((price_after - price_before) / price_before) * 100
            
            return {
                "pool_id": pool_id,
                "amount_in": amount_in,
                "amount_out": int(amount_out),
                "min_amount_out": min_amount_out,
                "price_impact": price_impact,
                "fee": int(amount_out_before_fee * fee_rate),
                "route": [pool_id]
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate swap: {e}")
            raise RaydiumError(f"Swap calculation failed: {e}")
    
    async def swap(
        self,
        params: RaydiumSwapParams,
        user_public_key: PublicKey
    ) -> Dict[str, Any]:
        """Execute token swap on Raydium."""
        try:
            if not self.solana_connection:
                raise RaydiumError("Solana connection required for swaps")
            
            # Calculate swap first
            calc_result = await self.calculate_swap(
                params.pool_id,
                params.input_mint,
                params.output_mint,
                params.amount_in,
                params.slippage_bps
            )
            
            # Build swap instruction
            # This would involve creating the actual Raydium swap instruction
            # For production, you would use the Raydium SDK or construct the instruction manually
            
            return {
                "status": "simulated",
                "calculation": calc_result,
                "message": "Swap instruction would be built and executed here"
            }
            
        except Exception as e:
            logger.error(f"Raydium swap failed: {e}")
            raise RaydiumError(f"Swap failed: {e}")
    
    async def get_price(
        self,
        input_mint: str,
        output_mint: str,
        amount: int = 1000000
    ) -> Dict[str, Any]:
        """Get price for a token pair."""
        try:
            # Find pools for the pair
            pools = await self.get_pools(input_mint, output_mint)
            
            if not pools:
                raise RaydiumError(f"No pools found for {input_mint}/{output_mint}")
            
            # Use the pool with highest liquidity
            best_pool = max(pools, key=lambda p: p.liquidity)
            
            # Calculate price
            calc_result = await self.calculate_swap(
                best_pool.id,
                input_mint,
                output_mint,
                amount,
                50
            )
            
            price = calc_result['amount_out'] / amount
            
            return {
                "price": price,
                "input_mint": input_mint,
                "output_mint": output_mint,
                "pool_id": best_pool.id,
                "liquidity": float(best_pool.liquidity)
            }
            
        except Exception as e:
            logger.error(f"Failed to get Raydium price: {e}")
            raise RaydiumError(f"Price fetch failed: {e}")
    
    async def get_liquidity_stats(self, pool_id: str) -> Dict[str, Any]:
        """Get liquidity statistics for a pool."""
        try:
            pool = await self.get_pool_info(pool_id)
            
            # Calculate various metrics
            total_liquidity = float(pool.liquidity)
            base_price = float(pool.quote_reserve / pool.base_reserve if pool.base_reserve > 0 else 0)
            
            # Calculate 24h APR (simplified)
            volume_24h = float(pool.volume_24h)
            fees_24h = volume_24h * 0.0025  # 0.25% fee
            apr_24h = (fees_24h * 365 / total_liquidity * 100) if total_liquidity > 0 else 0
            
            return {
                "pool_id": pool_id,
                "liquidity": total_liquidity,
                "volume_24h": volume_24h,
                "fees_24h": fees_24h,
                "apr_24h": apr_24h,
                "base_price": base_price,
                "base_reserve": float(pool.base_reserve),
                "quote_reserve": float(pool.quote_reserve)
            }
            
        except Exception as e:
            logger.error(f"Failed to get liquidity stats: {e}")
            raise RaydiumError(f"Stats fetch failed: {e}")
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()