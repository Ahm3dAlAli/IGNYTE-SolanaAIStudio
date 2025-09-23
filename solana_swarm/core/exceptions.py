"""
Custom exceptions for the Solana Swarm Intelligence Framework.
"""

class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass

class SolanaError(Exception):
    """Exception for Solana blockchain interaction errors."""
    pass

class LLMError(Exception):
    """Exception for LLM-related errors."""
    pass

class ConfigError(Exception):
    """Exception for configuration-related errors."""
    pass

class MarketDataError(Exception):
    """Exception for market data-related errors."""
    pass

class PluginError(Exception):
    """Exception for plugin-related errors."""
    pass

class DEXError(SolanaError):
    """Exception for DEX-related errors."""
    pass

class JupiterError(DEXError):
    """Exception for Jupiter aggregator errors."""
    pass

class RaydiumError(DEXError):
    """Exception for Raydium DEX errors."""
    pass

class OrcaError(DEXError):
    """Exception for Orca DEX errors."""
    pass

class TransactionError(SolanaError):
    """Exception for transaction-related errors."""
    pass

class NetworkError(SolanaError):
    """Exception for network connectivity issues."""
    pass

class WalletError(SolanaError):
    """Exception for wallet-related errors."""
    pass

class TokenError(SolanaError):
    """Exception for SPL token-related errors."""
    pass

class InsufficientFundsError(SolanaError):
    """Exception for insufficient funds errors."""
    pass

class SlippageError(DEXError):
    """Exception for slippage-related errors."""
    pass

class SecurityError(AgentError):
    """Exception for security-related errors."""
    pass

class ValidationError(AgentError):
    """Exception for validation errors."""
    pass

class ConsensusError(AgentError):
    """Exception for consensus-related errors."""
    pass

class MemoryError(AgentError):
    """Exception for memory management errors."""
    pass