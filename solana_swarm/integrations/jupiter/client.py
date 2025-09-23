"""
Jupiter DEX Aggregator Client for optimal routing and swapping.
"""

import logging
import aiohttp
from typing import Dict, Any, List, Optional
from decimal import Decimal
from dataclasses import dataclass
from solana.rpc.api import Pubkey

from .types import JupiterRoute, JupiterQuote
from ...core.exceptions import DEXError, JupiterError

logger = logging.getLogger(__name__)

@dataclass
class JupiterSwapResult:
    """Result of a Jupiter swap operation."""
    signature: str
    input_amount: int
    output_amount: int
    price_impact: float
    fee: int
    slippage: float

class JupiterClient:
    """Client for Jupiter DEX aggregator."""
    
    BASE_URL = "https://quote-api.jup.ag/v6"
    
    def __init__(self, solana_connection=None):
        """Initialize Jupiter client."""
        self.solana_connection = solana_connection
        self.session = None
        
    async def _ensure_session(self):
        """Ensure HTTP session exists."""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "Solana-Agent-Studio/1.0"}
            )
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str, 
        amount: int,
        slippage_bps: int = 50
    ) -> JupiterQuote:
        """Get a quote for token swap."""
        await self._ensure_session()
        
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": slippage_bps
            }
            
            async with self.session.get(f"{self.BASE_URL}/quote", params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise JupiterError(f"Quote request failed: {response.status} - {error_text}")
                
                data = await response.json()
                return JupiterQuote.from_dict(data)
                
        except Exception as e:
            logger.error(f"Failed to get Jupiter quote: {e}")
            raise JupiterError(f"Quote failed: {e}")
    
    async def get_routes(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
        only_direct_routes: bool = False
    ) -> List[JupiterRoute]:
        """Get available routes for token swap."""
        await self._ensure_session()
        
        try:
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": slippage_bps,
                "onlyDirectRoutes": str(only_direct_routes).lower()
            }
            
            async with self.session.get(f"{self.BASE_URL}/quote", params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise JupiterError(f"Routes request failed: {response.status}")
                
                data = await response.json()
                routes = []
                
                # Jupiter v6 returns single best route in quote
                if 'routePlan' in data:
                    route = JupiterRoute(
                        input_mint=input_mint,
                        output_mint=output_mint,
                        amount_in=data['inAmount'],
                        amount_out=data['outAmount'],
                        market_infos=data['routePlan'],
                        price_impact_pct=float(data.get('priceImpactPct', 0)),
                        slippage_bps=slippage_bps
                    )
                    routes.append(route)
                
                return routes
                
        except Exception as e:
            logger.error(f"Failed to get Jupiter routes: {e}")
            raise JupiterError(f"Routes failed: {e}")
    
    async def swap(
        self,
        quote: JupiterQuote,
        user_public_key: PublicKey,
        compute_unit_price_micro_lamports: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute token swap using Jupiter."""
        await self._ensure_session()
        
        try:
            swap_request = {
                "quoteResponse": quote.to_dict(),
                "userPublicKey": str(user_public_key),
                "wrapAndUnwrapSol": True,
            }
            
            if compute_unit_price_micro_lamports:
                swap_request["computeUnitPriceMicroLamports"] = compute_unit_price_micro_lamports
            
            async with self.session.post(
                f"{self.BASE_URL}/swap",
                json=swap_request
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise JupiterError(f"Swap request failed: {response.status}")
                
                data = await response.json()
                return data
                
        except Exception as e:
            logger.error(f"Jupiter swap failed: {e}")
            raise JupiterError(f"Swap failed: {e}")
    
    async def get_price(
        self,
        input_mint: str,
        output_mint: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        amount: int = 1000000  # 1 token with 6 decimals
    ) -> Dict[str, Any]:
        """Get price for a token pair."""
        try:
            quote = await self.get_quote(input_mint, output_mint, amount)
            price = float(quote.out_amount) / float(quote.in_amount)
            
            return {
                "price": price,
                "input_mint": input_mint,
                "output_mint": output_mint,
                "amount": amount
            }
            
        except Exception as e:
            logger.error(f"Failed to get Jupiter price: {e}")
            raise JupiterError(f"Price fetch failed: {e}")
    
    async def get_supported_tokens(self) -> List[Dict[str, Any]]:
        """Get list of supported tokens."""
        await self._ensure_session()
        
        try:
            async with self.session.get("https://token.jup.ag/strict") as response:
                if response.status != 200:
                    raise JupiterError(f"Failed to get tokens: {response.status}")
                
                tokens = await response.json()
                return tokens
                
        except Exception as e:
            logger.error(f"Failed to get supported tokens: {e}")
            raise JupiterError(f"Token list failed: {e}")
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()