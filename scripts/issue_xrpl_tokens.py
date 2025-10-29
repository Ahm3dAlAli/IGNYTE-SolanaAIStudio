#!/usr/bin/env python3
"""
Script to issue RLUSD, mUSD, and RLUSD+ tokens on XRPL Testnet.

This script creates a complete yield-bearing token chain:
- RLUSD: A stablecoin pegged to USD
- mUSD: A medium token for conversion
- RLUSD+: A yield-bearing version of RLUSD with 1% transfer fee

Usage:
    python scripts/issue_xrpl_tokens.py [--supply SUPPLY] [--save-config]

Options:
    --supply SUPPLY      Initial supply for each token (default: 1000000)
    --save-config        Save wallet configuration to file
    --load-config FILE   Load existing wallet configuration
"""

import sys
import os
import argparse
import logging
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solana_swarm.integrations.xrpl.client import XRPLClient
from solana_swarm.integrations.xrpl.token_issuer import TokenIssuer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to issue tokens."""
    parser = argparse.ArgumentParser(
        description="Issue RLUSD, mUSD, and RLUSD+ tokens on XRPL Testnet"
    )
    parser.add_argument(
        "--supply",
        type=float,
        default=1000000,
        help="Initial supply for each token (default: 1000000)"
    )
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Save wallet configuration to xrpl_wallets.json"
    )
    parser.add_argument(
        "--load-config",
        type=str,
        help="Load existing wallet configuration from file"
    )
    parser.add_argument(
        "--network",
        type=str,
        default="https://s.altnet.rippletest.net:51234",
        help="XRPL network URL (default: testnet)"
    )

    args = parser.parse_args()

    try:
        logger.info("Initializing XRPL Client...")
        client = XRPLClient(network_url=args.network)

        logger.info("Initializing Token Issuer...")
        issuer = TokenIssuer(client)

        if args.load_config:
            logger.info(f"Loading wallet configuration from {args.load_config}...")
            issuer.load_wallet_config(args.load_config)
            logger.info("Configuration loaded successfully!")
        else:
            logger.info("Creating yield-bearing token chain...")
            supply = Decimal(str(args.supply))

            # Create the complete token chain
            tokens = issuer.create_yield_bearing_chain(
                rlusd_supply=supply,
                musd_supply=supply,
                rlusd_plus_supply=supply
            )

            # Save configuration if requested
            if args.save_config:
                config_file = "xrpl_wallets.json"
                issuer.save_wallet_config(config_file)
                logger.info(f"Configuration saved to {config_file}")

        # Print summary
        issuer.print_summary()

        # Get and display balances
        logger.info("\nFetching current balances...")
        balances = issuer.get_all_balances()

        print("\n" + "=" * 80)
        print("Current Balances")
        print("=" * 80)

        for token_name, balance_info in balances.items():
            print(f"\n{token_name}:")
            print(f"  Hot Wallet XRP Balance: {balance_info['hot_wallet']['xrp_balance']:.2f} XRP")
            print(f"  Cold Wallet XRP Balance: {balance_info['cold_wallet']['xrp_balance']:.2f} XRP")

            if balance_info['hot_wallet']['trust_lines']:
                print(f"  Hot Wallet Trust Lines:")
                for line in balance_info['hot_wallet']['trust_lines']:
                    print(f"    - {line.get('currency', 'Unknown')}: {line.get('balance', '0')}")

        print("\n" + "=" * 80)
        print("Token Issuance Complete!")
        print("=" * 80)

        print("\nNext Steps:")
        print("1. Users can create trust lines to these tokens")
        print("2. Hot wallets can distribute tokens to users")
        print("3. Users can trade tokens in the XRPL DEX")
        print("4. RLUSD+ generates yield through the 1% transfer fee")
        print("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Error issuing tokens: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
