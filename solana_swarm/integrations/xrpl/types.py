"""
Type definitions for XRPL integration.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass
class WalletPair:
    """
    Represents a cold and hot wallet pair for token issuance.

    Attributes:
        cold_address: The cold wallet address (issuer)
        cold_seed: The cold wallet seed/secret
        hot_address: The hot wallet address (distributor)
        hot_seed: The hot wallet seed/secret
    """
    cold_address: str
    cold_seed: str
    hot_address: str
    hot_seed: str


@dataclass
class TokenConfig:
    """
    Configuration for a token to be issued on XRPL.

    Attributes:
        currency_code: 3-character currency code (e.g., "USD", "FOO")
        issuer_address: The cold address issuing the token
        initial_supply: Initial supply to mint to hot wallet
        transfer_fee: Transfer fee percentage (0-1, where 0.01 = 1%)
        tick_size: Tick size for DEX trading (recommended: 5)
        domain: Domain name in hex (for verification)
        require_destination_tag: Whether to require destination tags
        disallow_xrp: Whether to disallow XRP payments to this address
    """
    currency_code: str
    issuer_address: str
    initial_supply: Decimal
    transfer_fee: float = 0.0
    tick_size: int = 5
    domain: str = "6578616D706C652E636F6D"  # "example.com" in hex
    require_destination_tag: bool = True
    disallow_xrp: bool = True


@dataclass
class TrustLineConfig:
    """
    Configuration for creating a trust line between addresses.

    Attributes:
        account_address: The address creating the trust line
        issuer_address: The address being trusted
        currency_code: The currency code to trust
        limit: Maximum amount willing to hold
    """
    account_address: str
    issuer_address: str
    currency_code: str
    limit: Decimal


@dataclass
class TokenBalance:
    """
    Represents a token balance on XRPL.

    Attributes:
        currency: Currency code
        value: Balance value
        account: Account address
        issuer: Token issuer address (if applicable)
    """
    currency: str
    value: Decimal
    account: str
    issuer: Optional[str] = None
