"""
Orca DEX type definitions.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from decimal import Decimal

@dataclass
class OrcaWhirlpool:
    """Orca Whirlpool (concentrated liquidity pool) information."""
    address: str
    token_a: str
    token_b: str
    token_a_decimal: int
    token_b_decimal: int
    tick_spacing: int
    fee_rate: int  # in hundredths of a bps
    liquidity: Decimal
    sqrt_price: int
    tick: int
    price: Decimal
    tvl: Decimal
    volume_24h: Decimal
    fee_apr: float
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrcaWhirlpool':
        """Create from API response data."""
        return cls(
            address=data['address'],
            token_a=data['tokenA'],
            token_b=data['tokenB'],
            token_a_decimal=data['tokenADecimal'],
            token_b_decimal=data['tokenBDecimal'],
            tick_spacing=data['tickSpacing'],
            fee_rate=data['feeRate'],
            liquidity=Decimal(str(data.get('liquidity', 0))),
            sqrt_price=data.get('sqrtPrice', 0),
            tick=data.get('tick', 0),
            price=Decimal(str(data.get('price', 0))),
            tvl=Decimal(str(data.get('tvl', 0))),
            volume_24h=Decimal(str(data.get('volume24h', 0))),
            fee_apr=float(data.get('feeApr', 0))
        )

@dataclass
class OrcaSwapParams:
    """Parameters for Orca swap."""
    whirlpool_address: str
    input_token: str
    output_token: str
    amount_in: int
    slippage_bps: int = 50
    a_to_b: bool = True
    user_public_key: Optional[str] = None
    
@dataclass
class OrcaPosition:
    """Concentrated liquidity position in Orca."""
    position_mint: str
    whirlpool: str
    tick_lower_index: int
    tick_upper_index: int
    liquidity: Decimal
    fee_growth_checkpoint_a: int
    fee_owed_a: int
    fee_growth_checkpoint_b: int
    fee_owed_b: int