"""
Decision Maker Plugin for Solana Swarm Intelligence
Makes strategic decisions for Solana DeFi operations
"""

import logging
from typing import Dict, Any, Optional
from solana_swarm.plugins.base import AgentPlugin, PluginConfig
from solana_swarm.core.agent import AgentConfig

logger = logging.getLogger(__name__)

class DecisionMakerPlugin(AgentPlugin):
    """Strategic decision making plugin for Solana DeFi"""
    
    def __init__(self, agent_config: AgentConfig, plugin_config: PluginConfig):
        super().__init__(agent_config, plugin_config)
        self.min_confidence = float(self.plugin_config.custom_settings.get('min_confidence_threshold', 0.8))
        self.risk_tolerance = self.plugin_config.custom_settings.get('risk_tolerance', 'medium')
        self.max_slippage = float(self.plugin_config.custom_settings.get('max_slippage', 0.01))
        self.preferred_dexes = self.plugin_config.custom_settings.get('preferred_dexes', ['jupiter', 'raydium'])
        self.logger = logger
        
    async def initialize(self) -> None:
        """Initialize decision maker"""
        self.logger.info("Solana decision maker initialized successfully")
        
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate market analysis and provide strategic decisions for Solana"""
        try:
            market_analysis = context.get('market_analysis', {})
            current_price = context.get('current_price', 0)
            network = context.get('network', 'solana')
            
            # Extract market insights
            price_change = market_analysis.get('change_24h', 0)
            risk_level = market_analysis.get('risk_level', 'medium')
            market_confidence = market_analysis.get('confidence', 0)
            source = market_analysis.get('source', 'unknown')
            
            # Solana-specific analysis
            context_analysis = f"I'm analyzing the Solana market at ${current_price:.2f}. The price monitor indicates a {abs(price_change):.1f}% {'increase' if price_change > 0 else 'decrease'} "
            context_analysis += f"with {market_confidence*100:.0f}% confidence from {source}. Market risk is assessed as {risk_level}. "
            
            # DEX-specific considerations
            if source == 'jupiter':
                context_analysis += "Jupiter aggregator data suggests optimal routing across multiple DEXs is available. "
            elif source == 'raydium':
                context_analysis += "Raydium shows strong liquidity pools for potential trades. "
            elif source == 'orca':
                context_analysis += "Orca's concentrated liquidity model offers efficient price execution. "
            
            strategy = "Given Solana's high
                "