"""
Production Market Data Manager
Real-time market data integration with comprehensive fallback systems.
"""

import asyncio
import aiohttp
import logging
import time
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import ccxt.async_support as ccxt
from pycoingecko import CoinGeckoAPI

from .exceptions import MarketDataError
from ..integrations.jupiter.client import JupiterClient

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Available market data sources."""
    JUPITER = "jupiter"
    COINGECKO = "coingecko"
    BINANCE = "binance"
    COINBASE = "coinbase"
    PYTH = "pyth"
    SWITCHBOARD = "switchboard"

@dataclass
class PriceData:
    """Standardized price data structure."""
    symbol: str
    price: Decimal
    volume_24h: Decimal
    change_24h: float
    market_cap: Optional[Decimal]
    timestamp: datetime
    source: DataSource
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "price": float(self.price),
            "volume_24h": float(self.volume_24h),
            "change_24h": self.change_24h,
            "market_cap": float(self.market_cap) if self.market_cap else None,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source.value,
            "confidence": self.confidence
        }

@dataclass
class DexData:
    """DEX-specific market data."""
    name: str
    tvl: Decimal
    volume_24h: Decimal
    volume_7d: Decimal
    fees_24h: Decimal
    pools_count: int
    timestamp: datetime
    source: str

class MarketDataManager:
    """Production market data manager with real-time capabilities."""
    
    # Token mappings for different data sources
    SOLANA_TOKENS = {
        "SOL": {
            "coingecko_id": "solana",
            "jupiter_mint": "So11111111111111111111111111111111111111112",
            "symbol": "SOL",
            "decimals": 9
        },
        "USDC": {
            "coingecko_id": "usd-coin",
            "jupiter_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "symbol": "USDC",
            "decimals": 6
        },
        "USDT": {
            "coingecko_id": "tether",
            "jupiter_mint": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
            "symbol": "USDT",
            "decimals": 6
        },
        "RAY": {
            "coingecko_id": "raydium",
            "jupiter_mint": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
            "symbol": "RAY",
            "decimals": 6
        },
        "ORCA": {
            "coingecko_id": "orca",
            "jupiter_mint": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
            "symbol": "ORCA",
            "decimals": 6
        }
    }
    
    def __init__(self, 
                 jupiter_client: Optional[JupiterClient] = None,
                 coingecko_api_key: Optional[str] = None,
                 enable_ccxt: bool = True):
        """Initialize market data manager."""
        if jupiter_client is None:
            try:
                from ..integrations.jupiter.client import JupiterClient
                self.jupiter_client = JupiterClient()
                logger.info("Initialized Jupiter client")
            except Exception as e:
                logger.warning(f"Failed to initialize Jupiter client: {e}")
                self.jupiter_client = None
        else:
            self.jupiter_client = jupiter_client
        self.coingecko_api_key = coingecko_api_key
        self.enable_ccxt = enable_ccxt
        
        # Initialize APIs
        self.coingecko = CoinGeckoAPI(api_key=coingecko_api_key) if coingecko_api_key else CoinGeckoAPI()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # CCXT exchanges
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        
        # Caching
        self.cache: Dict[str, tuple] = {}
        self.cache_ttl = 30  # 30 seconds for production
        
        # Rate limiting
        self.rate_limits = {
            DataSource.COINGECKO: {"calls": 0, "window_start": time.time(), "limit": 50},
            DataSource.JUPITER: {"calls": 0, "window_start": time.time(), "limit": 100},
        }
        
        # Data source priorities (higher number = higher priority)
        self.source_priorities = {
            DataSource.JUPITER: 100,  # Highest for Solana tokens
            DataSource.PYTH: 90,
            DataSource.SWITCHBOARD: 85,
            DataSource.BINANCE: 80,
            DataSource.COINBASE: 75,
            DataSource.COINGECKO: 70
        }
    
    async def initialize(self):
        """Initialize all data sources."""
        await self._ensure_session()
        
        if self.enable_ccxt:
            await self._initialize_ccxt_exchanges()
        
        logger.info("Market data manager initialized successfully")
    
    async def _ensure_session(self):
        """Ensure HTTP session exists."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30.0)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "Solana-Agent-Studio/1.0"
                }
            )
    
    async def _initialize_ccxt_exchanges(self):
        """Initialize CCXT exchanges for additional data sources."""
        try:
            # Initialize major exchanges (removed FTX as it's defunct)
            exchange_configs = {
                'binance': {'sandbox': False, 'enableRateLimit': True},
                'coinbase': {'sandbox': False, 'enableRateLimit': True},
                # Removed FTX - exchange is defunct
            }
            
            for exchange_name, config in exchange_configs.items():
                try:
                    exchange_class = getattr(ccxt, exchange_name)
                    exchange = exchange_class(config)
                    await exchange.load_markets()
                    self.exchanges[exchange_name] = exchange
                    logger.info(f"Initialized {exchange_name} exchange")
                except Exception as e:
                    logger.warning(f"Failed to initialize {exchange_name}: {e}")
        
        except Exception as e:
            logger.error(f"CCXT initialization failed: {e}")
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self.cache:
            return False
        _, timestamp = self.cache[key]
        return (datetime.now() - timestamp).total_seconds() < self.cache_ttl
    
    async def _rate_limit_check(self, source: DataSource):
        """Check and enforce rate limits."""
        if source not in self.rate_limits:
            return
        
        limit_info = self.rate_limits[source]
        current_time = time.time()
        
        # Reset window if needed
        if current_time - limit_info["window_start"] >= 60:
            limit_info["calls"] = 0
            limit_info["window_start"] = current_time
        
        # Check limit
        if limit_info["calls"] >= limit_info["limit"]:
            sleep_time = 60 - (current_time - limit_info["window_start"])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached for {source.value}, sleeping {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                limit_info["calls"] = 0
                limit_info["window_start"] = time.time()
        
        limit_info["calls"] += 1
    
    async def get_token_price(self, symbol: str,sources: Optional[List[DataSource]] = None) -> Dict[str, Any]: 
        """Get token price from multiple sources with fallback."""
        symbol = symbol.upper()
        cache_key = f"price_{symbol}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            cached_data = self.cache[cache_key][0]
            # Convert PriceData to dict if needed
            if hasattr(cached_data, 'to_dict'):
                return cached_data.to_dict()
            return cached_data
        
        # Determine sources to use
        if sources is None:
            sources = [DataSource.JUPITER, DataSource.COINGECKO, DataSource.BINANCE]
        
        # Sort sources by priority
        sources = sorted(sources, key=lambda s: self.source_priorities.get(s, 0), reverse=True)
        
        last_error = None
        
        for source in sources:
            try:
                price_data = await self._get_price_from_source(symbol, source)
                if price_data:
                    # Convert PriceData to dict before caching
                    price_dict = price_data.to_dict() if hasattr(price_data, 'to_dict') else {
                        'symbol': symbol,
                        'price': float(price_data.price),
                        'volume_24h': float(price_data.volume_24h),
                        'price_change_24h': price_data.change_24h,
                        'market_cap': float(price_data.market_cap) if price_data.market_cap else None,
                        'timestamp': price_data.timestamp.isoformat(),
                        'source': price_data.source.value,
                        'confidence': price_data.confidence
                    }
                    
                    # Cache as dict
                    self.cache[cache_key] = (price_dict, datetime.now())
                    return price_dict
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to get price from {source.value}: {e}")
                continue
        
        raise MarketDataError(f"All price sources failed for {symbol}. Last error: {last_error}")


    
    async def _get_price_from_source(self, symbol: str, source: DataSource) -> Optional[PriceData]:
        """Get price from a specific source."""
        await self._rate_limit_check(source)
        
        if source == DataSource.JUPITER and self.jupiter_client:
            return await self._get_price_jupiter(symbol)
        elif source == DataSource.COINGECKO:
            return await self._get_price_coingecko(symbol)
        elif source == DataSource.BINANCE and 'binance' in self.exchanges:
            return await self._get_price_binance(symbol)
        elif source == DataSource.COINBASE and 'coinbase' in self.exchanges:
            return await self._get_price_coinbase(symbol)
        elif source == DataSource.PYTH:
            return await self._get_price_pyth(symbol)
        
        return None
    
    
    async def _get_price_jupiter(self, symbol: str) -> Optional[PriceData]:
        """Get price from Jupiter aggregator."""
        try:
            if not self.jupiter_client:
                logger.debug("Jupiter client not available for pricing")
                return None
                
            if symbol not in self.SOLANA_TOKENS:
                return None
            
            token_info = self.SOLANA_TOKENS[symbol]
            
            # Get price against USDC
            usdc_mint = self.SOLANA_TOKENS["USDC"]["jupiter_mint"]
            token_mint = token_info["jupiter_mint"]
            
            # Use 1 token as base amount (accounting for decimals)
            base_amount = 10 ** token_info["decimals"]
            
            try:
                price_info = await self.jupiter_client.get_price(
                    input_mint=token_mint,
                    output_mint=usdc_mint,
                    amount=base_amount
                )
                
                actual_price = price_info["price"]
                
                return PriceData(
                    symbol=symbol,
                    price=Decimal(str(actual_price)),
                    volume_24h=Decimal(0),
                    change_24h=0.0,
                    market_cap=None,
                    timestamp=datetime.now(),
                    source=DataSource.JUPITER,
                    confidence=0.95
                )
            except Exception as e:
                logger.warning(f"Jupiter price fetch failed for {symbol}: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error in Jupiter price fetch for {symbol}: {e}")
            return None

    
    async def _get_price_coingecko(self, symbol: str) -> Optional[PriceData]:
        """Get price from CoinGecko."""
        try:
            if symbol not in self.SOLANA_TOKENS:
                return None
            
            token_info = self.SOLANA_TOKENS[symbol]
            coin_id = token_info["coingecko_id"]
            
            # Get coin data
            data = self.coingecko.get_coin_by_id(
                id=coin_id,
                localization=False,
                tickers=False,
                market_data=True,
                community_data=False,
                developer_data=False,
                sparkline=False
            )
            
            market_data = data["market_data"]
            
            return PriceData(
                symbol=symbol,
                price=Decimal(str(market_data["current_price"]["usd"])),
                volume_24h=Decimal(str(market_data["total_volume"]["usd"])),
                change_24h=market_data["price_change_percentage_24h"] or 0.0,
                market_cap=Decimal(str(market_data["market_cap"]["usd"])) if market_data["market_cap"]["usd"] else None,
                timestamp=datetime.now(),
                source=DataSource.COINGECKO,
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"CoinGecko price fetch failed for {symbol}: {e}")
            return None
    
    async def _get_price_binance(self, symbol: str) -> Optional[PriceData]:
        """Get price from Binance."""
        try:
            exchange = self.exchanges.get('binance')
            if not exchange:
                return None
            
            # Try different trading pairs
            pairs_to_try = [f"{symbol}/USDT", f"{symbol}/USDC", f"{symbol}/USD"]
            
            for pair in pairs_to_try:
                try:
                    ticker = await exchange.fetch_ticker(pair)
                    if ticker:
                        return PriceData(
                            symbol=symbol,
                            price=Decimal(str(ticker['last'])),
                            volume_24h=Decimal(str(ticker['quoteVolume'])),
                            change_24h=ticker['percentage'] or 0.0,
                            market_cap=None,
                            timestamp=datetime.fromtimestamp(ticker['timestamp'] / 1000),
                            source=DataSource.BINANCE,
                            confidence=0.85
                        )
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Binance price fetch failed for {symbol}: {e}")
            return None
    
    async def _get_price_coinbase(self, symbol: str) -> Optional[PriceData]:
        """Get price from Coinbase."""
        try:
            exchange = self.exchanges.get('coinbase')
            if not exchange:
                return None
            
            pairs_to_try = [f"{symbol}/USD", f"{symbol}/USDC"]
            
            for pair in pairs_to_try:
                try:
                    ticker = await exchange.fetch_ticker(pair)
                    if ticker:
                        return PriceData(
                            symbol=symbol,
                            price=Decimal(str(ticker['last'])),
                            volume_24h=Decimal(str(ticker['quoteVolume'])),
                            change_24h=ticker['percentage'] or 0.0,
                            market_cap=None,
                            timestamp=datetime.fromtimestamp(ticker['timestamp'] / 1000),
                            source=DataSource.COINBASE,
                            confidence=0.85
                        )
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Coinbase price fetch failed for {symbol}: {e}")
            return None
    
    async def _get_price_pyth(self, symbol: str) -> Optional[PriceData]:
        """Get price from Pyth Network oracle."""
        try:
            await self._ensure_session()
            
            # Pyth API endpoint
            url = "https://hermes.pyth.network/api/latest_price_feeds"
            params = {"ids": self._get_pyth_price_id(symbol)}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        price_feed = data[0]
                        price_data = price_feed["price"]
                        
                        # Convert from Pyth format
                        price = Decimal(price_data["price"]) * (Decimal(10) ** price_data["expo"])
                        
                        return PriceData(
                            symbol=symbol,
                            price=price,
                            volume_24h=Decimal(0),
                            change_24h=0.0,
                            market_cap=None,
                            timestamp=datetime.fromtimestamp(price_data["publish_time"]),
                            source=DataSource.PYTH,
                            confidence=0.92
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Pyth price fetch failed for {symbol}: {e}")
            return None
    
    def _get_pyth_price_id(self, symbol: str) -> str:
        """Get Pyth price feed ID for symbol."""
        # Pyth price feed IDs for major tokens
        pyth_ids = {
            "SOL": "0xef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d",
            "BTC": "0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43",
            "ETH": "0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace",
            "USDC": "0xeaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a",
        }
        return pyth_ids.get(symbol, "")
    
    async def get_dex_data(self, dex_name: str) -> DexData:
        """Get DEX-specific data."""
        cache_key = f"dex_{dex_name}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key][0]
        
        try:
            if dex_name.lower() == "raydium":
                dex_data = await self._get_raydium_data()
            elif dex_name.lower() == "orca":
                dex_data = await self._get_orca_data()
            elif dex_name.lower() == "jupiter":
                dex_data = await self._get_jupiter_data()
            else:
                raise MarketDataError(f"Unsupported DEX: {dex_name}")
            
            self.cache[cache_key] = (dex_data, datetime.now())
            return dex_data
            
        except Exception as e:
            logger.error(f"Failed to get DEX data for {dex_name}: {e}")
            raise MarketDataError(f"DEX data fetch failed: {e}")
    
    async def _get_raydium_data(self) -> DexData:
        """Get Raydium DEX data."""
        await self._ensure_session()
        
        try:
            # Raydium API endpoints
            stats_url = "https://api.raydium.io/v2/main/info"
            
            async with self.session.get(stats_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return DexData(
                        name="Raydium",
                        tvl=Decimal(str(data.get("tvl", 0))),
                        volume_24h=Decimal(str(data.get("volume24h", 0))),
                        volume_7d=Decimal(str(data.get("volume7d", 0))),
                        fees_24h=Decimal(str(data.get("fees24h", 0))),
                        pools_count=data.get("poolsCount", 0),
                        timestamp=datetime.now(),
                        source="raydium_api"
                    )
                else:
                    raise MarketDataError(f"Raydium API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Raydium data fetch failed: {e}")
            raise
    
    async def _get_orca_data(self) -> DexData:
        """Get Orca DEX data."""
        await self._ensure_session()
        
        try:
            # Use DeFiLlama for Orca data
            url = "https://api.llama.fi/protocol/orca"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Get latest TVL
                    tvl_data = data.get("tvl", [])
                    latest_tvl = tvl_data[-1]["totalLiquidityUSD"] if tvl_data else 0
                    
                    return DexData(
                        name="Orca",
                        tvl=Decimal(str(latest_tvl)),
                        volume_24h=Decimal(0),  # Would need separate API call
                        volume_7d=Decimal(0),
                        fees_24h=Decimal(0),
                        pools_count=0,
                        timestamp=datetime.now(),
                        source="defillama"
                    )
                else:
                    raise MarketDataError(f"DeFiLlama API error: {response.status}")
        
        except Exception as e:
            logger.error(f"Orca data fetch failed: {e}")
            raise
    
    
    async def _get_jupiter_data(self) -> DexData:
        """Get Jupiter aggregator data."""
        try:
            if not self.jupiter_client:
                raise MarketDataError("Jupiter client not available")
            
            # Get supported tokens count as a proxy for routes
            try:
                tokens = await self.jupiter_client.get_supported_tokens()
                token_count = len(tokens) if tokens else 0
            except Exception as e:
                logger.warning(f"Failed to get Jupiter token count: {e}")
                token_count = 0
            
            return DexData(
                name="Jupiter",
                tvl=Decimal(0),  # Aggregator doesn't have TVL
                volume_24h=Decimal(0),  # Would need specific API
                volume_7d=Decimal(0),
                fees_24h=Decimal(0),
                pools_count=token_count,
                timestamp=datetime.now(),
                source="jupiter_api"
            )
            
        except Exception as e:
            logger.error(f"Jupiter data fetch failed: {e}")
            raise MarketDataError(f"Jupiter data unavailable: {e}")


    
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get comprehensive market overview."""
        try:
            # Get major token prices
            major_tokens = ["SOL", "USDC", "RAY", "ORCA"]
            price_tasks = [self.get_token_price(token) for token in major_tokens]
            prices = await asyncio.gather(*price_tasks, return_exceptions=True)
            
            # Get DEX data
            dex_tasks = [
                self.get_dex_data("raydium"),
                self.get_dex_data("orca"),
                self.get_dex_data("jupiter")
            ]
            dex_data = await asyncio.gather(*dex_tasks, return_exceptions=True)
            
            # Format results
            token_prices = {}
            for token, price_data in zip(major_tokens, prices):
                if isinstance(price_data, PriceData):
                    token_prices[token] = price_data.to_dict()
                else:
                    token_prices[token] = {"error": str(price_data)}
            
            dex_info = {}
            dex_names = ["raydium", "orca", "jupiter"]
            for name, data in zip(dex_names, dex_data):
                if isinstance(data, DexData):
                    dex_info[name] = {
                        "tvl": float(data.tvl),
                        "volume_24h": float(data.volume_24h),
                        "pools_count": data.pools_count
                    }
                else:
                    dex_info[name] = {"error": str(data)}
            
            return {
                "timestamp": datetime.now().isoformat(),
                "tokens": token_prices,
                "dexes": dex_info,
                "total_ecosystem_tvl": sum(
                    float(data.tvl) for data in dex_data 
                    if isinstance(data, DexData)
                )
            }
            
        except Exception as e:
            logger.error(f"Market overview fetch failed: {e}")
            raise MarketDataError(f"Market overview failed: {e}")
    
    async def close(self):
        """Close all connections."""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
            
            for exchange in self.exchanges.values():
                await exchange.close()
            
            logger.info("Market data manager closed")
            
        except Exception as e:
            logger.error(f"Error closing market data manager: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return None