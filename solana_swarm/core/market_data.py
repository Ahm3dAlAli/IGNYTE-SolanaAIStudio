"""
Market Data Manager for Solana Ecosystem
Integrates with CoinGecko, Jupiter, and other Solana-specific data sources
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MarketDataManager:
    """Manages market data integration for Solana ecosystem."""
    
    # Solana token mappings
    SOLANA_TOKENS = {
        "sol": "solana",
        "usdc": "usd-coin",
        "usdt": "tether", 
        "ray": "raydium",
        "orca": "orca",
        "mngo": "mango-markets",
        "srm": "serum",
        "ftt": "ftx-token",
        "cope": "cope"
    }
    
    # Solana mint addresses
    MINT_ADDRESSES = {
        "SOL": "So11111111111111111111111111111111111111112",
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE"
    }
    
    def __init__(self):
        """Initialize market data manager."""
        self.api_url = "https://api.coingecko.com/api/v3"
        self.jupiter_api = "https://price.jup.ag/v4"
        self.session = None
        
        # Enhanced caching for Solana
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.rate_limit_delay = 1.0
        self.last_request_time = 0.0
        self.max_retries = 3
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return None
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid."""
        if key not in self.cache:
            return False
        data, timestamp = self.cache[key]
        return datetime.now() - timestamp < timedelta(seconds=self.cache_ttl)
    
    async def _rate_limit(self):
        """Rate limiting for API calls."""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    async def get_token_price(self, token: str = "sol") -> Dict[str, Any]:
        """Get current token price from multiple sources."""
        try:
            token_id = self.SOLANA_TOKENS.get(token.lower(), token.lower())
            cache_key = f"price_{token_id}"
            
            if self._is_cache_valid(cache_key):
                logger.info("Using cached price data")
                return self.cache[cache_key][0]
            
            await self._ensure_session()
            await self._rate_limit()
            
            # Try Jupiter API first for Solana tokens
            if token.upper() in self.MINT_ADDRESSES:
                try:
                    jupiter_price = await self._get_jupiter_price(token)
                    if jupiter_price:
                        self.cache[cache_key] = (jupiter_price, datetime.now())
                        return jupiter_price
                except Exception as e:
                    logger.warning(f"Jupiter API failed, falling back to CoinGecko: {e}")
            
            # Fallback to CoinGecko
            async with self.session.get(
                f"{self.api_url}/coins/{token_id}"
            ) as response:
                if response.status == 429:
                    logger.warning("Rate limit hit, using cached data if available")
                    if cache_key in self.cache:
                        return self.cache[cache_key][0]
                    
                    # Return estimated data
                    return self._get_estimated_price(token)
                
                if response.status != 200:
                    raise Exception(f"API error: {response.status}")
                
                data = await response.json()
                if not data or "market_data" not in data:
                    raise Exception(f"No data found for token: {token_id}")
                
                market_data = data["market_data"]
                
                result = {
                    "price": market_data["current_price"].get("usd", 0),
                    "volume_24h": market_data["total_volume"].get("usd", 0),
                    "market_cap": market_data["market_cap"].get("usd", 0),
                    "price_change_24h": market_data["price_change_percentage_24h"],
                    "last_updated": market_data["last_updated"],
                    "confidence": 90.0,
                    "source": "coingecko"
                }
                
                self.cache[cache_key] = (result, datetime.now())
                return result
                
        except Exception as e:
            logger.error(f"Error fetching price data: {str(e)}")
            
            # Fallback to cached data
            if cache_key in self.cache:
                logger.warning("Using cached data due to error")
                return self.cache[cache_key][0]
            
            return self._get_estimated_price(token)
    
    async def _get_jupiter_price(self, token: str) -> Optional[Dict[str, Any]]:
        """Get price from Jupiter aggregator."""
        try:
            mint_address = self.MINT_ADDRESSES.get(token.upper())
            if not mint_address:
                return None
                
            async with self.session.get(
                f"{self.jupiter_api}/price?ids={mint_address}"
            ) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                if "data" not in data or mint_address not in data["data"]:
                    return None
                
                price_data = data["data"][mint_address]
                
                return {
                    "price": price_data["price"],
                    "volume_24h": 0,  # Jupiter doesn't provide volume
                    "market_cap": 0,
                    "price_change_24h": 0,
                    "last_updated": datetime.now().isoformat(),
                    "confidence": 95.0,
                    "source": "jupiter",
                    "mint_address": mint_address
                }
                
        except Exception as e:
            logger.error(f"Jupiter API error: {e}")
            return None
    
    def _get_estimated_price(self, token: str) -> Dict[str, Any]:
        """Get estimated price for fallback."""
        estimated_prices = {
            "sol": 100.0,
            "usdc": 1.0,
            "usdt": 1.0,
            "ray": 2.5,
            "orca": 3.5
        }
        
        price = estimated_prices.get(token.lower(), 1.0)
        
        return {
            "price": price,
            "volume_24h": 1000000,
            "market_cap": price * 1000000000,
            "price_change_24h": 0.0,
            "last_updated": datetime.now().isoformat(),
            "confidence": 50.0,
            "source": "estimated"
        }
    
    async def get_dex_data(self, dex: str = "raydium") -> Dict[str, Any]:
        """Get DEX-specific data for Solana DEXs."""
        try:
            cache_key = f"dex_{dex}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key][0]
            
            # Mock DEX data for Solana ecosystem
            dex_data = {
                "raydium": {
                    "name": "Raydium",
                    "tvl": 500_000_000,
                    "24h_volume": 50_000_000,
                    "pairs": 1200,
                    "fees_24h": 150_000
                },
                "orca": {
                    "name": "Orca", 
                    "tvl": 300_000_000,
                    "24h_volume": 30_000_000,
                    "pairs": 800,
                    "fees_24h": 90_000
                },
                "jupiter": {
                    "name": "Jupiter",
                    "tvl": 0,  # Aggregator
                    "24h_volume": 100_000_000,
                    "routes": 15000,
                    "fees_24h": 200_000
                }
            }
            
            if dex not in dex_data:
                dex = "raydium"  # Default fallback
            
            result = {
                **dex_data[dex],
                "timestamp": datetime.now().isoformat()
            }
            
            self.cache[cache_key] = (result, datetime.now())
            return result
            
        except Exception as e:
            logger.error(f"Error fetching DEX data: {str(e)}")
            return {
                "name": dex.title(),
                "tvl": 100_000_000,
                "24h_volume": 10_000_000,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_solana_network_stats(self) -> Dict[str, Any]:
        """Get Solana network statistics."""
        try:
            # This would integrate with Solana RPC and analytics APIs
            return {
                "tps": 2500,  # Current TPS
                "total_accounts": 50_000_000,
                "active_validators": 1900,
                "total_supply": 550_000_000,
                "staked_percentage": 75.0,
                "average_slot_time": 0.4,
                "network_fees_24h": 50000,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting Solana network stats: {e}")
            return {"error": str(e)}
    
    async def analyze_solana_opportunity(
        self,
        token_pair: str,
        amount: float,
        max_slippage: float
    ) -> Dict[str, Any]:
        """Analyze trading opportunity on Solana DEXs."""
        try:
            base_token, quote_token = token_pair.split('/')
            
            # Get data for both tokens
            base_data = await self.get_token_price(base_token)
            quote_data = await self.get_token_price(quote_token)
            
            # Get DEX data
            raydium_data = await self.get_dex_data("raydium")
            orca_data = await self.get_dex_data("orca")
            
            # Calculate metrics
            trade_value = amount * base_data["price"]
            estimated_slippage = min(trade_value / raydium_data["tvl"] * 100, max_slippage)
            
            # Analyze opportunity
            is_opportunity = (
                base_data["confidence"] > 80 and
                estimated_slippage < max_slippage and
                raydium_data["24h_volume"] > trade_value * 10
            )
            
            return {
                "analysis": {
                    "is_opportunity": is_opportunity,
                    "estimated_slippage": estimated_slippage,
                    "confidence": min(base_data["confidence"], quote_data["confidence"]),
                    "recommended_dex": "raydium" if raydium_data["tvl"] > orca_data["tvl"] else "orca",
                    "market_data": {
                        "base_token": base_data,
                        "quote_token": quote_data,
                        "raydium": raydium_data,
                        "orca": orca_data
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Solana opportunity: {str(e)}")
            raise
    
    async def get_market_context(self) -> Dict[str, Any]:
        """Get comprehensive Solana market context."""
        try:
            # Get SOL price and market data
            sol_data = await self.get_token_price("sol")
            
            # Get DEX data
            raydium_data = await self.get_dex_data("raydium")
            orca_data = await self.get_dex_data("orca")
            
            # Get network stats
            network_stats = await self.get_solana_network_stats()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "sol": {
                    "price": sol_data["price"],
                    "confidence": sol_data.get("confidence", 0.8),
                    "source": sol_data.get("source", "unknown")
                },
                "dex_ecosystem": {
                    "raydium_tvl": raydium_data["tvl"],
                    "orca_tvl": orca_data["tvl"],
                    "total_dex_volume": raydium_data["24h_volume"] + orca_data["24h_volume"]
                },
                "network": {
                    "tps": network_stats.get("tps", 0),
                    "validators": network_stats.get("active_validators", 0),
                    "fees_24h": network_stats.get("network_fees_24h", 0)
                },
                "indicators": {
                    "trend_strength": "medium",
                    "market_sentiment": "neutral",
                    "dex_health": "good" if raydium_data["tvl"] > 400_000_000 else "moderate"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting market context: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "sol": {"price": 0.0, "confidence": 0.5}
            }