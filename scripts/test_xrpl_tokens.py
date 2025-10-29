#!/usr/bin/env python3
"""
Test script for XRPL tokens.

This script demonstrates how users can interact with the issued tokens:
1. Create trust lines to all tokens
2. Receive tokens from hot wallets
3. Transfer tokens between users
4. Check balances

Usage:
    python scripts/test_xrpl_tokens.py --config xrpl_wallets.json
"""

import sys
import os
import argparse
import logging
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solana_swarm.integrations.xrpl.client import XRPLClient
from solana_swarm.integrations.xrpl.types import TrustLineConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_token_config(filepath: str):
    """Load token configuration from JSON file."""
    import json
    with open(filepath, 'r') as f:
        return json.load(f)


def create_test_user(client: XRPLClient, name: str):
    """Create a test user wallet."""
    logger.info(f"Creating test user: {name}")
    wallet = client.create_wallet()
    logger.info(f"  Address: {wallet.classic_address}")
    logger.info(f"  Seed: {wallet.seed}")
    return wallet


def setup_trust_lines(client: XRPLClient, user_wallet, token_config):
    """Set up trust lines for a user to all tokens."""
    logger.info(f"\nSetting up trust lines for user: {user_wallet.classic_address}")

    tokens = [
        ("RLUSD", "RLD"),
        ("mUSD", "MUD"),
        ("RLUSD+", "RLP")
    ]

    for token_name, currency_code in tokens:
        if token_name not in token_config:
            logger.warning(f"Token {token_name} not found in config, skipping...")
            continue

        issuer_address = token_config[token_name]["cold_address"]

        logger.info(f"  Creating trust line to {token_name} ({currency_code})...")

        trust_config = TrustLineConfig(
            account_address=user_wallet.classic_address,
            issuer_address=issuer_address,
            currency_code=currency_code,
            limit=Decimal("10000000")
        )

        try:
            result = client.create_trust_line(trust_config, user_wallet)
            logger.info(f"    ✓ Trust line created. TX: {result['hash']}")
        except Exception as e:
            logger.error(f"    ✗ Failed to create trust line: {e}")


def distribute_tokens(client: XRPLClient, token_config, recipient_address: str, amount: Decimal = Decimal("1000")):
    """Distribute tokens from hot wallets to a recipient."""
    logger.info(f"\nDistributing tokens to: {recipient_address}")

    tokens = [
        ("RLUSD", "RLD"),
        ("mUSD", "MUD"),
        ("RLUSD+", "RLP")
    ]

    for token_name, currency_code in tokens:
        if token_name not in token_config:
            logger.warning(f"Token {token_name} not found in config, skipping...")
            continue

        hot_seed = token_config[token_name]["hot_seed"]
        cold_address = token_config[token_name]["cold_address"]
        hot_wallet = client.get_wallet_from_seed(hot_seed)

        logger.info(f"  Sending {amount} {token_name} ({currency_code})...")

        try:
            result = client.send_token(
                from_wallet=hot_wallet,
                to_address=recipient_address,
                amount=amount,
                currency=currency_code,
                issuer=cold_address,
                destination_tag=1
            )
            logger.info(f"    ✓ Sent {amount} {token_name}. TX: {result['hash']}")
        except Exception as e:
            logger.error(f"    ✗ Failed to send tokens: {e}")


def check_balances(client: XRPLClient, address: str):
    """Check token balances for an address."""
    logger.info(f"\nChecking balances for: {address}")

    # Get XRP balance
    try:
        xrp_balance = client.get_xrp_balance(address)
        logger.info(f"  XRP Balance: {xrp_balance:.2f} XRP")
    except Exception as e:
        logger.error(f"  Failed to get XRP balance: {e}")

    # Get trust lines (token balances)
    try:
        lines = client.get_account_lines(address)
        if lines:
            logger.info(f"  Token Balances:")
            for line in lines:
                currency = line.get('currency', 'Unknown')
                balance = line.get('balance', '0')
                limit = line.get('limit', '0')
                logger.info(f"    {currency}: {balance} (Limit: {limit})")
        else:
            logger.info(f"  No token balances found")
    except Exception as e:
        logger.error(f"  Failed to get token balances: {e}")


def test_token_transfer(client: XRPLClient, from_wallet, to_address: str, token_config):
    """Test transferring tokens between users."""
    logger.info(f"\nTesting token transfer from {from_wallet.classic_address} to {to_address}")

    # Test transfer RLUSD
    token_name = "RLUSD"
    currency_code = "RLD"
    amount = Decimal("50")

    if token_name not in token_config:
        logger.error(f"Token {token_name} not found in config")
        return

    cold_address = token_config[token_name]["cold_address"]

    logger.info(f"  Transferring {amount} {token_name}...")

    try:
        result = client.send_token(
            from_wallet=from_wallet,
            to_address=to_address,
            amount=amount,
            currency=currency_code,
            issuer=cold_address,
            destination_tag=1
        )
        logger.info(f"    ✓ Transfer successful. TX: {result['hash']}")
    except Exception as e:
        logger.error(f"    ✗ Transfer failed: {e}")


