"""
Raydium DEX type definitions.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from decimal import Decimal

@dataclass
class RaydiumPool:
    """Raydium liquidity pool information."""
    id: str
    base_mint: str
    quote_mint: str
    lp_mint: str
    base_decimal: int
    quote_decimal: int
    lp_decimal: int
    version: int
    program_id: str
    base_reserve: Decimal
    quote_reserve: Decimal
    lp_supply: Decimal
    liquidity: Decimal
    volume_24h: Decimal
    fee_rate: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RaydiumPool':
        """Create from API response data."""
        return cls(
            id=data['id'],
            base_mint=data['baseMint'],
            quote_mint=data['quoteMint'],
            lp_mint=data['lpMint'],
            base_decimal=data['baseDecimals'],
            quote_decimal=data['quoteDecimals'],
            lp_decimal=data['lpDecimals'],
            version=data.get('version', 4),
            program_id=data.get('programId', ''),
            base_reserve=Decimal(str(data.get('baseReserve', 0))),
            quote_reserve=Decimal(str(data.get('quoteReserve', 0))),
            lp_supply=Decimal(str(data.get('lpSupply', 0))),
            liquidity=Decimal(str(data.get('liquidity', 0))),
            volume_24h=Decimal(str(data.get('volume24h', 0))),
            fee_rate=float(data.get('feeRate', 0.0025))
        )

@dataclass
class RaydiumSwapParams:
    """Parameters for Raydium swap."""
    pool_id: str
    input_mint: str
    output_mint: str
    amount_in: int
    slippage_bps: int = 50
    user_public_key: Optional[str] = None