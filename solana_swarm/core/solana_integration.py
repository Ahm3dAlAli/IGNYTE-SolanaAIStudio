"""
Solana Protocol Integration Module
Handles interactions with Solana blockchain, DEXs, and DeFi protocols
"""

import logging
import os
import base64
import json
from typing import Dict, Any, Optional, List
import asyncio
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator

try:
    from solana.rpc.async_api import AsyncClient
    from solana.rpc.commitment import Commitment
    from solana.keypair import Keypair
    from solana.system_program import TransferParams, transfer
    from solana.transaction import Transaction
    from solana.publickey import PublicKey
    from spl.token.instructions import transfer as spl_transfer, TransferParams as SPLTransferParams
    from spl.token.core import _TokenCore
    import base58
except ImportError:
    raise ImportError("Please install solana dependencies: pip install solana solders spl-token")

from aiohttp.client_exceptions import ClientError

logger = logging.getLogger(__name__)

class SolanaError(Exception):
    pass

class SolanaConnectionError(SolanaError):
    pass

class SolanaRPCError(SolanaError):
    pass

class InvalidKeyError(SolanaError):
    pass

@dataclass
class SolanaConfig:
    """Solana connection configuration."""
    network: str = Field(default="devnet", description="Network to connect to (devnet/mainnet)")
    rpc_url: str = Field(default="https://api.devnet.solana.com", description="RPC endpoint")
    wallet_path: Optional[str] = Field(None, description="Path to wallet keypair file")
    private_key: Optional[str] = Field(None, description="Base58 encoded private key")
    commitment: str = Field(default="confirmed", description="Transaction commitment level")

    def __post_init__(self):
        """Post-initialization validation"""
        if not self.wallet_path and not self.private_key:
            raise ValueError("Either wallet_path or private_key must be provided")
        
        if self.network == "mainnet" and "devnet" in self.rpc_url:
            self.rpc_url = "https://api.mainnet-beta.solana.com"
        elif self.network == "devnet" and "mainnet" in self.rpc_url:
            self.rpc_url = "https://api.devnet.solana.com"

