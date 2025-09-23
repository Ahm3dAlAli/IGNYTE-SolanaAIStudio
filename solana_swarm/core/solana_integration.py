"""
Production Solana Integration
Real blockchain integration with comprehensive error handling and monitoring.
"""

import asyncio
import logging
import time
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from contextlib import asynccontextmanager

import solana
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.rpc.types import RPCError, TxOpts
from solana.transaction import Transaction
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.system_program import TransferParams, transfer
from solders.keypair import Keypair as SoldersKeypair
from solders.pubkey import Pubkey
from solders.rpc.responses import GetAccountInfoResp
from spl.token.instructions import get_associated_token_address, create_associated_token_account
from spl.token.client import Token
from anchorpy import Provider, Wallet

from .exceptions import SolanaError, ConfigError
from .market_data import MarketDataManager

logger = logging.getLogger(__name__)

@dataclass
class SolanaConfig:
    """Production Solana configuration with validation."""
    
    # Network configuration
    network: str = "mainnet-beta"  # mainnet-beta, devnet, testnet
    rpc_url: str = ""  # Primary RPC endpoint
    ws_url: str = ""   # WebSocket endpoint
    backup_rpcs: List[str] = None  # Backup RPC endpoints
    
    # Wallet configuration
    private_key: str = ""  # Base58 encoded private key
    wallet_path: Optional[str] = None  # Path to keypair file
    
    # Transaction settings
    commitment: str = "confirmed"  # finalized, confirmed, processed
    max_retries: int = 3
    timeout: float = 30.0
    priority_fee: int = 0  # Micro-lamports
    
    # Rate limiting
    requests_per_second: int = 10
    burst_limit: int = 50
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.rpc_url:
            if self.network == "mainnet-beta":
                self.rpc_url = "https://api.mainnet-beta.solana.com"
            elif self.network == "devnet":
                self.rpc_url = "https://api.devnet.solana.com"
            else:
                raise ConfigError(f"RPC URL required for network: {self.network}")
        
        if not self.ws_url:
            self.ws_url = self.rpc_url.replace("https://", "wss://").replace("http://", "ws://")
        
        if not self.private_key and not self.wallet_path:
            raise ConfigError("Either private_key or wallet_path must be provided")
        
        if self.backup_rpcs is None:
            self.backup_rpcs = []