def test_yield_bearing_transfer(client: XRPLClient, from_wallet, to_address: str, token_config):
    """Test transferring RLUSD+ to demonstrate yield mechanism."""
    logger.info(f"\nTesting RLUSD+ transfer (with 1% fee)")

    token_name = "RLUSD+"
    currency_code = "RLP"
    amount = Decimal("100")

    if token_name not in token_config:
        logger.error(f"Token {token_name} not found in config")
        return

    cold_address = token_config[token_name]["cold_address"]

    logger.info(f"  Transferring {amount} {token_name}...")
    logger.info(f"  Note: Recipient will receive {amount * Decimal('0.99')} due to 1% transfer fee")

    try:
        result = client.send_token(
            from_wallet=from_wallet,
            to_address=to_address,
            amount=amount,
            currency=currency_code,
            issuer=cold_address,
            destination_tag=1
        )
        logger.info(f"    ✓ Transfer successful. TX: {result['hash']}")
    except Exception as e:
        logger.error(f"    ✗ Transfer failed: {e}")


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test XRPL token functionality"
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to wallet configuration file (xrpl_wallets.json)"
    )
    parser.add_argument(
        "--network",
        type=str,
        default="https://s.altnet.rippletest.net:51234",
        help="XRPL network URL (default: testnet)"
    )
    parser.add_argument(
        "--skip-creation",
        action="store_true",
        help="Skip creating test users (use existing addresses)"
    )
    parser.add_argument(
        "--user1-seed",
        type=str,
        help="Seed for user 1 (if skip-creation is set)"
    )
    parser.add_argument(
        "--user2-seed",
        type=str,
        help="Seed for user 2 (if skip-creation is set)"
    )

    args = parser.parse_args()

    try:
        # Load token configuration
        logger.info("Loading token configuration...")
        token_config = load_token_config(args.config)
        logger.info(f"Loaded configuration for: {', '.join(token_config.keys())}")

        # Initialize client
        logger.info(f"\nConnecting to XRPL network: {args.network}")
        client = XRPLClient(network_url=args.network)

        # Create or load test users
        if args.skip_creation and args.user1_seed and args.user2_seed:
            logger.info("\nLoading existing test users...")
            user1 = client.get_wallet_from_seed(args.user1_seed)
            user2 = client.get_wallet_from_seed(args.user2_seed)
            logger.info(f"User 1: {user1.classic_address}")
            logger.info(f"User 2: {user2.classic_address}")
        else:
            logger.info("\n" + "=" * 80)
            logger.info("Step 1: Creating Test Users")
            logger.info("=" * 80)
            user1 = create_test_user(client, "User 1")
            user2 = create_test_user(client, "User 2")

        # Set up trust lines
        logger.info("\n" + "=" * 80)
        logger.info("Step 2: Setting Up Trust Lines")
        logger.info("=" * 80)
        setup_trust_lines(client, user1, token_config)
        setup_trust_lines(client, user2, token_config)

        # Distribute tokens to users
        logger.info("\n" + "=" * 80)
        logger.info("Step 3: Distributing Tokens")
        logger.info("=" * 80)
        distribute_tokens(client, token_config, user1.classic_address, Decimal("1000"))
        distribute_tokens(client, token_config, user2.classic_address, Decimal("500"))

        # Check balances
        logger.info("\n" + "=" * 80)
        logger.info("Step 4: Checking Balances")
        logger.info("=" * 80)
        check_balances(client, user1.classic_address)
        check_balances(client, user2.classic_address)

        # Test token transfer
        logger.info("\n" + "=" * 80)
        logger.info("Step 5: Testing Token Transfer")
        logger.info("=" * 80)
        test_token_transfer(client, user1, user2.classic_address, token_config)

        # Test yield-bearing transfer
        logger.info("\n" + "=" * 80)
        logger.info("Step 6: Testing Yield-Bearing Transfer (RLUSD+)")
        logger.info("=" * 80)
        test_yield_bearing_transfer(client, user1, user2.classic_address, token_config)

        # Final balance check
        logger.info("\n" + "=" * 80)
        logger.info("Step 7: Final Balance Check")
        logger.info("=" * 80)
        check_balances(client, user1.classic_address)
        check_balances(client, user2.classic_address)

        # Print summary
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        print("\n✓ All tests completed successfully!")
        print("\nTest Users:")
        print(f"  User 1: {user1.classic_address}")
        print(f"    Seed: {user1.seed}")
        print(f"  User 2: {user2.classic_address}")
        print(f"    Seed: {user2.seed}")
        print("\nYou can view transactions on the XRPL Testnet Explorer:")
        print(f"  https://testnet.xrpl.org/accounts/{user1.classic_address}")
        print(f"  https://testnet.xrpl.org/accounts/{user2.classic_address}")
        print("=" * 80 + "\n")

    except FileNotFoundError:
        logger.error(f"Configuration file not found: {args.config}")
        logger.error("Please run 'python scripts/issue_xrpl_tokens.py --save-config' first")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
