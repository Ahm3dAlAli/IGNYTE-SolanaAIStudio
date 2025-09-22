"""
Decision Maker Plugin for Solana Swarm Intelligence
Makes strategic decisions for Solana DeFi operations
"""

import logging
from typing import Dict, Any, Optional
from solana_swarm.plugins.base import AgentPlugin, PluginConfig
from solana_swarm.core.agent import AgentConfig
from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig
import os

logger = logging.getLogger(__name__)

class DecisionMakerPlugin(AgentPlugin):
    """Strategic decision making plugin for Solana DeFi"""
    
    def __init__(self, agent_config: AgentConfig, plugin_config: PluginConfig):
        super().__init__(agent_config, plugin_config)
        self.min_confidence = float(self.plugin_config.custom_settings.get('min_confidence_threshold', 0.8))
        self.risk_tolerance = self.plugin_config.custom_settings.get('risk_tolerance', 'medium')
        self.max_slippage = float(self.plugin_config.custom_settings.get('max_slippage', 0.01))
        self.preferred_dexes = self.plugin_config.custom_settings.get('preferred_dexes', ['jupiter', 'raydium'])
        self.solana_connection = None
        self.logger = logger
        
    async def initialize(self) -> None:
        """Initialize decision maker"""
        # Initialize Solana connection
        config = SolanaConfig(
            network=os.getenv('SOLANA_NETWORK', 'devnet'),
            wallet_path=os.getenv('SOLANA_WALLET_PATH'),
            private_key=os.getenv('SOLANA_PRIVATE_KEY')
        )
        self.solana_connection = SolanaConnection(config)
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
            
            strategy = "Given Solana's high throughput and low fees, "
            if risk_level == 'high':
                strategy += "I recommend a cautious approach using smaller position sizes and Jupiter's route optimization for best execution. "
            elif risk_level == 'medium':
                strategy += "a balanced strategy using Raydium's deep liquidity pools while monitoring slippage is appropriate. "
            else:
                strategy += "we can be more aggressive with larger positions using Orca's concentrated liquidity for efficient trades. "
                
            rationale = f"My reasoning considers: 1) The {'upward' if price_change > 0 else 'downward'} momentum in SOL, "
            rationale += f"2) The {risk_level} risk environment across Solana DEXs, and "
            rationale += f"3) Our {self.risk_tolerance} risk tolerance with {self.max_slippage*100:.1f}% max slippage. "
            
            # Get current Solana network stats
            network_stats = await self.solana_connection.get_network_stats()
            current_tps = network_stats.get('tps', 0)
            
            if current_tps > 2000:
                rationale += f"High network throughput ({current_tps:.0f} TPS) supports immediate execution. "
            else:
                rationale += f"Moderate network activity ({current_tps:.0f} TPS) suggests normal execution times. "
            
            action = "Recommended Action: "
            confidence = 0.0
            action_type = ""
            
            if abs(price_change) >= 0.05 and market_confidence >= 0.8:
                if price_change > 0:
                    action_type = 'take_profit'
                    action += f"Take profit using Jupiter's smart routing to minimize slippage across DEXs. "
                else:
                    action_type = 'buy_dip'
                    action += f"Buy the dip using Raydium's deep liquidity pools. "
                confidence = 0.85
            elif abs(price_change) >= 0.02 and market_confidence >= 0.7:
                if price_change > 0:
                    action_type = 'partial_profit'
                    action += f"Partial profit-taking using Orca's concentrated liquidity. "
                else:
                    action_type = 'scale_in'
                    action += f"Scale into position gradually across multiple DEXs. "
                confidence = 0.75
            else:
                action_type = 'hold'
                action += "Hold current positions and monitor for clearer Solana market signals. "
                confidence = 0.65
                
            action += f"Set stops at {abs(price_change)*1.5:.1f}% to protect against adverse moves."
            
            return {
                'context': context_analysis,
                'strategy': strategy,
                'rationale': rationale,
                'action': action,
                'action_type': action_type,
                'confidence': confidence,
                'risk_level': risk_level,
                'network_tps': current_tps,
                'preferred_dex': self.preferred_dexes[0] if self.preferred_dexes else 'jupiter'
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating Solana market data: {str(e)}")
            return {'error': str(e)}
            
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trading decision on Solana"""
        try:
            action_type = action.get('type', '')
            amount = action.get('amount', 0.01)  # Default to 0.01 SOL
            recipient = action.get('recipient', '')
            
            if action_type == 'transfer' and recipient:
                result = await self.solana_connection.transfer_sol(recipient, amount)
                return {
                    "status": "success",
                    "transaction": result,
                    "network": "solana"
                }
            elif action_type == 'swap':
                input_mint = action.get('input_mint', 'So11111111111111111111111111111111111111112')  # SOL
                output_mint = action.get('output_mint', 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')  # USDC
                slippage = action.get('slippage', self.max_slippage)
                
                result = await self.solana_connection.swap_tokens_jupiter(
                    input_mint, output_mint, amount, slippage
                )
                return {
                    "status": "success", 
                    "transaction": result,
                    "network": "solana"
                }
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported action type: {action_type}"
                }
            
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.solana_connection:
            await self.solana_connection.close()