class SolanaConnection:
    """
    Solana connection handler using solana-py
    """
    def __init__(self, config: SolanaConfig):
        """Initialize Solana connection"""
        self.config = config
        self.client = AsyncClient(config.rpc_url, commitment=Commitment(config.commitment))
        self.keypair = None
        self._initialize_keypair()
        
        logger.info(f"Initialized Solana connection to {config.network} using {config.rpc_url}")

    def _initialize_keypair(self):
        """Initialize keypair from config"""
        try:
            if self.config.wallet_path and os.path.exists(self.config.wallet_path):
                # Load from wallet file
                with open(self.config.wallet_path, 'r') as f:
                    wallet_data = json.load(f)
                    self.keypair = Keypair.from_secret_key(bytes(wallet_data))
            elif self.config.private_key:
                # Load from base58 private key
                secret_key = base58.b58decode(self.config.private_key)
                self.keypair = Keypair.from_secret_key(secret_key)
            else:
                raise ValueError("No valid keypair source provided")
                
            logger.info(f"Loaded keypair: {self.keypair.public_key}")
            
        except Exception as e:
            logger.error(f"Failed to initialize keypair: {str(e)}")
            raise SolanaConnectionError(f"Keypair initialization failed: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def get_balance(self, public_key: Optional[PublicKey] = None) -> float:
        """Get SOL balance for a public key"""
        try:
            key = public_key or self.keypair.public_key
            response = await self.client.get_balance(key)
            # Convert lamports to SOL
            return response.value / 1_000_000_000
        except Exception as e:
            logger.error(f"Failed to get balance: {str(e)}")
            raise SolanaRPCError(str(e))

    async def get_token_balance(self, token_mint: str, owner: Optional[PublicKey] = None) -> float:
        """Get SPL token balance"""
        try:
            owner_key = owner or self.keypair.public_key
            mint_key = PublicKey(token_mint)
            
            # Get token accounts by owner
            response = await self.client.get_token_accounts_by_owner(
                owner_key,
                {"mint": mint_key}
            )
            
            if not response.value:
                return 0.0
                
            # Get token account info
            token_account = response.value[0].pubkey
            account_info = await self.client.get_token_account_balance(token_account)
            
            return float(account_info.value.amount) / (10 ** account_info.value.decimals)
            
        except Exception as e:
            logger.error(f"Failed to get token balance: {str(e)}")
            raise SolanaRPCError(str(e))

    async def transfer_sol(self, recipient: str, amount: float) -> Dict[str, Any]:
        """Transfer SOL to another address"""
        try:
            recipient_key = PublicKey(recipient)
            lamports = int(amount * 1_000_000_000)  # Convert SOL to lamports
            
            # Create transfer instruction
            transfer_instruction = transfer(
                TransferParams(
                    from_pubkey=self.keypair.public_key,
                    to_pubkey=recipient_key,
                    lamports=lamports
                )
            )
            
            # Create and send transaction
            transaction = Transaction().add(transfer_instruction)
            response = await self.client.send_transaction(
                transaction, 
                self.keypair,
                opts={"skip_confirmation": False, "preflight_commitment": "confirmed"}
            )
            
            signature = response.value
            
            # Wait for confirmation
            await self.client.confirm_transaction(signature)
            
            explorer_url = self._get_explorer_url(signature)
            
            return {
                "status": "success",
                "signature": signature,
                "explorer_url": explorer_url,
                "amount": amount,
                "recipient": recipient
            }
            
        except Exception as e:
            logger.error(f"SOL transfer failed: {str(e)}")
            raise SolanaRPCError(f"Transfer failed: {str(e)}")

    async def transfer_token(self, token_mint: str, recipient: str, amount: float, decimals: int = 6) -> Dict[str, Any]:
        """Transfer SPL token to another address"""
        try:
            mint_key = PublicKey(token_mint)
            recipient_key = PublicKey(recipient)
            token_amount = int(amount * (10 ** decimals))
            
            # Find source token account
            source_accounts = await self.client.get_token_accounts_by_owner(
                self.keypair.public_key,
                {"mint": mint_key}
            )
            
            if not source_accounts.value:
                raise SolanaError("No token account found for this mint")
                
            source_account = source_accounts.value[0].pubkey
            
            # Find or create destination token account
            dest_accounts = await self.client.get_token_accounts_by_owner(
                recipient_key,
                {"mint": mint_key}
            )
            
            if dest_accounts.value:
                dest_account = dest_accounts.value[0].pubkey
            else:
                # Would need to create associated token account
                raise SolanaError("Destination token account does not exist")
            
            # Create transfer instruction
            transfer_instruction = spl_transfer(
                SPLTransferParams(
                    program_id=_TokenCore.TOKEN_PROGRAM_ID,
                    source=source_account,
                    dest=dest_account,
                    owner=self.keypair.public_key,
                    amount=token_amount
                )
            )
            
            # Create and send transaction
            transaction = Transaction().add(transfer_instruction)
            response = await self.client.send_transaction(
                transaction, 
                self.keypair,
                opts={"skip_confirmation": False, "preflight_commitment": "confirmed"}
            )
            
            signature = response.value
            
            # Wait for confirmation
            await self.client.confirm_transaction(signature)
            
            explorer_url = self._get_explorer_url(signature)
            
            return {
                "status": "success",
                "signature": signature,
                "explorer_url": explorer_url,
                "amount": amount,
                "token_mint": token_mint,
                "recipient": recipient
            }
            
        except Exception as e:
            logger.error(f"Token transfer failed: {str(e)}")
            raise SolanaRPCError(f"Token transfer failed: {str(e)}")

    async def swap_tokens_jupiter(self, input_mint: str, output_mint: str, amount: float, slippage: float = 0.5) -> Dict[str, Any]:
        """Swap tokens using Jupiter aggregator"""
        try:
            # This would integrate with Jupiter API
            # For now, return a mock response
            logger.info(f"Swapping {amount} {input_mint} to {output_mint} via Jupiter")
            
            return {
                "status": "success",
                "input_amount": amount,
                "output_amount": amount * 0.998,  # Mock output with 0.2% fee
                "input_mint": input_mint,
                "output_mint": output_mint,
                "signature": "mock_signature",
                "explorer_url": self._get_explorer_url("mock_signature")
            }
            
        except Exception as e:
            logger.error(f"Jupiter swap failed: {str(e)}")
            raise SolanaRPCError(f"Swap failed: {str(e)}")

    async def get_token_price(self, token_mint: str) -> Dict[str, Any]:
        """Get token price from various sources"""
        try:
            # This would integrate with price APIs like CoinGecko, Jupiter, etc.
            # For now, return mock data
            mock_prices = {
                "So11111111111111111111111111111111111111112": {"price": 100.0, "symbol": "SOL"},  # SOL
                "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {"price": 1.0, "symbol": "USDC"},   # USDC
                "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {"price": 1.0, "symbol": "USDT"},   # USDT
            }
            
            if token_mint in mock_prices:
                return mock_prices[token_mint]
            else:
                return {"price": 1.0, "symbol": "UNKNOWN"}
                
        except Exception as e:
            logger.error(f"Failed to get token price: {str(e)}")
            raise SolanaRPCError(str(e))

    async def get_network_stats(self) -> Dict[str, Any]:
        """Get Solana network statistics"""
        try:
            # Get recent performance samples
            performance = await self.client.get_recent_performance_samples(limit=1)
            slot_info = await self.client.get_slot()
            
            return {
                "current_slot": slot_info.value,
                "tps": performance.value[0].num_transactions / performance.value[0].sample_period_secs if performance.value else 0,
                "network": self.config.network,
                "commitment": self.config.commitment
            }
            
        except Exception as e:
            logger.error(f"Failed to get network stats: {str(e)}")
            return {"error": str(e)}

    def _get_explorer_url(self, signature: str) -> str:
        """Get Solana explorer URL for transaction"""
        base_url = "https://explorer.solana.com/tx"
        cluster = "" if self.config.network == "mainnet" else f"?cluster={self.config.network}"
        return f"{base_url}/{signature}{cluster}"

    async def close(self):
        """Close the connection"""
        if self.client:
            await self.client.close()

async def create_solana_connection(config: SolanaConfig) -> SolanaConnection:
    """Create a new Solana connection from configuration"""
    try:
        connection = SolanaConnection(config)
        
        # Test connection by getting balance
        balance = await connection.get_balance()
        logger.info(f"Connection successful. Wallet balance: {balance} SOL")
        
        return connection
    except Exception as e:
        logger.error(f"Failed to create Solana connection: {str(e)}")
        raise SolanaConnectionError(f"Connection failed: {str(e)}")

        