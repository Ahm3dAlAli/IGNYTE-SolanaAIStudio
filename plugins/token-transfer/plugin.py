"""
Token Transfer Plugin for Solana Swarm Intelligence
Handles secure token transfers with validation
"""

import logging
from typing import Dict, Any, Optional
from solana_swarm.plugins.base import AgentPlugin, PluginConfig
from solana_swarm.core.agent import AgentConfig
from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig
from solana_swarm.core.market_data import MarketDataManager
from solana_swarm.core.llm_provider import create_llm_provider, LLMConfig
import os
import re

logger = logging.getLogger(__name__)

class TokenTransferPlugin(AgentPlugin):
    """Secure token transfer plugin with validation"""
    
    def __init__(self, agent_config: AgentConfig, plugin_config: PluginConfig):
        super().__init__(agent_config, plugin_config)
        self.max_transfer_amount = float(self.plugin_config.custom_settings.get('max_transfer_amount', 1000))
        self.require_confirmation = self.plugin_config.custom_settings.get('require_confirmation', True)
        self.solana_connection = None
        self.market_data = None
        self.llm_provider = None
        self.logger = logger
        
    async def initialize(self) -> None:
        """Initialize token transfer agent"""
        # Initialize Solana connection
        config = SolanaConfig(
            network=os.getenv('SOLANA_NETWORK', 'devnet'),
            wallet_path=os.getenv('SOLANA_WALLET_PATH'),
            private_key=os.getenv('SOLANA_PRIVATE_KEY')
        )
        self.solana_connection = SolanaConnection(config)
        
        # Initialize market data for price validation
        self.market_data = MarketDataManager()
        await self.market_data._ensure_session()
        
        # Initialize LLM for transfer validation
        llm_config = LLMConfig(
            provider=os.getenv('LLM_PROVIDER', 'openrouter'),
            api_key=os.getenv('LLM_API_KEY'),
            model=os.getenv('LLM_MODEL', 'anthropic/claude-3.5-sonnet'),
            temperature=0.2  # Low temperature for security validation
        )
        self.llm_provider = create_llm_provider(llm_config)
        
        self.logger.info("Token transfer agent initialized successfully")
        
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate and validate transfer request"""
        try:
            recipient = context.get('recipient', '')
            amount = float(context.get('amount', 0))
            token = context.get('token', 'SOL').upper()
            
            # Basic validation
            validation_result = await self._validate_transfer(recipient, amount, token)
            
            if not validation_result['is_valid']:
                return {
                    'valid': False,
                    'reason': validation_result['reason'],
                    'confidence': 0.0
                }
            
            # Get current balance
            if token == 'SOL':
                balance = await self.solana_connection.get_balance()
            else:
                # For SPL tokens, would need mint address
                balance = 0.0  # Simplified for demo
            
            # LLM security analysis
            security_analysis = await self._analyze_transfer_security(recipient, amount, token, balance)
            
            return {
                'valid': True,
                'security_analysis': security_analysis,
                'current_balance': balance,
                'transfer_amount': amount,
                'recipient': recipient,
                'token': token,
                'confidence': security_analysis.get('confidence', 0.8),
                'recommendation': security_analysis.get('recommendation', 'proceed')
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating transfer: {str(e)}")
            return {'error': str(e)}
    
    async def _validate_transfer(self, recipient: str, amount: float, token: str) -> Dict[str, Any]:
        """Validate transfer parameters"""
        # Check recipient address format
        if not self._is_valid_solana_address(recipient):
            return {
                'is_valid': False,
                'reason': 'Invalid Solana address format'
            }
        
        # Check amount limits
        if amount <= 0:
            return {
                'is_valid': False,
                'reason': 'Amount must be positive'
            }
        
        if amount > self.max_transfer_amount:
            return {
                'is_valid': False,
                'reason': f'Amount exceeds maximum transfer limit of {self.max_transfer_amount}'
            }
        
        # Check token validity
        valid_tokens = ['SOL', 'USDC', 'USDT']  # Extend as needed
        if token not in valid_tokens:
            return {
                'is_valid': False,
                'reason': f'Token {token} not supported'
            }
        
        return {'is_valid': True, 'reason': 'Valid transfer parameters'}
    
    def _is_valid_solana_address(self, address: str) -> bool:
        """Validate Solana address format"""
        if not address or len(address) < 32 or len(address) > 44:
            return False
        
        # Check for base58 characters
        base58_pattern = r'^[1-9A-HJ-NP-Za-km-z]+
        return bool(re.match(base58_pattern, address))
    
    async def _analyze_transfer_security(self, recipient: str, amount: float, token: str, balance: float) -> Dict[str, Any]:
        """Analyze transfer security with LLM"""
        try:
            # Get current token price for USD value calculation
            token_data = await self.market_data.get_token_price(token.lower())
            usd_value = amount * token_data.get('price', 0)
            
            prompt = f"""
            Analyze this Solana token transfer for security risks:
            
            Transfer Details:
            - Token: {token}
            - Amount: {amount} {token}
            - USD Value: ${usd_value:.2f}
            - Recipient: {recipient}
            - Current Balance: {balance} {token}
            - Percentage of Balance: {(amount/balance*100) if balance > 0 else 0:.1f}%
            
            Security Considerations:
            1. Is the amount reasonable for a legitimate transfer?
            2. Does the recipient address look suspicious?
            3. Is this a large percentage of the wallet balance?
            4. Are there any red flags?
            
            Provide analysis as JSON with:
            - recommendation: "approve" | "review" | "reject"
            - confidence: float (0-1)
            - risk_level: "low" | "medium" | "high"
            - reasoning: string
            - security_score: int (0-100)
            """
            
            response = await self.llm_provider.query(prompt, expect_json=True)
            return response
            
        except Exception as e:
            self.logger.error(f"Security analysis failed: {e}")
            return {
                "recommendation": "reject",
                "confidence": 0.0,
                "risk_level": "high",
                "reasoning": f"Security analysis failed: {str(e)}",
                "security_score": 0
            }
    
    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute token transfer"""
        try:
            if action.get('type') != 'transfer':
                return {'error': 'Invalid action type for transfer agent'}
            
            recipient = action.get('recipient', '')
            amount = float(action.get('amount', 0))
            token = action.get('token', 'SOL').upper()
            
            # Re-validate before execution
            validation = await self._validate_transfer(recipient, amount, token)
            if not validation['is_valid']:
                return {'error': f"Transfer validation failed: {validation['reason']}"}
            
            # Execute transfer based on token type
            if token == 'SOL':
                result = await self.solana_connection.transfer_sol(recipient, amount)
            else:
                # For SPL tokens, need mint address mapping
                mint_addresses = {
                    'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                    'USDT': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
                }
                
                if token in mint_addresses:
                    result = await self.solana_connection.transfer_token(
                        mint_addresses[token],
                        recipient,
                        amount,
                        6 if token in ['USDC', 'USDT'] else 9
                    )
                else:
                    return {'error': f'Mint address not found for token {token}'}
            
            return {
                'status': 'success',
                'transaction': result,
                'amount': amount,
                'token': token,
                'recipient': recipient
            }
            
        except Exception as e:
            self.logger.error(f"Transfer execution failed: {str(e)}")
            return {'error': str(e)}
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self.solana_connection:
            await self.solana_connection.close()
        if self.market_data:
            await self.market_data.close()
        if self.llm_provider:
            await self.llm_provider.close()