class SolanaConnection:
    """Production Solana connection with comprehensive error handling."""
    
    def __init__(self, config: SolanaConfig):
        """Initialize Solana connection."""
        self.config = config
        self.client: Optional[AsyncClient] = None
        self.backup_clients: List[AsyncClient] = []
        self.keypair: Optional[Keypair] = None
        self.public_key: Optional[PublicKey] = None
        
        # Rate limiting
        self._last_request_time = 0.0
        self._request_count = 0
        self._request_window_start = time.time()
        
        # Connection health
        self._is_connected = False
        self._last_health_check = 0.0
        self._health_check_interval = 30.0
        
        logger.info(f"Initializing Solana connection to {config.network}")
    
    async def initialize(self) -> None:
        """Initialize connection and validate setup."""
        try:
            # Initialize primary client
            self.client = AsyncClient(
                self.config.rpc_url,
                commitment=Commitment(self.config.commitment),
                timeout=self.config.timeout
            )
            
            # Initialize backup clients
            for backup_url in self.config.backup_rpcs:
                backup_client = AsyncClient(
                    backup_url,
                    commitment=Commitment(self.config.commitment),
                    timeout=self.config.timeout
                )
                self.backup_clients.append(backup_client)
            
            # Load keypair
            await self._load_keypair()
            
            # Validate connection
            await self._validate_connection()
            
            self._is_connected = True
            logger.info(f"Solana connection initialized successfully")
            logger.info(f"Public key: {self.public_key}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Solana connection: {e}")
            raise SolanaError(f"Connection initialization failed: {e}")
    
    async def _load_keypair(self) -> None:
        """Load keypair from private key or file."""
        try:
            if self.config.private_key:
                # Load from base58 private key
                keypair_bytes = solana.keypair.Keypair.from_secret_key(
                    base58.b58decode(self.config.private_key)
                ).secret_key
                self.keypair = Keypair.from_secret_key(keypair_bytes)
            elif self.config.wallet_path:
                # Load from file
                with open(self.config.wallet_path, 'r') as f:
                    secret_key = json.load(f)
                self.keypair = Keypair.from_secret_key(bytes(secret_key))
            
            self.public_key = self.keypair.public_key
            
        except Exception as e:
            raise SolanaError(f"Failed to load keypair: {e}")
    
    async def _validate_connection(self) -> None:
        """Validate connection by making test requests."""
        try:
            # Test basic connectivity
            response = await self.client.get_health()
            if response.value != "ok":
                raise SolanaError("RPC health check failed")
            
            # Test account access
            balance = await self.get_balance()
            logger.info(f"Wallet balance: {balance} SOL")
            
            # Test recent blockhash
            blockhash_resp = await self.client.get_latest_blockhash()
            if not blockhash_resp.value:
                raise SolanaError("Failed to get latest blockhash")
            
        except Exception as e:
            raise SolanaError(f"Connection validation failed: {e}")
    
    async def _rate_limit(self) -> None:
        """Implement rate limiting to prevent API abuse."""
        current_time = time.time()
        
        # Reset window if needed
        if current_time - self._request_window_start >= 1.0:
            self._request_count = 0
            self._request_window_start = current_time
        
        # Check rate limit
        if self._request_count >= self.config.requests_per_second:
            sleep_time = 1.0 - (current_time - self._request_window_start)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self._request_count = 0
                self._request_window_start = time.time()
        
        self._request_count += 1
    
    async def _execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic and failover."""
        clients = [self.client] + self.backup_clients
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            for client_idx, client in enumerate(clients):
                try:
                    await self._rate_limit()
                    
                    if client_idx > 0:
                        logger.warning(f"Using backup RPC #{client_idx}")
                    
                    result = await func(client, *args, **kwargs)
                    return result
                    
                except RPCError as e:
                    last_exception = e
                    logger.warning(f"RPC error on attempt {attempt + 1}: {e}")
                    continue
                except Exception as e:
                    last_exception = e
                    logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                    continue
            
            # Exponential backoff between full retry cycles
            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        raise SolanaError(f"All retry attempts failed. Last error: {last_exception}")
    
    async def get_balance(self, address: Optional[PublicKey] = None) -> Decimal:
        """Get SOL balance for an address."""
        target_address = address or self.public_key
        
        async def _get_balance(client: AsyncClient) -> Decimal:
            response = await client.get_balance(target_address)
            return Decimal(response.value) / Decimal(10**9)  # Convert lamports to SOL
        
        return await self._execute_with_retry(_get_balance)
    
    async def get_token_balance(
        self, 
        mint: PublicKey, 
        owner: Optional[PublicKey] = None
    ) -> Decimal:
        """Get SPL token balance."""
        owner_address = owner or self.public_key
        
        async def _get_token_balance(client: AsyncClient) -> Decimal:
            # Get associated token account
            ata = get_associated_token_address(owner_address, mint)
            
            try:
                response = await client.get_token_account_balance(ata)
                if response.value:
                    amount = response.value.amount
                    decimals = response.value.decimals
                    return Decimal(amount) / Decimal(10**decimals)
                else:
                    return Decimal(0)
            except Exception:
                return Decimal(0)  # Account doesn't exist or no balance
        
        return await self._execute_with_retry(_get_token_balance)
    
    async def send_transaction(
        self, 
        transaction: Transaction, 
        signers: Optional[List[Keypair]] = None
    ) -> str:
        """Send a transaction to the network."""
        if not signers:
            signers = [self.keypair]
        
        async def _send_transaction(client: AsyncClient) -> str:
            # Get latest blockhash
            blockhash_resp = await client.get_latest_blockhash()
            transaction.recent_blockhash = blockhash_resp.value.blockhash
            
            # Sign transaction
            transaction.sign(*signers)
            
            # Send transaction
            opts = TxOpts(
                skip_confirmation=False,
                skip_preflight=False,
                max_retries=self.config.max_retries
            )
            
            response = await client.send_transaction(transaction, opts=opts)
            return str(response.value)
        
        return await self._execute_with_retry(_send_transaction)
    
    async def transfer_sol(
        self, 
        recipient: Union[str, PublicKey], 
        amount: Union[float, Decimal]
    ) -> str:
        """Transfer SOL to another address."""
        if isinstance(recipient, str):
            recipient = PublicKey(recipient)
        
        lamports = int(Decimal(amount) * Decimal(10**9))
        
        # Create transfer instruction
        transfer_ix = transfer(
            TransferParams(
                from_pubkey=self.public_key,
                to_pubkey=recipient,
                lamports=lamports
            )
        )
        
        # Create and send transaction
        transaction = Transaction().add(transfer_ix)
        signature = await self.send_transaction(transaction)
        
        logger.info(f"Transferred {amount} SOL to {recipient}, signature: {signature}")
        return signature
    
    async def swap_tokens(
        self,
        input_mint: PublicKey,
        output_mint: PublicKey,
        amount: Decimal,
        slippage: float = 0.01
    ) -> Dict[str, Any]:
        """Swap tokens using Jupiter aggregator."""
        from ..integrations.jupiter.client import JupiterClient
        
        jupiter = JupiterClient(self)
        return await jupiter.swap(input_mint, output_mint, amount, slippage)
    
    async def get_account_info(self, address: PublicKey) -> Optional[Dict[str, Any]]:
        """Get account information."""
        async def _get_account_info(client: AsyncClient) -> Optional[Dict[str, Any]]:
            response = await client.get_account_info(address)
            if response.value:
                return {
                    "executable": response.value.executable,
                    "owner": str(response.value.owner),
                    "lamports": response.value.lamports,
                    "data": response.value.data,
                    "rent_epoch": response.value.rent_epoch
                }
            return None
        
        return await self._execute_with_retry(_get_account_info)
    
    async def get_token_accounts(
        self, 
        owner: Optional[PublicKey] = None
    ) -> List[Dict[str, Any]]:
        """Get all token accounts for an owner."""
        owner_address = owner or self.public_key
        
        async def _get_token_accounts(client: AsyncClient) -> List[Dict[str, Any]]:
            response = await client.get_token_accounts_by_owner(owner_address, {})
            accounts = []
            
            for account in response.value:
                account_info = account.account
                accounts.append({
                    "pubkey": str(account.pubkey),
                    "mint": str(account_info.data.parsed["info"]["mint"]),
                    "amount": account_info.data.parsed["info"]["tokenAmount"]["amount"],
                    "decimals": account_info.data.parsed["info"]["tokenAmount"]["decimals"],
                    "uiAmount": account_info.data.parsed["info"]["tokenAmount"]["uiAmount"]
                })
            
            return accounts
        
        return await self._execute_with_retry(_get_token_accounts)
    
    async def get_recent_performance_samples(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent network performance samples."""
        async def _get_performance(client: AsyncClient) -> List[Dict[str, Any]]:
            response = await client.get_recent_performance_samples(limit)
            return [
                {
                    "slot": sample.slot,
                    "numTransactions": sample.num_transactions,
                    "numSlots": sample.num_slots,
                    "samplePeriodSecs": sample.sample_period_secs
                }
                for sample in response.value
            ]
        
        return await self._execute_with_retry(_get_performance)
    
    async def get_network_stats(self) -> Dict[str, Any]:
        """Get comprehensive network statistics."""
        try:
            # Get multiple metrics in parallel
            tasks = [
                self.get_recent_performance_samples(1),
                self._execute_with_retry(lambda client: client.get_slot()),
                self._execute_with_retry(lambda client: client.get_epoch_info()),
                self._execute_with_retry(lambda client: client.get_supply()),
            ]
            
            performance, slot, epoch_info, supply = await asyncio.gather(*tasks)
            
            # Calculate TPS from performance sample
            tps = 0
            if performance and len(performance) > 0:
                sample = performance[0]
                tps = sample["numTransactions"] / sample["samplePeriodSecs"]
            
            return {
                "current_slot": slot.value,
                "current_epoch": epoch_info.value.epoch,
                "slot_index": epoch_info.value.slot_index,
                "slots_in_epoch": epoch_info.value.slots_in_epoch,
                "tps": round(tps, 2),
                "total_supply": supply.value.total / 10**9,  # Convert to SOL
                "circulating_supply": supply.value.circulating / 10**9,
                "network": self.config.network
            }
            
        except Exception as e:
            logger.error(f"Failed to get network stats: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Perform health check on the connection."""
        try:
            current_time = time.time()
            if current_time - self._last_health_check < self._health_check_interval:
                return self._is_connected
            
            # Test basic connectivity
            response = await self.client.get_health()
            self._is_connected = (response.value == "ok")
            self._last_health_check = current_time
            
            return self._is_connected
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self._is_connected = False
            return False
    
    async def close(self) -> None:
        """Close all connections."""
        try:
            if self.client:
                await self.client.close()
            
            for backup_client in self.backup_clients:
                await backup_client.close()
            
            self._is_connected = False
            logger.info("Solana connection closed")
            
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return None

class SolanaTransactionBuilder:
    """Helper class for building complex transactions."""
    
    def __init__(self, connection: SolanaConnection):
        self.connection = connection
        self.instructions = []
        self.signers = [connection.keypair]
    
    def add_instruction(self, instruction):
        """Add an instruction to the transaction."""
        self.instructions.append(instruction)
        return self
    
    def add_signer(self, signer: Keypair):
        """Add a signer to the transaction."""
        if signer not in self.signers:
            self.signers.append(signer)
        return self
    
    async def build_and_send(self) -> str:
        """Build and send the transaction."""
        if not self.instructions:
            raise SolanaError("No instructions added to transaction")
        
        transaction = Transaction()
        for ix in self.instructions:
            transaction.add(ix)
        
        signature = await self.connection.send_transaction(transaction, self.signers)
        
        # Clear for reuse
        self.instructions.clear()
        self.signers = [self.connection.keypair]
        
        return signature

@asynccontextmanager
async def create_solana_connection(config: SolanaConfig):
    """Create and manage a Solana connection with proper cleanup."""
    connection = SolanaConnection(config)
    try:
        await connection.initialize()
        yield connection
    finally:
        await connection.close()

# Utility functions for common operations
async def get_token_mint_info(connection: SolanaConnection, mint: PublicKey) -> Dict[str, Any]:
    """Get token mint information."""
    try:
        token = Token(connection.client, mint, connection.keypair)
        mint_info = await token.get_mint_info()
        
        return {
            "mint": str(mint),
            "decimals": mint_info.decimals,
            "supply": str(mint_info.supply),
            "mint_authority": str(mint_info.mint_authority) if mint_info.mint_authority else None,
            "freeze_authority": str(mint_info.freeze_authority) if mint_info.freeze_authority else None,
            "is_initialized": mint_info.is_initialized
        }
    except Exception as e:
        logger.error(f"Failed to get mint info for {mint}: {e}")
        return {"error": str(e)}

async def find_associated_token_address(owner: PublicKey, mint: PublicKey) -> PublicKey:
    """Find associated token account address."""
    return get_associated_token_address(owner, mint)

# Common Solana addresses and constants
class SolanaAddresses:
    """Common Solana program addresses."""
    
    SYSTEM_PROGRAM = PublicKey("11111111111111111111111111111111")
    TOKEN_PROGRAM = PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
    ASSOCIATED_TOKEN_PROGRAM = PublicKey("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
    RENT_PROGRAM = PublicKey("SysvarRent111111111111111111111111111111111")
    CLOCK_PROGRAM = PublicKey("SysvarC1ock11111111111111111111111111111111")
    
    # Major DEX program IDs
    JUPITER_PROGRAM = PublicKey("JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4")
    RAYDIUM_PROGRAM = PublicKey("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
    ORCA_PROGRAM = PublicKey("9W959DqEETiGZocYWCQPaJ6sBmUzgfxXfqGeTEdp3aQP")
    SERUM_PROGRAM = PublicKey("9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin")
    
    # Stablecoins
    USDC_MINT = PublicKey("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    USDT_MINT = PublicKey("Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB")
    
    # Wrapped SOL
    WSOL_MINT = PublicKey("So11111111111111111111111111111111111111112")