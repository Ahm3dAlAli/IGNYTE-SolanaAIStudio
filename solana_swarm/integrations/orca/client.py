"""
Orca DEX Client for concentrated liquidity and swapping.
"""

import logging
import aiohttp
from typing import Dict, Any, List, Optional
from decimal import Decimal
from solana.publickey import PublicKey

from .types import OrcaWhirlpool, OrcaSwapParams
from ...core.exceptions import DEXError, OrcaError

logger = logging.getLogger(__name__)

class OrcaClient:
    """Client for Orca DEX operations."""
    
    WHIRLPOOL_PROGRAM = PublicKey("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc")
    API_URL = "https://api.mainnet.orca.so/v1"
    
    def __init__(self, solana_connection=None):
        """Initialize Orca client."""
        self.solana_connection = solana_connection
        self.session = None
        self._whirlpools_cache = {}
        
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
    
    async def get_whirlpools(self, token_a: Optional[str] = None, token_b: Optional[str] = None) -> List[OrcaWhirlpool]:
        """Get available Whirlpools (concentrated liquidity pools)."""
        await self._ensure_session()
        
        try:
            url = f"{self.API_URL}/whirlpools/list"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise OrcaError(f"Failed to get whirlpools: {response.status}")
                
                data = await response.json()
                whirlpools = []
                
                for pool_data in data.get('whirlpools', []):
                    # Filter by tokens if provided
                    if token_a and token_b:
                        pool_tokens = [pool_data.get('tokenA'), pool_data.get('tokenB')]
                        if token_a not in pool_tokens or token_b not in pool_tokens:
                            continue
                    
                    whirlpool = OrcaWhirlpool.from_dict(pool_data)
                    whirlpools.append(whirlpool)
                    
                    # Cache whirlpool data
                    self._whirlpools_cache[whirlpool.address] = whirlpool
                
                return whirlpools
                
        except Exception as e:
            logger.error(f"Failed to get Orca whirlpools: {e}")
            raise OrcaError(f"Whirlpools fetch failed: {e}")
    
    async def get_whirlpool_info(self, whirlpool_address: str) -> OrcaWhirlpool:
        """Get detailed whirlpool information."""
        # Check cache first
        if whirlpool_address in self._whirlpools_cache:
            return self._whirlpools_cache[whirlpool_address]
        
        await self._ensure_session()
        
        try:
            url = f"{self.API_URL}/whirlpool/{whirlpool_address}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise OrcaError(f"Failed to get whirlpool info: {response.status}")
                
                data = await response.json()
                whirlpool = OrcaWhirlpool.from_dict(data)
                
                # Cache the whirlpool
                self._whirlpools_cache[whirlpool_address] = whirlpool
                
                return whirlpool
                
        except Exception as e:
            logger.error(f"Failed to get whirlpool info for {whirlpool_address}: {e}")
            raise OrcaError(f"Whirlpool info fetch failed: {e}")
    
    async def calculate_swap(
        self,
        whirlpool_address: str,
        input_token: str,
        output_token: str,
        amount_in: int,
        slippage_bps: int = 50
    ) -> Dict[str, Any]:
        """Calculate swap output amount with concentrated liquidity."""
        try:
            whirlpool = await self.get_whirlpool_info(whirlpool_address)
            
            # Determine direction
            is_a_to_b = (input_token == whirlpool.token_a)
            
            # Calculate based on current price and liquidity
            # This is a simplified calculation
            # Production would use the actual tick math
            
            current_price = float(whirlpool.price)
            liquidity = float(whirlpool.liquidity)
            
            if is_a_to_b:
                # Token A to Token B
                amount_out_ideal = amount_in * current_price
            else:
                # Token B to Token A
                amount_out_ideal = amount_in / current_price
            
            # Calculate price impact based on liquidity
            trade_size_ratio = amount_in / liquidity if liquidity > 0 else 0
            price_impact = trade_size_ratio * 100  # Simplified
            
            # Apply fees (variable based on fee tier)
            fee_rate = whirlpool.fee_rate / 1000000  # Convert from bps
            amount_out = amount_out_ideal * (1 - fee_rate)
            
            # Apply slippage
            min_amount_out = int(amount_out * (1 - slippage_bps / 10000))
            
            return {
                "whirlpool": whirlpool_address,
                "amount_in": amount_in,
                "amount_out": int(amount_out),
                "min_amount_out": min_amount_out,
                "price_impact": price_impact,
                "fee": int(amount_out_ideal * fee_rate),
                "current_price": current_price,
                "tick_spacing": whirlpool.tick_spacing
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate Orca swap: {e}")
            raise OrcaError(f"Swap calculation failed: {e}")
    
    async def get_quote(
        self,
        input_token: str,
        output_token: str,
        amount_in: int,
        slippage_bps: int = 50
    ) -> Dict[str, Any]:
        """Get best quote across all Orca pools."""
        try:
            # Find all relevant whirlpools
            whirlpools = await self.get_whirlpools(input_token, output_token)
            
            if not whirlpools:
                raise OrcaError(f"No pools found for {input_token}/{output_token}")
            
            # Get quotes from all pools
            quotes = []
            for whirlpool in whirlpools:
                try:
                    quote = await self.calculate_swap(
                        whirlpool.address,
                        input_token,
                        output_token,
                        amount_in,
                        slippage_bps
                    )
                    quotes.append(quote)
                except Exception as e:
                    logger.warning(f"Failed to get quote from pool {whirlpool.address}: {e}")
                    continue
            
            if not quotes:
                raise OrcaError("No valid quotes found")
            
            # Return best quote (highest output)
            best_quote = max(quotes, key=lambda q: q['amount_out'])
            
            return best_quote
            
        except Exception as e:
            logger.error(f"Failed to get Orca quote: {e}")
            raise OrcaError(f"Quote failed: {e}")
    
    async def get_concentrated_liquidity_positions(
        self,
        whirlpool_address: str,
        tick_lower: Optional[int] = None,
        tick_upper: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get concentrated liquidity positions in a whirlpool."""
        try:
            await self._ensure_session()
            
            url = f"{self.API_URL}/whirlpool/{whirlpool_address}/positions"
            params = {}
            if tick_lower is not None:
                params['tick_lower'] = tick_lower
            if tick_upper is not None:
                params['tick_upper'] = tick_upper
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    raise OrcaError(f"Failed to get positions: {response.status}")
                
                data = await response.json()
                positions = data.get('positions', [])
                
                return positions
                
        except Exception as e:
            logger.error(f"Failed to get CL positions: {e}")
            raise OrcaError(f"Positions fetch failed: {e}")
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()