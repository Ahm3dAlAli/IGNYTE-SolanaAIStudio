"""
XRPL Client for interacting with the XRP Ledger.
"""

import asyncio
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging

try:
    from xrpl.clients import JsonRpcClient, WebsocketClient
    from xrpl.wallet import Wallet
    from xrpl.models.transactions import (
        AccountSet,
        Payment,
        TrustSet,
        AccountSetAsfFlag,
        AccountSetFlag
    )
    from xrpl.models.amounts import IssuedCurrencyAmount
    from xrpl.models.requests import (
        AccountLines,
        GatewayBalances,
        AccountInfo
    )
    from xrpl.transaction import (
        submit_and_wait,
        safe_sign_and_autofill_transaction
    )
    from xrpl.account import get_balance
    XRPL_AVAILABLE = True
except ImportError:
    XRPL_AVAILABLE = False

from .types import TokenConfig, TrustLineConfig, TokenBalance, WalletPair

logger = logging.getLogger(__name__)


class XRPLClient:
    """
    Client for interacting with the XRP Ledger.

    This client provides methods for:
    - Connecting to XRPL testnet/mainnet
    - Managing wallets
    - Issuing tokens
    - Creating trust lines
    - Checking balances
    """

    def __init__(self, network_url: str = "https://s.altnet.rippletest.net:51234"):
        """
        Initialize XRPL client.

        Args:
            network_url: The XRPL network URL (default: testnet)
        """
        if not XRPL_AVAILABLE:
            raise ImportError(
                "xrpl-py library is not installed. "
                "Install it with: pip install xrpl-py"
            )

        self.network_url = network_url
        self.client = JsonRpcClient(network_url)
        logger.info(f"XRPL Client initialized with network: {network_url}")

    def create_wallet(self) -> Wallet:
        """
        Generate a new wallet on the testnet.

        Returns:
            A new Wallet instance with funded testnet XRP
        """
        from xrpl.wallet import generate_faucet_wallet

        logger.info("Generating new wallet from faucet...")
        wallet = generate_faucet_wallet(self.client, debug=True)
        logger.info(f"Wallet created: {wallet.classic_address}")
        return wallet

    def get_wallet_from_seed(self, seed: str) -> Wallet:
        """
        Create a wallet instance from a seed.

        Args:
            seed: The wallet seed/secret

        Returns:
            Wallet instance
        """
        return Wallet.from_seed(seed)

    def configure_account(
        self,
        wallet: Wallet,
        default_ripple: bool = False,
        require_dest_tag: bool = True,
        disallow_xrp: bool = True,
        require_auth: bool = False,
        transfer_rate: float = 0.0,
        tick_size: int = 5,
        domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configure account settings.

        Args:
            wallet: The wallet to configure
            default_ripple: Enable DefaultRipple flag (required for issuers)
            require_dest_tag: Require destination tags
            disallow_xrp: Disallow incoming XRP payments
            require_auth: Require authorization for trust lines
            transfer_rate: Transfer fee (0-1, where 0.01 = 1%)
            tick_size: Tick size for DEX (5-15 recommended)
            domain: Domain name in hex

        Returns:
            Transaction result
        """
        logger.info(f"Configuring account: {wallet.classic_address}")

        # Build AccountSet transaction
        tx_flags = 0
        if require_dest_tag:
            tx_flags |= AccountSetFlag.ASF_REQUIRE_DEST
        if disallow_xrp:
            tx_flags |= AccountSetFlag.ASF_DISALLOW_XRP

        set_flag = None
        if default_ripple:
            set_flag = AccountSetAsfFlag.ASF_DEFAULT_RIPPLE
        elif require_auth:
            set_flag = AccountSetAsfFlag.ASF_REQUIRE_AUTH

        account_set_tx = AccountSet(
            account=wallet.classic_address,
            set_flag=set_flag,
            flags=tx_flags,
            tick_size=tick_size,
        )

        # Add domain if provided
        if domain:
            account_set_tx.domain = domain

        # Add transfer rate if specified (convert percentage to XRPL format)
        if transfer_rate > 0:
            # XRPL uses 1,000,000,000 as 0% fee, 1,010,000,000 as 1% fee
            account_set_tx.transfer_rate = int(1_000_000_000 * (1 + transfer_rate))

        # Sign and submit
        signed_tx = safe_sign_and_autofill_transaction(account_set_tx, wallet, self.client)
        result = submit_and_wait(signed_tx, self.client)

        logger.info(f"Account configured. TX: {result.result['hash']}")
        return result.result

    def create_trust_line(
        self,
        config: TrustLineConfig,
        wallet: Wallet
    ) -> Dict[str, Any]:
        """
        Create a trust line from one account to another.

        Args:
            config: Trust line configuration
            wallet: The wallet creating the trust line

        Returns:
            Transaction result
        """
        logger.info(
            f"Creating trust line from {config.account_address} "
            f"to {config.issuer_address} for {config.currency_code}"
        )

        trust_set_tx = TrustSet(
            account=wallet.classic_address,
            limit_amount=IssuedCurrencyAmount(
                currency=config.currency_code,
                issuer=config.issuer_address,
                value=str(config.limit)
            )
        )

        signed_tx = safe_sign_and_autofill_transaction(trust_set_tx, wallet, self.client)
        result = submit_and_wait(signed_tx, self.client)

        logger.info(f"Trust line created. TX: {result.result['hash']}")
        return result.result

    def send_token(
        self,
        from_wallet: Wallet,
        to_address: str,
        amount: Decimal,
        currency: str,
        issuer: str,
        destination_tag: int = 1
    ) -> Dict[str, Any]:
        """
        Send tokens from one account to another.

        Args:
            from_wallet: The wallet sending tokens
            to_address: The recipient address
            amount: Amount to send
            currency: Currency code
            issuer: Token issuer address
            destination_tag: Destination tag (required if recipient requires it)

        Returns:
            Transaction result
        """
        logger.info(
            f"Sending {amount} {currency} from {from_wallet.classic_address} "
            f"to {to_address}"
        )

        payment_tx = Payment(
            account=from_wallet.classic_address,
            destination=to_address,
            amount=IssuedCurrencyAmount(
                currency=currency,
                issuer=issuer,
                value=str(amount)
            ),
            destination_tag=destination_tag
        )

        signed_tx = safe_sign_and_autofill_transaction(payment_tx, from_wallet, self.client)
        result = submit_and_wait(signed_tx, self.client)

        logger.info(f"Token sent. TX: {result.result['hash']}")
        return result.result

    def get_account_lines(self, address: str) -> List[Dict[str, Any]]:
        """
        Get all trust lines for an account.

        Args:
            address: The account address

        Returns:
            List of trust lines
        """
        request = AccountLines(
            account=address,
            ledger_index="validated"
        )
        response = self.client.request(request)
        return response.result.get("lines", [])

    def get_gateway_balances(
        self,
        issuer_address: str,
        hotwallet_addresses: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get balances from the perspective of a token issuer.

        Args:
            issuer_address: The issuer address
            hotwallet_addresses: Optional list of hot wallet addresses

        Returns:
            Gateway balances
        """
        request = GatewayBalances(
            account=issuer_address,
            ledger_index="validated"
        )

        if hotwallet_addresses:
            request.hotwallet = hotwallet_addresses

        response = self.client.request(request)
        return response.result

    def get_xrp_balance(self, address: str) -> Decimal:
        """
        Get XRP balance for an account.

        Args:
            address: The account address

        Returns:
            XRP balance in drops
        """
        balance = get_balance(address, self.client)
        return Decimal(balance) / Decimal(1_000_000)  # Convert drops to XRP

    def get_account_info(self, address: str) -> Dict[str, Any]:
        """
        Get account information.

        Args:
            address: The account address

        Returns:
            Account info
        """
        request = AccountInfo(
            account=address,
            ledger_index="validated"
        )
        response = self.client.request(request)
        return response.result
