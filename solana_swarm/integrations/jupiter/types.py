"""
Jupiter DEX aggregator type definitions.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class JupiterRoute:
    """Jupiter swap route information."""
    input_mint: str
    output_mint: str
    amount_in: int
    amount_out: int
    market_infos: List[Dict[str, Any]]
    price_impact_pct: float
    slippage_bps: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JupiterRoute':
        """Create from API response data."""
        return cls(
            input_mint=data['inputMint'],
            output_mint=data['outputMint'],
            amount_in=int(data['inAmount']),
            amount_out=int(data['outAmount']),
            market_infos=data.get('routePlan', []),
            price_impact_pct=float(data.get('priceImpactPct', 0)),
            slippage_bps=data.get('slippageBps', 50)
        )

@dataclass 
class JupiterQuote:
    """Jupiter swap quote."""
    input_mint: str
    in_amount: int
    output_mint: str
    out_amount: int
    other_amount_threshold: int
    swap_mode: str
    slippage_bps: int
    platform_fee: Optional[Dict[str, Any]]
    price_impact_pct: str
    route_plan: List[Dict[str, Any]]
    context_slot: int
    time_taken: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JupiterQuote':
        """Create from API response data."""
        return cls(
            input_mint=data['inputMint'],
            in_amount=int(data['inAmount']),
            output_mint=data['outputMint'],
            out_amount=int(data['outAmount']),
            other_amount_threshold=int(data['otherAmountThreshold']),
            swap_mode=data['swapMode'],
            slippage_bps=data['slippageBps'],
            platform_fee=data.get('platformFee'),
            price_impact_pct=data['priceImpactPct'],
            route_plan=data['routePlan'],
            context_slot=data['contextSlot'],
            time_taken=data['timeTaken']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        return {
            'inputMint': self.input_mint,
            'inAmount': str(self.in_amount),
            'outputMint': self.output_mint,
            'outAmount': str(self.out_amount),
            'otherAmountThreshold': str(self.other_amount_threshold),
            'swapMode': self.swap_mode,
            'slippageBps': self.slippage_bps,
            'platformFee': self.platform_fee,
            'priceImpactPct': self.price_impact_pct,
            'routePlan': self.route_plan,
            'contextSlot': self.context_slot,
            'timeTaken': self.time_taken
        }