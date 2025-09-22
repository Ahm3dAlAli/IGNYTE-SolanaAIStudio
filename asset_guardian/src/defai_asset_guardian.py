"""
Solana Asset Guardian - Intelligent Portfolio Management on Solana
Main service that orchestrates the specialized agents and provides a unified interface
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
import json
import os
from datetime import datetime
from dotenv import load_dotenv

from solana_swarm.core.agent import AgentConfig
from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
from solana_swarm.plugins.loader import PluginLoader
from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig
from solana_swarm.core.market_data import MarketDataManager
from solana_swarm.core.memory_manager import MemoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AssetGuardian:
    """
    Solana Asset Guardian - Intelligent Portfolio Management System
    
    Uses swarm intelligence from specialized agents to provide:
    1. Real-time portfolio monitoring on Solana
    2. Risk assessment and mitigation
    3. Automated strategy execution across DEXs
    4. Market insights and predictions
    """
    
    def __init__(self):
        """Initialize Solana Asset Guardian"""
        # Load environment variables
        load_dotenv()
        
        self.config = self._load_config()
        self.agents = {}
        self.solana = None
        self.market_data = None
        self.memory = None
        self.plugin_loader = PluginLoader()
        
        # Asset Guardian state
        self.portfolio = {}
        self.market_analysis = {}
        self.risk_assessment = {}
        self.active_strategies = []
        self.transaction_history = []
        
        # System settings
        self.settings = {
            'auto_execution': False,  # Start in manual mode for safety
            'simulation_mode': True,  # Start in simulation mode
            'risk_tolerance': 'medium',  # Default risk tolerance
            'notification_level': 'high',  # Default to high notifications
            'update_interval': 300,  # 5 minutes between updates
            'emergency_stop_loss': True  # Enable emergency stop loss
        }
        
        logger.info("Solana Asset Guardian initialized")
    
    def _load_config(self) -> AgentConfig:
        """Load configuration from environment variables"""
        # Validate required environment variables
        required_vars = ['SOLANA_WALLET_PATH', 'LLM_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return AgentConfig(
            name="solana-asset-guardian",
            environment=os.getenv('ENVIRONMENT', 'development'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            llm={
                'provider': os.getenv('LLM_PROVIDER', 'openrouter'),
                'api_key': os.getenv('LLM_API_KEY'),
                'model': os.getenv('LLM_MODEL', 'anthropic/claude-3.5-sonnet'),
                'temperature': float(os.getenv('LLM_TEMPERATURE', '0.7')),
                'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '2000')),
                'api_url': os.getenv('LLM_API_URL', 'https://openrouter.ai/api/v1')
            },
            solana={
                'network': os.getenv('SOLANA_NETWORK', 'devnet'),
                'wallet_path': os.getenv('SOLANA_WALLET_PATH'),
                'private_key': os.getenv('SOLANA_PRIVATE_KEY'),
                'rpc_url': os.getenv('SOLANA_RPC_URL', ''),
                'commitment': os.getenv('SOLANA_COMMITMENT', 'confirmed')
            }
        )
    
    async def initialize(self) -> None:
        """Initialize the Solana Asset Guardian system"""
        try:
            logger.info("Starting Solana Asset Guardian initialization")
            
            # Initialize core services
            self.market_data = MarketDataManager()
            self.memory = MemoryManager()
            
            # Initialize Solana connection
            solana_config = SolanaConfig(
                network=self.config.solana.network,
                wallet_path=self.config.solana.wallet_path,
                private_key=self.config.solana.private_key,
                rpc_url=self.config.solana.rpc_url,
                commitment=self.config.solana.commitment
            )
            self.solana = SolanaConnection(solana_config)
            
            # Load and initialize specialized agents
            await self._initialize_agents()
            
            # Get initial portfolio data
            await self._update_portfolio()
            
            # Initial analyses
            self.market_analysis = await self._perform_market_analysis()
            self.risk_assessment = await self._assess_portfolio_risk()
            
            logger.info("Solana Asset Guardian initialization complete")
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            await self.cleanup()
            raise
    
    async def _initialize_agents(self) -> None:
        """Load and initialize all specialized agents"""
        try:
            agent_configs = [
                {
                    'name': 'price-monitor',
                    'role': 'market_analyzer',
                    'min_confidence': 0.7
                },
                {
                    'name': 'decision-maker',
                    'role': 'strategy_optimizer',
                    'min_confidence': 0.8
                },
                {
                    'name': 'arbitrage-agent',
                    'role': 'arbitrage_detector',
                    'min_confidence': 0.75
                }
            ]
            
            # Load and initialize each agent
            for cfg in agent_configs:
                logger.info(f"Loading agent: {cfg['name']}")
                
                # Create SwarmConfig for this agent
                swarm_config = SwarmConfig(
                    role=cfg['role'],
                    min_confidence=cfg['min_confidence'],
                    min_votes=2,
                    timeout=60.0
                )
                
                # Create swarm agent
                agent = SwarmAgent(swarm_config)
                
                # Initialize agent
                await agent.initialize()
                
                # Store agent
                self.agents[cfg['name']] = agent
                logger.info(f"Agent {cfg['name']} initialized")
            
            # Form swarm network between agents
            if len(self.agents) >= 2:
                agent_list = list(self.agents.values())
                if len(agent_list) >= 2:
                    await agent_list[0].join_swarm(agent_list[1:])
                    logger.info("Swarm network established between agents")
            
        except Exception as e:
            logger.error(f"Agent initialization error: {e}")
            raise
    
    async def update(self) -> Dict[str, Any]:
        """Update all data and analyses"""
        try:
            # Update portfolio
            await self._update_portfolio()
            
            # Update market analysis
            self.market_analysis = await self._perform_market_analysis()
            
            # Update risk assessment
            self.risk_assessment = await self._assess_portfolio_risk()
            
            # Store history in memory
            await self.memory.store(
                category="updates",
                data={
                    "portfolio": self.portfolio,
                    "market_analysis": self.market_analysis,
                    "risk_assessment": self.risk_assessment
                },
                context={
                    "timestamp": datetime.now().isoformat(),
                    "network": "solana"
                }
            )
            
            # Check for automated actions
            await self._check_automated_actions()
            
            return {
                "portfolio": self.portfolio,
                "market_analysis": self.market_analysis,
                "risk_assessment": self.risk_assessment,
                "updated_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Update error: {e}")
            return {
                "error": str(e),
                "updated_at": datetime.now().isoformat()
            }
    
    async def _update_portfolio(self) -> None:
        """Update portfolio data from Solana blockchain"""
        try:
            # Get SOL balance
            sol_balance = await self.solana.get_balance()
            
            # Get SOL price
            sol_price_data = await self.market_data.get_token_price("sol")
            sol_price = sol_price_data["price"]
            sol_value = sol_balance * sol_price
            
            # Get network stats for context
            network_stats = await self.solana.get_network_stats()
            
            # Build portfolio
            assets = [
                {
                    "symbol": "SOL",
                    "balance": sol_balance,
                    "value_usd": sol_value,
                    "price_usd": sol_price,
                    "type": "Native Token",
                    "network": "solana"
                }
            ]
            
            # Get SPL token balances (simplified for demo)
            spl_tokens = [
                ('USDC', 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'),
                ('USDT', 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB')
            ]
            
            total_value = sol_value
            
            for symbol, mint in spl_tokens:
                try:
                    token_balance = await self.solana.get_token_balance(mint)
                    if token_balance > 0:
                        token_price_data = await self.market_data.get_token_price(symbol.lower())
                        token_price = token_price_data["price"]
                        token_value = token_balance * token_price
                        total_value += token_value
                        
                        assets.append({
                            "symbol": symbol,
                            "balance": token_balance,
                            "value_usd": token_value,
                            "price_usd": token_price,
                            "type": "SPL Token",
                            "mint": mint,
                            "network": "solana"
                        })
                except Exception as e:
                    logger.warning(f"Failed to get {symbol} balance: {e}")
            
            # Calculate allocations
            for asset in assets:
                asset["allocation"] = (asset["value_usd"] / total_value * 100) if total_value > 0 else 0
            
            self.portfolio = {
                "total_value_usd": total_value,
                "assets": assets,
                "network_stats": network_stats,
                "updated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Portfolio updated. Total value: ${total_value:.2f}")
            
        except Exception as e:
            logger.error(f"Portfolio update error: {e}")
            raise
    
    async def _perform_market_analysis(self) -> Dict[str, Any]:
        """Perform market analysis using agents"""
        try:
            # Try to get price monitor agent
            price_monitor = None
            for name, agent in self.agents.items():
                if hasattr(agent, 'config') and agent.config.role == 'market_analyzer':
                    price_monitor = agent
                    break
            
            if not price_monitor:
                # Fallback to direct market data
                sol_data = await self.market_data.get_token_price("sol")
                return {
                    "price": sol_data["price"],
                    "change_24h": sol_data.get("price_change_24h", 0),
                    "confidence": 0.8,
                    "source": "direct",
                    "trends": ["Market data retrieved directly"],
                    "timestamp": datetime.now().isoformat()
                }
            
            # Create context for analysis
            context = {
                "token": "sol",
                "network": "solana",
                "timestamp": datetime.now().isoformat()
            }
            
            # Perform analysis
            response = await price_monitor.evaluate(context)
            
            # Log analysis
            logger.info(f"Market analysis completed. Confidence: {response.get('confidence', 0):.2f}")
            
            return response
            
        except Exception as e:
            logger.error(f"Market analysis error: {e}")
            return {
                "error": str(e),
                "confidence": 0,
                "trends": ["Error performing market analysis"],
                "timestamp": datetime.now().isoformat()
            }
    
    async def _assess_portfolio_risk(self) -> Dict[str, Any]:
        """Assess portfolio risk"""
        try:
            # Calculate basic risk metrics
            assets = self.portfolio.get('assets', [])
            total_value = self.portfolio.get('total_value_usd', 0)
            
            if not assets or total_value == 0:
                return {
                    "risk_score": 50,
                    "risk_factors": ["No portfolio data available"],
                    "confidence": 0.5,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Calculate concentration risk
            concentrations = [asset.get('allocation', 0) for asset in assets]
            max_concentration = max(concentrations) if concentrations else 0
            
            # Calculate diversification
            asset_count = len(assets)
            diversification_score = min(10, asset_count * 2)
            
            # Base risk score
            risk_score = 50  # Medium risk baseline
            
            # Adjust for concentration
            if max_concentration > 80:
                risk_score += 30
            elif max_concentration > 60:
                risk_score += 15
            
            # Adjust for diversification
            if asset_count < 2:
                risk_score += 20
            elif asset_count >= 5:
                risk_score -= 10
            
            # Market volatility factor
            market_change = abs(self.market_analysis.get('change_24h', 0))
            if market_change > 10:
                risk_score += 15
            elif market_change < 2:
                risk_score -= 5
            
            risk_score = max(0, min(100, risk_score))
            
            risk_factors = []
            if max_concentration > 70:
                risk_factors.append(f"High concentration: {max_concentration:.1f}% in single asset")
            if asset_count < 3:
                risk_factors.append("Low diversification: fewer than 3 assets")
            if market_change > 10:
                risk_factors.append(f"High market volatility: {market_change:.1f}% change")
            
            return {
                "risk_score": risk_score,
                "risk_factors": risk_factors or ["Portfolio within normal risk parameters"],
                "diversification_score": diversification_score,
                "concentration_risk": max_concentration,
                "confidence": 0.85,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return {
                "error": str(e),
                "risk_score": 50,
                "risk_factors": ["Error performing risk assessment"],
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_strategy(self, operation_type: str = "rebalance") -> Dict[str, Any]:
        """Generate a portfolio strategy"""
        try:
            # Get decision maker agent
            decision_maker = None
            for name, agent in self.agents.items():
                if hasattr(agent, 'config') and 'strategy' in agent.config.role:
                    decision_maker = agent
                    break
            
            if not decision_maker:
                return {
                    "error": "No strategy agent available",
                    "confidence": 0,
                    "actions": [],
                    "timestamp": datetime.now().isoformat()
                }
            
            # Create context for strategy generation
            context = {
                "portfolio": self.portfolio,
                "market_analysis": self.market_analysis,
                "risk_assessment": self.risk_assessment,
                "operation_type": operation_type,
                "timestamp": datetime.now().isoformat(),
                "network": "solana"
            }
            
            # Generate strategy
            response = await decision_maker.evaluate(context)
            
            # Log strategy
            logger.info(f"Strategy generated. Confidence: {response.get('confidence', 0):.2f}")
            
            # Store strategy
            await self.memory.store(
                category="strategies",
                data=response,
                context={
                    "timestamp": datetime.now().isoformat(),
                    "network": "solana",
                    "operation_type": operation_type
                }
            )
            
            # Add to active strategies if confidence is high enough
            if response.get('confidence', 0) >= 0.75:
                self.active_strategies.append({
                    "strategy": response,
                    "status": "pending",
                    "created_at": datetime.now().isoformat()
                })
            
            return response
            
        except Exception as e:
            logger.error(f"Strategy generation error: {e}")
            return {
                "error": str(e),
                "confidence": 0,
                "actions": [],
                "reasoning": ["Error generating strategy"],
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_strategy(self, strategy_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a generated strategy"""
        try:
            # Find strategy to execute
            target_strategy = None
            
            if strategy_id:
                for strategy in self.active_strategies:
                    if strategy.get('strategy', {}).get('id') == strategy_id:
                        target_strategy = strategy
                        break
            else:
                if self.active_strategies:
                    target_strategy = self.active_strategies[-1]
            
            if not target_strategy:
                raise ValueError("No active strategy found for execution")
                
            strategy_data = target_strategy.get('strategy', {})
            
            # Check simulation mode
            if self.settings['simulation_mode']:
                logger.info("Running in simulation mode - no real transactions will be executed")
                
                # Update strategy status
                target_strategy['status'] = 'simulated'
                target_strategy['executed_at'] = datetime.now().isoformat()
                
                return {
                    "status": "simulated",
                    "strategy": strategy_data,
                    "message": "Strategy execution simulated - no real transactions were performed",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Real execution mode - execute actions
            execution_results = []
            
            # For demo, simulate successful execution
            target_strategy['status'] = 'executed'
            target_strategy['executed_at'] = datetime.now().isoformat()
            target_strategy['execution_results'] = execution_results
            
            return {
                "status": "executed",
                "execution_results": execution_results,
                "strategy": strategy_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Strategy execution error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_automated_actions(self) -> None:
        """Check if any automated actions should be triggered"""
        # Skip if auto-execution is disabled
        if not self.settings['auto_execution']:
            return
            
        try:
            # Check for emergency conditions first
            if self.settings['emergency_stop_loss'] and await self._check_emergency_conditions():
                await self._execute_emergency_actions()
                return
                
            # Check if we should generate a new strategy
            should_rebalance = await self._should_rebalance()
            
            if should_rebalance:
                logger.info("Auto-generating rebalance strategy based on current conditions")
                strategy = await self.generate_strategy(operation_type="rebalance")
                
                # Execute immediately if confidence is high enough
                if strategy.get('confidence', 0) >= 0.8:
                    logger.info("Auto-executing high-confidence strategy")
                    await self.execute_strategy()
                
        except Exception as e:
            logger.error(f"Automated actions error: {e}")
    
    async def _check_emergency_conditions(self) -> bool:
        """Check for emergency conditions that require immediate action"""
        try:
            # Check for significant SOL price drop
            if self.market_analysis.get('change_24h', 0) < -20:
                return True
                
            # Check for high risk score
            if self.risk_assessment.get('risk_score', 0) > 90:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Emergency condition check error: {e}")
            return False
    
    async def _execute_emergency_actions(self) -> None:
        """Execute emergency actions to protect the portfolio"""
        logger.warning("EMERGENCY ACTIONS TRIGGERED - Executing protective measures")
        
        try:
            # Generate emergency exit strategy
            strategy = await self.generate_strategy(operation_type="exit")
            
            # Execute immediately
            await self.execute_strategy()
            
            logger.critical("Emergency exit strategy executed")
            
        except Exception as e:
            logger.error(f"Emergency action execution error: {e}")
    
    async def _should_rebalance(self) -> bool:
        """Determine if portfolio should be rebalanced"""
        try:
            # Check time since last rebalance
            last_rebalance = None
            
            for strategy in reversed(self.active_strategies):
                if (strategy.get('strategy', {}).get('operation_type') == "rebalance" and 
                    strategy.get('status') == "executed"):
                    last_rebalance = strategy.get('executed_at')
                    break
            
            if last_rebalance:
                # Parse timestamp and check if enough time has passed
                from datetime import datetime
                last_time = datetime.fromisoformat(last_rebalance)
                time_diff = (datetime.now() - last_time).total_seconds()
                
                # Default 24 hours between rebalances
                if time_diff < 86400:
                    return False
            
            # Check for significant market changes
            if abs(self.market_analysis.get('change_24h', 0)) > 15:
                return True
                
            # Check for high risk score
            if self.risk_assessment.get('risk_score', 0) > 80:
                return True
                
            # Check for significant asset drift
            for asset in self.portfolio.get('assets', []):
                target_allocation = 25  # Simple equal allocation for example
                current_allocation = asset.get('allocation', 0)
                
                if abs(current_allocation - target_allocation) > 15:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Rebalance check error: {e}")
            return False
    
    async def get_portfolio_insights(self) -> Dict[str, Any]:
        """Get comprehensive insights about the portfolio"""
        try:
            # Combine data from different sources
            insights = {
                "portfolio_summary": {
                    "total_value": self.portfolio.get('total_value_usd', 0),
                    "asset_count": len(self.portfolio.get('assets', [])),
                    "updated_at": self.portfolio.get('updated_at'),
                    "network": "solana"
                },
                "asset_allocation": [
                    {
                        "symbol": asset.get('symbol'),
                        "allocation": asset.get('allocation'),
                        "value_usd": asset.get('value_usd'),
                        "type": asset.get('type')
                    }
                    for asset in self.portfolio.get('assets', [])
                ],
                "risk_metrics": {
                    "overall_risk": self.risk_assessment.get('risk_score', 50),
                    "risk_factors": self.risk_assessment.get('risk_factors', []),
                    "diversification": self.risk_assessment.get('diversification_score', 0)
                },
                "market_trends": {
                    "trends": self.market_analysis.get('trends', []),
                    "sentiment": self.market_analysis.get('confidence', 50),
                    "price_change": self.market_analysis.get('change_24h', 0)
                },
                "recent_strategies": self._get_recent_strategies(5),
                "generated_at": datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Portfolio insights error: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def _get_recent_strategies(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent strategies with simplified data"""
        recent = []
        
        for strategy in reversed(self.active_strategies):
            if len(recent) >= limit:
                break
                
            recent.append({
                "operation_type": strategy.get('strategy', {}).get('operation_type', 'unknown'),
                "confidence": strategy.get('strategy', {}).get('confidence', 0),
                "status": strategy.get('status'),
                "created_at": strategy.get('created_at'),
                "executed_at": strategy.get('executed_at', None)
            })
            
        return recent
    
    async def get_transaction_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transaction history"""
        try:
            # In production, this would fetch from Solana blockchain
            # For now, return the stored history
            
            history = list(reversed(self.transaction_history))[:limit]
            
            # Format for better readability
            formatted_history = []
            for tx in history:
                formatted_history.append({
                    "action_type": tx.get('action', {}).get('type'),
                    "asset": tx.get('action', {}).get('asset'),
                    "amount": tx.get('action', {}).get('amount'),
                    "status": tx.get('result', {}).get('status'),
                    "signature": tx.get('result', {}).get('signature'),
                    "timestamp": tx.get('timestamp'),
                    "network": "solana"
                })
                
            return formatted_history
            
        except Exception as e:
            logger.error(f"Transaction history error: {e}")
            return []
    
    async def update_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update system settings"""
        try:
            # Validate and apply new settings
            for key, value in new_settings.items():
                if key in self.settings:
                    # Type checking
                    if isinstance(self.settings[key], bool) and not isinstance(value, bool):
                        continue
                        
                    # Specific validation for certain settings
                    if key == 'risk_tolerance' and value not in ['low', 'medium', 'high']:
                        continue
                    
                    # Apply validated setting
                    self.settings[key] = value
                    logger.info(f"Updated setting {key} to {value}")
            
            return {
                "status": "success",
                "settings": self.settings,
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Settings update error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "updated_at": datetime.now().isoformat()
            }
    
    async def cleanup(self) -> None:
        """Clean up all resources"""
        try:
            # Clean up agents
            for name, agent in self.agents.items():
                try:
                    await agent.cleanup()
                    logger.info(f"Agent {name} cleaned up")
                except Exception as e:
                    logger.error(f"Error cleaning up agent {name}: {e}")
            
            # Clean up Solana connection
            if self.solana:
                await self.solana.close()
                logger.info("Solana connection closed")
            
            # Clean up market data
            if self.market_data:
                await self.market_data.close()
                logger.info("Market data connection closed")
            
            logger.info("Solana Asset Guardian shutdown complete")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
        return None