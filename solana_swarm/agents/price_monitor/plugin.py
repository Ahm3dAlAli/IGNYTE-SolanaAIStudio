"""
Price Monitor Plugin for Solana Swarm Intelligence
Monitors SOL and SPL token prices across Solana DEXs
"""

import logging
from typing import Dict, Any, Optional
from solana_swarm.plugins.base import AgentPlugin, PluginConfig
from solana_swarm.core.agent import AgentConfig
from solana_swarm.core.market_data import MarketDataManager

logger = logging.getLogger(__name__)

class PriceMonitorPlugin(AgentPlugin):
    """Price monitoring plugin for Solana market analysis"""
    
    def __init__(self, agent_config: AgentConfig, plugin_config: PluginConfig):
        super().__init__(agent_config, plugin_config)
        self.market_data = None
        self.update_interval = int(self.plugin_config.custom_settings.get('update_interval', 60))
        self.alert_threshold = float(self.plugin_config.custom_settings.get('alert_threshold', 0.05))
        self.monitored_tokens = self.plugin_config.custom_settings.get('monitored_tokens', ['SOL', 'USDC'])
        self.logger = logger
        
    async def initialize(self) -> None:
        """Initialize market data connection"""
        self.market_data = MarketDataManager()
        self.logger.info("Solana price monitor initialized successfully")
        
    async def get_price_data(self, token: str = 'sol') -> Dict[str, Any]:
        """Get token price data using available method"""
        try:
            return await self.market_data.get_token_price(token)
        except Exception as e:
            self.logger.error(f"Error getting price data for {token}: {str(e)}")
            return {}
        
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate Solana market conditions with detailed analysis"""
        try:
            token = context.get('token', 'sol').lower()
            price_data = await self.get_price_data(token)
            
            if not price_data:
                return {'error': f'Failed to get price data for {token}'}
            
            price = price_data['price']
            change_24h = price_data.get('price_change_24h', 0)
            source = price_data.get('source', 'unknown')
            
            # Detailed market analysis
            observation = f"I observe that {token.upper()} is currently trading at ${price:.2f}, with a {change_24h:.1f}% change in the last 24 hours. "
            observation += f"Price data sourced from {source}. "
            
            if abs(change_24h) >= self.alert_threshold * 100:
                observation += f"This represents a significant {'increase' if change_24h > 0 else 'decrease'} in price, exceeding our alert threshold of {self.alert_threshold*100}%."
            else:
                observation += "The price movement is within normal trading ranges for Solana tokens."
                
            reasoning = f"Analyzing this price action on Solana: The {abs(change_24h):.1f}% {'upward' if change_24h > 0 else 'downward'} movement "
            
            if abs(change_24h) >= 10:
                reasoning += "indicates high volatility. This could be due to significant DEX activity, major announcements, or large transactions on Jupiter aggregator. "
            elif abs(change_24h) >= 5:
                reasoning += "suggests moderate activity across Solana DEXs. This might indicate normal trading dynamics or emerging trends on Raydium/Orca. "
            else:
                reasoning += "shows relatively stable conditions. This could indicate low trading volume or consolidation period across Solana DEXs. "
                
            # Add DEX-specific insights
            if source == "jupiter":
                reasoning += "Jupiter aggregator data suggests optimal routing across multiple DEXs. "
            elif source == "raydium":
                reasoning += "Raydium DEX shows strong liquidity for this token. "
            elif source == "orca":
                reasoning += "Orca concentrated liquidity pools indicate efficient price discovery. "
                
            conclusion = "Based on the Solana ecosystem analysis, "
            if abs(change_24h) >= 10:
                conclusion += f"the market is showing {'strong bullish' if change_24h > 0 else 'strong bearish'} momentum with high volatility. Traders should consider DEX liquidity and potential MEV risks."
            elif abs(change_24h) >= 5:
                conclusion += f"there's a moderate {'upward' if change_24h > 0 else 'downward'} trend developing. This could present opportunities on Solana DEXs while maintaining reasonable risk levels."
            else:
                conclusion += "the market appears stable with good liquidity across Raydium and Orca. This could be optimal for larger trades with minimal slippage."
            
            return {
                'observation': observation,
                'reasoning': reasoning,
                'conclusion': conclusion,
                'price': price,
                'change_24h': change_24h,
                'confidence': 0.95,
                'risk_level': 'high' if abs(change_24h) >= 10 else 'medium' if abs(change_24h) >= 5 else 'low',
                'source': source,
                'network': 'solana'
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating Solana market conditions: {str(e)}")
            return {'error': str(e)}
            
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute monitoring actions"""
        try:
            if action.get('type') == 'monitor_price':
                token = action.get('token', 'sol')
                return await self.evaluate({'token': token})
            return {'error': 'Unsupported action type'}
            
        except Exception as e:
            self.logger.error(f"Error executing action: {str(e)}")
            return {'error': str(e)}
            
    async def cleanup(self) -> None:
        """Cleanup market data connection"""
        if self.market_data:
            try:
                await self.market_data.close()
            except:
                pass