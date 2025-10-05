
import logging
import aiohttp
from aiohttp.resolver import ThreadedResolver
import asyncio
from typing import Dict, Any, List, Optional, Literal
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from .types import JupiterRoute, JupiterQuote
from ...core.exceptions import JupiterError

logger = logging.getLogger(__name__)


class TokenCategory(str, Enum):
    """Token category types for trending queries"""
    TOP_ORGANIC_SCORE = "toporganicscore"
    TOP_TRADED = "toptraded"
    TOP_TRENDING = "toptrending"


class TimeInterval(str, Enum):
    """Time intervals for category queries"""
    FIVE_MIN = "5m"
    ONE_HOUR = "1h"
    SIX_HOURS = "6h"
    TWENTY_FOUR_HOURS = "24h"


class TokenTag(str, Enum):
    """Token tag types"""
    LST = "lst"  # Liquid Staking Tokens
    VERIFIED = "verified"


@dataclass
class TokenInfo:
    """Comprehensive token information from V2 API"""
    id: str  # Mint address
    name: str
    symbol: str
    decimals: int
    icon: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    website: Optional[str] = None
    dev: Optional[str] = None
    circ_supply: Optional[float] = None
    total_supply: Optional[float] = None
    token_program: Optional[str] = None
    launchpad: Optional[str] = None
    partner_config: Optional[str] = None
    graduated_pool: Optional[str] = None
    graduated_at: Optional[str] = None
    holder_count: Optional[int] = None
    fdv: Optional[float] = None
    mcap: Optional[float] = None
    usd_price: Optional[float] = None
    price_block_id: Optional[int] = None
    liquidity: Optional[float] = None
    stats_5m: Optional[Dict[str, Any]] = None
    stats_1h: Optional[Dict[str, Any]] = None
    stats_6h: Optional[Dict[str, Any]] = None
    stats_24h: Optional[Dict[str, Any]] = None
    first_pool: Optional[Dict[str, Any]] = None
    audit: Optional[Dict[str, Any]] = None
    organic_score: Optional[float] = None
    organic_score_label: Optional[str] = None
    is_verified: Optional[bool] = None
    cexes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenInfo':
        """Create TokenInfo from API response"""
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            symbol=data.get('symbol', ''),
            decimals=data.get('decimals', 9),
            icon=data.get('icon'),
            twitter=data.get('twitter'),
            telegram=data.get('telegram'),
            website=data.get('website'),
            dev=data.get('dev'),
            circ_supply=data.get('circSupply'),
            total_supply=data.get('totalSupply'),
            token_program=data.get('tokenProgram'),
            launchpad=data.get('launchpad'),
            partner_config=data.get('partnerConfig'),
            graduated_pool=data.get('graduatedPool'),
            graduated_at=data.get('graduatedAt'),
            holder_count=data.get('holderCount'),
            fdv=data.get('fdv'),
            mcap=data.get('mcap'),
            usd_price=data.get('usdPrice'),
            price_block_id=data.get('priceBlockId'),
            liquidity=data.get('liquidity'),
            stats_5m=data.get('stats5m'),
            stats_1h=data.get('stats1h'),
            stats_6h=data.get('stats6h'),
            stats_24h=data.get('stats24h'),
            first_pool=data.get('firstPool'),
            audit=data.get('audit'),
            organic_score=data.get('organicScore'),
            organic_score_label=data.get('organicScoreLabel'),
            is_verified=data.get('isVerified'),
            cexes=data.get('cexes'),
            tags=data.get('tags'),
            updated_at=data.get('updatedAt')
        )

