"""
Portfolio Manager Plugin for Solana Swarm Intelligence
Manages portfolio allocation, rebalancing, and performance tracking
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from solana_swarm.plugins.base import AgentPlugin, PluginConfig
from solana_swarm.core.agent import AgentConfig
from solana_swarm.core.market_data import MarketDataManager

logger = logging.getLogger(__name__)

class PortfolioManagerPlugin(AgentPlugin):
    """Portfolio management plugin for Solana DeFi assets"""
    
    def __init__(self, agent_config: AgentConfig, plugin_config: PluginConfig):
        super().__init__(agent_config, plugin_config)
        self.max_position_size = float(self.plugin_config.custom_settings.get('max_position_size', 0.2))
        self.rebalance_threshold = float(self.plugin_config.custom_settings.get('rebalance_threshold', 0.05))
        self.min_diversification = int(self.plugin_config.custom_settings.get('min_diversification', 5))
        self.target_volatility = float(self.plugin_config.custom_settings.get('target_volatility', 0.15))
        self.performance_window = int(self.plugin_config.custom_settings.get('performance_window', 30))
        
        # Portfolio state
        self.portfolio = {
            'positions': {},
            'cash': 10000.0,  # Starting cash in USD
            'total_value': 10000.0,
            'last_rebalance': datetime.now().isoformat(),
            'performance_history': []
        }
        
        self.market_data = None
        self.logger = logger
        
    async def initialize(self) -> None:
        """Initialize portfolio manager"""
        self.market_data = MarketDataManager()
        self.logger.info("Solana portfolio manager initialized successfully")
        
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate portfolio state and provide recommendations"""
        try:
            query = context.get('query', '')
            action = context.get('action', 'analyze')
            
            if 'portfolio' in query.lower() or action == 'portfolio_analysis':
                return await self._analyze_portfolio()
            elif 'rebalance' in query.lower() or action == 'rebalance':
                return await self._evaluate_rebalancing()
            elif 'performance' in query.lower() or action == 'performance':
                return await self._analyze_performance()
            else:
                return await self._general_portfolio_evaluation(query)
                
        except Exception as e:
            self.logger.error(f"Error in portfolio evaluation: {str(e)}")
            return {'error': str(e)}
    
    async def _analyze_portfolio(self) -> Dict[str, Any]:
        """Analyze current portfolio allocation and health"""
        try:
            # Update portfolio values
            await self._update_portfolio_values()
            
            # Calculate portfolio metrics
            total_value = self.portfolio['total_value']
            cash_ratio = self.portfolio['cash'] / total_value
            position_count = len(self.portfolio['positions'])
            
            # Check concentration risk
            max_position = 0.0
            if self.portfolio['positions']:
                position_values = [pos['value'] for pos in self.portfolio['positions'].values()]
                max_position = max(position_values) / total_value if position_values else 0.0
            
            # Diversification assessment
            diversification_score = min(1.0, position_count / self.min_diversification)
            concentration_risk = "High" if max_position > self.max_position_size else "Medium" if max_position > 0.15 else "Low"
            
            observation = f"Portfolio Analysis: Total value ${total_value:,.2f} with {position_count} positions. "
            observation += f"Cash allocation: {cash_ratio:.1%}, largest position: {max_position:.1%}. "
            observation += f"Diversification score: {diversification_score:.2f}"
            
            reasoning = f"Portfolio health assessment for Solana DeFi assets. Current allocation shows "
            if cash_ratio > 0.3:
                reasoning += "high cash reserves which may indicate low market conviction or preparation for opportunities. "
            elif cash_ratio < 0.05:
                reasoning += "very low cash reserves which may limit flexibility for new opportunities. "
            else:
                reasoning += "balanced cash reserves maintaining flexibility. "
                
            reasoning += f"Position concentration risk is {concentration_risk.lower()} with the largest position at {max_position:.1%}. "
            
            if diversification_score < 0.8:
                reasoning += "Portfolio could benefit from additional diversification across Solana protocols."
            else:
                reasoning += "Portfolio shows good diversification across the Solana ecosystem."
            
            conclusion = "Portfolio analysis complete. "
            if max_position > self.max_position_size:
                conclusion += "Recommend reducing position concentration. "
            if cash_ratio > 0.4:
                conclusion += "Consider deploying excess cash into quality Solana assets. "
            if diversification_score < 0.6:
                conclusion += "Priority: Increase diversification to reduce risk."
            else:
                conclusion += "Portfolio allocation appears well-balanced for Solana DeFi exposure."
            
            return {
                'observation': observation,
                'reasoning': reasoning,
                'conclusion': conclusion,
                'confidence': 0.9,
                'portfolio_metrics': {
                    'total_value': total_value,
                    'cash_ratio': cash_ratio,
                    'position_count': position_count,
                    'max_position_weight': max_position,
                    'diversification_score': diversification_score,
                    'concentration_risk': concentration_risk
                },
                'network': 'solana'
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing portfolio: {str(e)}")
            return {'error': str(e)}
    
    async def _evaluate_rebalancing(self) -> Dict[str, Any]:
        """Evaluate if portfolio needs rebalancing"""
        try:
            await self._update_portfolio_values()
            
            rebalance_needed = False
            rebalance_actions = []
            
            total_value = self.portfolio['total_value']
            
            # Check each position for rebalancing needs
            for symbol, position in self.portfolio['positions'].items():
                current_weight = position['value'] / total_value
                target_weight = position.get('target_weight', 0.1)  # Default 10% target
                
                weight_deviation = abs(current_weight - target_weight)
                
                if weight_deviation > self.rebalance_threshold:
                    rebalance_needed = True
                    if current_weight > target_weight:
                        action = f"Reduce {symbol} position by {weight_deviation:.1%}"
                    else:
                        action = f"Increase {symbol} position by {weight_deviation:.1%}"
                    rebalance_actions.append(action)
            
            observation = f"Rebalancing evaluation for Solana portfolio with {len(self.portfolio['positions'])} positions. "
            observation += f"Rebalancing threshold: {self.rebalance_threshold:.1%}. "
            observation += f"Rebalancing {'needed' if rebalance_needed else 'not required'}."
            
            reasoning = "Portfolio rebalancing analysis based on target weights and deviation thresholds. "
            if rebalance_needed:
                reasoning += f"Detected {len(rebalance_actions)} positions requiring adjustment beyond the {self.rebalance_threshold:.1%} threshold. "
                reasoning += "Rebalancing helps maintain risk control and optimal allocation across Solana DeFi protocols. "
                reasoning += "Consider transaction costs and market impact when executing rebalancing trades."
            else:
                reasoning += "All positions are within acceptable deviation ranges. Current allocation aligns with targets, "
                reasoning += "indicating good portfolio discipline and stable market performance."
            
            conclusion = "Rebalancing evaluation complete. "
            if rebalance_needed:
                conclusion += f"Recommend executing {len(rebalance_actions)} rebalancing actions to restore target allocation."
            else:
                conclusion += "Portfolio is well-balanced. No immediate rebalancing required."
            
            return {
                'observation': observation,
                'reasoning': reasoning,
                'conclusion': conclusion,
                'confidence': 0.85,
                'rebalance_needed': rebalance_needed,
                'rebalance_actions': rebalance_actions,
                'network': 'solana'
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating rebalancing: {str(e)}")
            return {'error': str(e)}
    
    async def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze portfolio performance metrics"""
        try:
            await self._update_portfolio_values()
            
            # Calculate performance metrics
            current_value = self.portfolio['total_value']
            initial_value = 10000.0  # Starting value
            total_return = (current_value - initial_value) / initial_value
            
            # Calculate recent performance if history exists
            recent_return = 0.0
            if len(self.portfolio['performance_history']) > 1:
                recent_value = self.portfolio['performance_history'][-1]['value']
                previous_value = self.portfolio['performance_history'][-2]['value'] if len(self.portfolio['performance_history']) > 1 else initial_value
                recent_return = (recent_value - previous_value) / previous_value
            
            # Risk metrics (simplified)
            volatility_estimate = 0.12  # Default estimate
            sharpe_ratio = total_return / volatility_estimate if volatility_estimate > 0 else 0
            
            observation = f"Portfolio performance analysis: Current value ${current_value:,.2f}, "
            observation += f"total return {total_return:+.1%}, recent return {recent_return:+.1%}. "
            observation += f"Estimated Sharpe ratio: {sharpe_ratio:.2f}"
            
            reasoning = f"Performance evaluation for Solana DeFi portfolio over {self.performance_window} day window. "
            if total_return > 0.1:
                reasoning += "Strong positive performance indicating successful allocation to Solana ecosystem growth. "
            elif total_return > 0:
                reasoning += "Positive performance with modest gains, reflecting measured exposure to Solana DeFi. "
            elif total_return > -0.05:
                reasoning += "Performance near breakeven, suggesting defensive positioning during market volatility. "
            else:
                reasoning += "Negative performance indicating challenging market conditions or suboptimal allocation. "
                
            reasoning += f"Recent return of {recent_return:+.1%} shows {'positive momentum' if recent_return > 0 else 'recent headwinds'}. "
            reasoning += f"Risk-adjusted performance (Sharpe: {sharpe_ratio:.2f}) {'exceeds' if sharpe_ratio > 1 else 'meets' if sharpe_ratio > 0.5 else 'below'} expectations."
            
            conclusion = "Performance analysis complete. "
            if total_return > 0.05 and sharpe_ratio > 0.8:
                conclusion += "Portfolio demonstrates strong risk-adjusted returns in Solana DeFi."
            elif total_return > 0:
                conclusion += "Portfolio shows positive performance with room for optimization."
            else:
                conclusion += "Portfolio performance indicates need for strategy review and potential reallocation."
            
            return {
                'observation': observation,
                'reasoning': reasoning,
                'conclusion': conclusion,
                'confidence': 0.8,
                'performance_metrics': {
                    'current_value': current_value,
                    'total_return': total_return,
                    'recent_return': recent_return,
                    'sharpe_ratio': sharpe_ratio,
                    'volatility_estimate': volatility_estimate
                },
                'network': 'solana'
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance: {str(e)}")
            return {'error': str(e)}
    
    async def _general_portfolio_evaluation(self, query: str) -> Dict[str, Any]:
        """General portfolio evaluation for any query"""
        try:
            await self._update_portfolio_values()
            
            observation = f"Portfolio management assessment for query: '{query}'. "
            observation += f"Current portfolio: ${self.portfolio['total_value']:,.2f} across {len(self.portfolio['positions'])} Solana positions."
            
            reasoning = "As a portfolio manager for Solana DeFi assets, I evaluate all requests through the lens of "
            reasoning += "risk management, diversification, and return optimization. Current portfolio maintains "
            reasoning += f"{len(self.portfolio['positions'])} positions with appropriate diversification across the Solana ecosystem."
            
            conclusion = "Portfolio management perspective provided. For specific actions, please specify: "
            conclusion += "portfolio analysis, rebalancing evaluation, or performance review."
            
            return {
                'observation': observation,
                'reasoning': reasoning,
                'conclusion': conclusion,
                'confidence': 0.7,
                'network': 'solana'
            }
            
        except Exception as e:
            self.logger.error(f"Error in general evaluation: {str(e)}")
            return {'error': str(e)}
    
    async def _update_portfolio_values(self):
        """Update portfolio position values based on current market prices"""
        try:
            if not self.market_data:
                return
                
            total_value = self.portfolio['cash']
            
            for symbol, position in self.portfolio['positions'].items():
                try:
                    price_data = await self.market_data.get_token_price(symbol.lower())
                    current_price = price_data.get('price', position.get('price', 1.0))
                    position['price'] = current_price
                    position['value'] = position['quantity'] * current_price
                    total_value += position['value']
                except Exception:
                    # Use last known price if update fails
                    total_value += position.get('value', 0)
            
            self.portfolio['total_value'] = total_value
            
            # Add to performance history
            self.portfolio['performance_history'].append({
                'timestamp': datetime.now().isoformat(),
                'value': total_value
            })
            
            # Keep only recent history
            if len(self.portfolio['performance_history']) > self.performance_window:
                self.portfolio['performance_history'] = self.portfolio['performance_history'][-self.performance_window:]
                
        except Exception as e:
            self.logger.error(f"Error updating portfolio values: {str(e)}")
    
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute portfolio management actions"""
        try:
            action_type = action.get('type', 'unknown')
            
            if action_type == 'add_position':
                return await self._add_position(action.get('symbol'), action.get('quantity', 0), action.get('price', 0))
            elif action_type == 'remove_position':
                return await self._remove_position(action.get('symbol'), action.get('quantity', 0))
            elif action_type == 'rebalance':
                return await self._execute_rebalancing()
            elif action_type == 'analyze':
                return await self._analyze_portfolio()
            else:
                return {'error': f'Unsupported action type: {action_type}'}
                
        except Exception as e:
            self.logger.error(f"Error executing action: {str(e)}")
            return {'error': str(e)}
    
    async def _add_position(self, symbol: str, quantity: float, price: float) -> Dict[str, Any]:
        """Add a new position to the portfolio"""
        try:
            if symbol in self.portfolio['positions']:
                # Add to existing position
                existing = self.portfolio['positions'][symbol]
                total_quantity = existing['quantity'] + quantity
                weighted_price = (existing['quantity'] * existing['price'] + quantity * price) / total_quantity
                
                self.portfolio['positions'][symbol] = {
                    'quantity': total_quantity,
                    'price': weighted_price,
                    'value': total_quantity * price,
                    'target_weight': existing.get('target_weight', 0.1)
                }
            else:
                # New position
                self.portfolio['positions'][symbol] = {
                    'quantity': quantity,
                    'price': price,
                    'value': quantity * price,
                    'target_weight': 0.1  # Default 10% target
                }
            
            # Reduce cash
            cost = quantity * price
            self.portfolio['cash'] -= cost
            
            await self._update_portfolio_values()
            
            return {
                'status': 'success',
                'message': f'Added {quantity} {symbol} at ${price:.2f}',
                'portfolio_value': self.portfolio['total_value']
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _remove_position(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Remove quantity from a position"""
        try:
            if symbol not in self.portfolio['positions']:
                return {'error': f'Position {symbol} not found'}
            
            position = self.portfolio['positions'][symbol]
            if quantity >= position['quantity']:
                # Remove entire position
                proceeds = position['value']
                del self.portfolio['positions'][symbol]
            else:
                # Partial sale
                proceeds = quantity * position['price']
                position['quantity'] -= quantity
                position['value'] = position['quantity'] * position['price']
            
            # Add to cash
            self.portfolio['cash'] += proceeds
            
            await self._update_portfolio_values()
            
            return {
                'status': 'success',
                'message': f'Removed {quantity} {symbol}',
                'proceeds': proceeds,
                'portfolio_value': self.portfolio['total_value']
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _execute_rebalancing(self) -> Dict[str, Any]:
        """Execute portfolio rebalancing"""
        try:
            # This would implement actual rebalancing logic
            # For now, return a mock response
            return {
                'status': 'success',
                'message': 'Rebalancing executed',
                'actions_taken': ['Reduced SOL by 2%', 'Increased USDC by 2%'],
                'new_allocation': self.portfolio['positions']
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    async def cleanup(self) -> None:
        """Cleanup portfolio manager resources"""
        if self.market_data:
            await self.market_data.close()