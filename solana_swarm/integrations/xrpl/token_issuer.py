"""
Token Issuer for creating and managing fungible tokens on XRPL.
Specifically handles RLUSD, mUSD, and RLUSD+ yield-bearing tokens.
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import json

from .client import XRPLClient
from .types import TokenConfig, TrustLineConfig, WalletPair

logger = logging.getLogger(__name__)


class TokenIssuer:
    """
    Handles the issuance of fungible tokens on XRPL.

    This class manages the complete lifecycle of token issuance including:
    - Creating and configuring issuer (cold) and distributor (hot) wallets
    - Setting up trust lines between wallets
    - Issuing initial token supply
    - Creating the yield-bearing token chain: XRP -> RLUSD -> mUSD -> RLUSD+
    """

    def __init__(self, client: XRPLClient):
        """
        Initialize the token issuer.

        Args:
            client: XRPL client instance
        """
        self.client = client
        self.tokens: Dict[str, WalletPair] = {}
        logger.info("TokenIssuer initialized")

    def create_token_pair(
        self,
        token_name: str,
        currency_code: str,
        initial_supply: Decimal,
        transfer_fee: float = 0.0,
        use_existing_cold: Optional[str] = None,
        use_existing_hot: Optional[str] = None
    ) -> WalletPair:
        """
        Create a new token with cold and hot wallet pair.

        Args:
            token_name: Name/identifier for this token
            currency_code: 3-character currency code
            initial_supply: Initial supply to mint
            transfer_fee: Transfer fee percentage (0-1)
            use_existing_cold: Optional seed for existing cold wallet
            use_existing_hot: Optional seed for existing hot wallet

        Returns:
            WalletPair with cold and hot wallet info
        """
        logger.info(f"Creating token pair for {token_name} ({currency_code})")

        # Create or load cold wallet (issuer)
        if use_existing_cold:
            cold_wallet = self.client.get_wallet_from_seed(use_existing_cold)
            logger.info(f"Using existing cold wallet: {cold_wallet.classic_address}")
        else:
            cold_wallet = self.client.create_wallet()
            logger.info(f"Created new cold wallet: {cold_wallet.classic_address}")

        # Create or load hot wallet (distributor)
        if use_existing_hot:
            hot_wallet = self.client.get_wallet_from_seed(use_existing_hot)
            logger.info(f"Using existing hot wallet: {hot_wallet.classic_address}")
        else:
            hot_wallet = self.client.create_wallet()
            logger.info(f"Created new hot wallet: {hot_wallet.classic_address}")

        # Configure cold wallet (issuer settings)
        logger.info("Configuring cold wallet as token issuer...")
        self.client.configure_account(
            wallet=cold_wallet,
            default_ripple=True,  # Required for tokens to be transferable between users
            require_dest_tag=True,
            disallow_xrp=True,
            transfer_rate=transfer_fee,
            tick_size=5,
            domain="6578616D706C652E636F6D"  # "example.com" in hex
        )

        # Configure hot wallet (distributor settings)
        logger.info("Configuring hot wallet as token distributor...")
        self.client.configure_account(
            wallet=hot_wallet,
            default_ripple=False,  # Hot wallet should not enable rippling
            require_dest_tag=True,
            disallow_xrp=True,
            require_auth=True,  # Prevent accidental trust lines to hot wallet
            tick_size=5,
            domain="6578616D706C652E636F6D"
        )

        # Create trust line from hot to cold
        logger.info("Creating trust line from hot to cold wallet...")
        trust_config = TrustLineConfig(
            account_address=hot_wallet.classic_address,
            issuer_address=cold_wallet.classic_address,
            currency_code=currency_code,
            limit=Decimal("10000000000")  # Large limit
        )
        self.client.create_trust_line(trust_config, hot_wallet)

        # Issue initial supply to hot wallet
        logger.info(f"Issuing initial supply of {initial_supply} {currency_code}...")
        self.client.send_token(
            from_wallet=cold_wallet,
            to_address=hot_wallet.classic_address,
            amount=initial_supply,
            currency=currency_code,
            issuer=cold_wallet.classic_address,
            destination_tag=1
        )

        # Store wallet pair
        wallet_pair = WalletPair(
            cold_address=cold_wallet.classic_address,
            cold_seed=cold_wallet.seed,
            hot_address=hot_wallet.classic_address,
            hot_seed=hot_wallet.seed
        )
        self.tokens[token_name] = wallet_pair

        logger.info(f"Token {token_name} created successfully!")
        return wallet_pair

    def create_yield_bearing_chain(
        self,
        rlusd_supply: Decimal = Decimal("1000000"),
        musd_supply: Decimal = Decimal("1000000"),
        rlusd_plus_supply: Decimal = Decimal("1000000")
    ) -> Dict[str, WalletPair]:
        """
        Create the complete yield-bearing token chain:
        XRP -> RLUSD -> mUSD -> RLUSD+

        Args:
            rlusd_supply: Initial supply of RLUSD
            musd_supply: Initial supply of mUSD
            rlusd_plus_supply: Initial supply of RLUSD+

        Returns:
            Dictionary mapping token names to WalletPair instances
        """
        logger.info("=" * 60)
        logger.info("Creating Yield-Bearing Token Chain")
        logger.info("Chain: XRP -> RLUSD -> mUSD -> RLUSD+")
        logger.info("=" * 60)

        tokens = {}

        # Step 1: Create RLUSD (XRP -> RLUSD)
        logger.info("\n[1/3] Creating RLUSD token...")
        rlusd_pair = self.create_token_pair(
            token_name="RLUSD",
            currency_code="RLD",  # 3-char code for RLUSD
            initial_supply=rlusd_supply,
            transfer_fee=0.0  # No transfer fee
        )
        tokens["RLUSD"] = rlusd_pair
        logger.info(f"✓ RLUSD created")
        logger.info(f"  Issuer (Cold): {rlusd_pair.cold_address}")
        logger.info(f"  Distributor (Hot): {rlusd_pair.hot_address}")

        # Step 2: Create mUSD (RLUSD -> mUSD)
        logger.info("\n[2/3] Creating mUSD token...")
        musd_pair = self.create_token_pair(
            token_name="mUSD",
            currency_code="MUD",  # 3-char code for mUSD
            initial_supply=musd_supply,
            transfer_fee=0.0
        )
        tokens["mUSD"] = musd_pair
        logger.info(f"✓ mUSD created")
        logger.info(f"  Issuer (Cold): {musd_pair.cold_address}")
        logger.info(f"  Distributor (Hot): {musd_pair.hot_address}")

        # Step 3: Create RLUSD+ (mUSD -> RLUSD+)
        logger.info("\n[3/3] Creating RLUSD+ yield-bearing token...")
        rlusd_plus_pair = self.create_token_pair(
            token_name="RLUSD+",
            currency_code="RLP",  # 3-char code for RLUSD+
            initial_supply=rlusd_plus_supply,
            transfer_fee=0.01  # 1% transfer fee for yield generation
        )
        tokens["RLUSD+"] = rlusd_plus_pair
        logger.info(f"✓ RLUSD+ created")
        logger.info(f"  Issuer (Cold): {rlusd_plus_pair.cold_address}")
        logger.info(f"  Distributor (Hot): {rlusd_plus_pair.hot_address}")

        # Step 4: Create cross-token trust lines for the chain
        logger.info("\n[4/4] Setting up cross-token trust lines...")

        # RLUSD hot wallet trusts mUSD
        logger.info("  Creating trust line: RLUSD hot -> mUSD cold")
        rlusd_hot_wallet = self.client.get_wallet_from_seed(rlusd_pair.hot_seed)
        self.client.create_trust_line(
            TrustLineConfig(
                account_address=rlusd_pair.hot_address,
                issuer_address=musd_pair.cold_address,
                currency_code="MUD",
                limit=Decimal("10000000000")
            ),
            rlusd_hot_wallet
        )

        # mUSD hot wallet trusts RLUSD
        logger.info("  Creating trust line: mUSD hot -> RLUSD cold")
        musd_hot_wallet = self.client.get_wallet_from_seed(musd_pair.hot_seed)
        self.client.create_trust_line(
            TrustLineConfig(
                account_address=musd_pair.hot_address,
                issuer_address=rlusd_pair.cold_address,
                currency_code="RLD",
                limit=Decimal("10000000000")
            ),
            musd_hot_wallet
        )

        # mUSD hot wallet trusts RLUSD+
        logger.info("  Creating trust line: mUSD hot -> RLUSD+ cold")
        self.client.create_trust_line(
            TrustLineConfig(
                account_address=musd_pair.hot_address,
                issuer_address=rlusd_plus_pair.cold_address,
                currency_code="RLP",
                limit=Decimal("10000000000")
            ),
            musd_hot_wallet
        )

        # RLUSD+ hot wallet trusts mUSD
        logger.info("  Creating trust line: RLUSD+ hot -> mUSD cold")
        rlusd_plus_hot_wallet = self.client.get_wallet_from_seed(rlusd_plus_pair.hot_seed)
        self.client.create_trust_line(
            TrustLineConfig(
                account_address=rlusd_plus_pair.hot_address,
                issuer_address=musd_pair.cold_address,
                currency_code="MUD",
                limit=Decimal("10000000000")
            ),
            rlusd_plus_hot_wallet
        )

        logger.info("\n" + "=" * 60)
        logger.info("✓ Yield-Bearing Token Chain Created Successfully!")
        logger.info("=" * 60)

        # Store all tokens
        self.tokens.update(tokens)

        return tokens

    def save_wallet_config(self, filepath: str = "xrpl_wallets.json"):
        """
        Save wallet configuration to a JSON file.

        Args:
            filepath: Path to save the configuration
        """
        config = {}
        for token_name, wallet_pair in self.tokens.items():
            config[token_name] = {
                "cold_address": wallet_pair.cold_address,
                "cold_seed": wallet_pair.cold_seed,
                "hot_address": wallet_pair.hot_address,
                "hot_seed": wallet_pair.hot_seed
            }

        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Wallet configuration saved to {filepath}")

    def load_wallet_config(self, filepath: str = "xrpl_wallets.json"):
        """
        Load wallet configuration from a JSON file.

        Args:
            filepath: Path to load the configuration from
        """
        with open(filepath, 'r') as f:
            config = json.load(f)

        for token_name, wallet_data in config.items():
            self.tokens[token_name] = WalletPair(
                cold_address=wallet_data["cold_address"],
                cold_seed=wallet_data["cold_seed"],
                hot_address=wallet_data["hot_address"],
                hot_seed=wallet_data["hot_seed"]
            )

        logger.info(f"Wallet configuration loaded from {filepath}")

    def get_all_balances(self) -> Dict[str, Dict[str, any]]:
        """
        Get balances for all tokens.

        Returns:
            Dictionary mapping token names to their balance information
        """
        balances = {}

        for token_name, wallet_pair in self.tokens.items():
            logger.info(f"Fetching balances for {token_name}...")

            # Get hot wallet balances (trust lines)
            hot_lines = self.client.get_account_lines(wallet_pair.hot_address)

            # Get cold wallet balances (gateway perspective)
            gateway_balances = self.client.get_gateway_balances(
                wallet_pair.cold_address,
                [wallet_pair.hot_address]
            )

            balances[token_name] = {
                "hot_wallet": {
                    "address": wallet_pair.hot_address,
                    "trust_lines": hot_lines,
                    "xrp_balance": float(self.client.get_xrp_balance(wallet_pair.hot_address))
                },
                "cold_wallet": {
                    "address": wallet_pair.cold_address,
                    "gateway_balances": gateway_balances,
                    "xrp_balance": float(self.client.get_xrp_balance(wallet_pair.cold_address))
                }
            }

        return balances

    def print_summary(self):
        """
        Print a summary of all created tokens and their addresses.
        """
        print("\n" + "=" * 80)
        print("XRPL Token Summary")
        print("=" * 80)

        for token_name, wallet_pair in self.tokens.items():
            print(f"\n{token_name}:")
            print(f"  Cold Wallet (Issuer):      {wallet_pair.cold_address}")
            print(f"  Cold Wallet Seed:          {wallet_pair.cold_seed}")
            print(f"  Hot Wallet (Distributor):  {wallet_pair.hot_address}")
            print(f"  Hot Wallet Seed:           {wallet_pair.hot_seed}")

        print("\n" + "=" * 80)
        print("Token Chain: XRP -> RLUSD (RLD) -> mUSD (MUD) -> RLUSD+ (RLP)")
        print("=" * 80)
        print("\nAll tokens are now available on XRPL Testnet!")
        print("Users can create trust lines to these tokens and start using them.")
        print("=" * 80 + "\n")
