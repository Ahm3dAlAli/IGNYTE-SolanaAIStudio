# XRPL Integration for Solana Swarm

This module provides integration with the XRP Ledger (XRPL) for issuing and managing fungible tokens.

## Features

- **Token Issuance**: Create fungible tokens with custom settings
- **Wallet Management**: Manage cold (issuer) and hot (distributor) wallets
- **Trust Lines**: Create and manage trust lines between accounts
- **Token Transfers**: Send tokens between accounts
- **Balance Queries**: Check token and XRP balances
- **Yield-Bearing Tokens**: Support for tokens with transfer fees

## Architecture

### Components

```
xrpl/
├── __init__.py       # Module exports
├── client.py         # XRPL client for network operations
├── token_issuer.py   # Token issuance and management
└── types.py          # Data structures and types
```

### Client (`client.py`)

The `XRPLClient` class provides low-level operations:
- Connect to XRPL networks (testnet/mainnet)
- Create and manage wallets
- Configure account settings
- Create trust lines
- Send tokens
- Query balances and account info

### Token Issuer (`token_issuer.py`)

The `TokenIssuer` class provides high-level token operations:
- Create token pairs (cold + hot wallets)
- Issue tokens with initial supply
- Create complete token chains
- Save/load wallet configurations
- Manage token balances

### Types (`types.py`)

Data structures for:
- `WalletPair`: Cold and hot wallet information
- `TokenConfig`: Token configuration parameters
- `TrustLineConfig`: Trust line settings
- `TokenBalance`: Token balance information

## Quick Start

### 1. Install Dependencies

```bash
pip install xrpl-py>=2.5.0
```

### 2. Create Tokens

```python
from solana_swarm.integrations.xrpl import XRPLClient, TokenIssuer
from decimal import Decimal

# Initialize
client = XRPLClient(network_url="https://s.altnet.rippletest.net:51234")
issuer = TokenIssuer(client)

# Create token chain
tokens = issuer.create_yield_bearing_chain(
    rlusd_supply=Decimal("1000000"),
    musd_supply=Decimal("1000000"),
    rlusd_plus_supply=Decimal("1000000")
)

# Save configuration
issuer.save_wallet_config("wallets.json")
```

### 3. Use Tokens

```python
# Load configuration
issuer.load_wallet_config("wallets.json")

# Get balances
balances = issuer.get_all_balances()
print(balances)
```

## Token Chain

The integration creates a yield-bearing token chain:

```
XRP → RLUSD (RLD) → mUSD (MUD) → RLUSD+ (RLP)
```

- **RLUSD**: Entry stablecoin (0% transfer fee)
- **mUSD**: Intermediate token (0% transfer fee)
- **RLUSD+**: Yield-bearing token (1% transfer fee)

## Examples

### Example 1: Issue Single Token

```python
from solana_swarm.integrations.xrpl import XRPLClient, TokenIssuer
from decimal import Decimal

client = XRPLClient()
issuer = TokenIssuer(client)

# Create a single token
wallet_pair = issuer.create_token_pair(
    token_name="MyToken",
    currency_code="MTK",
    initial_supply=Decimal("1000000"),
    transfer_fee=0.0
)

print(f"Issuer: {wallet_pair.cold_address}")
print(f"Distributor: {wallet_pair.hot_address}")
```

### Example 2: Send Tokens

```python
from solana_swarm.integrations.xrpl import XRPLClient
from decimal import Decimal

client = XRPLClient()

# Load hot wallet
hot_wallet = client.get_wallet_from_seed("sEdV...")

# Send tokens
result = client.send_token(
    from_wallet=hot_wallet,
    to_address="rUserAddress...",
    amount=Decimal("100"),
    currency="MTK",
    issuer="rIssuerAddress...",
    destination_tag=1
)
```

### Example 3: Create Trust Line

```python
from solana_swarm.integrations.xrpl import XRPLClient
from solana_swarm.integrations.xrpl.types import TrustLineConfig
from decimal import Decimal

client = XRPLClient()

# User wallet
user_wallet = client.get_wallet_from_seed("sEdU...")

# Create trust line
config = TrustLineConfig(
    account_address=user_wallet.classic_address,
    issuer_address="rIssuerAddress...",
    currency_code="MTK",
    limit=Decimal("1000000")
)

result = client.create_trust_line(config, user_wallet)
```

## Configuration

### Account Settings

**Cold Wallet (Issuer)**:
- `default_ripple=True`: Enable token transfers between users
- `require_dest_tag=True`: Require destination tags
- `disallow_xrp=True`: Prevent XRP payments
- `transfer_rate`: Set transfer fee (0-1)
- `tick_size`: DEX tick size (5-15)

**Hot Wallet (Distributor)**:
- `default_ripple=False`: Disable rippling
- `require_auth=True`: Prevent accidental trust lines
- `require_dest_tag=True`: Require destination tags
- `disallow_xrp=True`: Prevent XRP payments

### Network URLs

**Testnet** (default):
```python
client = XRPLClient("https://s.altnet.rippletest.net:51234")
```

**Mainnet**:
```python
client = XRPLClient("https://xrplcluster.com")
```

## API Reference

See the main documentation at `docs/XRPL_TOKENS.md` for complete API reference.

### Key Methods

**XRPLClient**:
- `create_wallet()`: Generate new testnet wallet
- `configure_account(wallet, **settings)`: Configure account
- `create_trust_line(config, wallet)`: Create trust line
- `send_token(...)`: Send tokens
- `get_account_lines(address)`: Get trust lines
- `get_xrp_balance(address)`: Get XRP balance

**TokenIssuer**:
- `create_token_pair(...)`: Create single token
- `create_yield_bearing_chain(...)`: Create token chain
- `save_wallet_config(filepath)`: Save wallets
- `load_wallet_config(filepath)`: Load wallets
- `get_all_balances()`: Get all balances

## Testing

Run the test script:

```bash
# Issue tokens first
python scripts/issue_xrpl_tokens.py --save-config

# Run tests
python scripts/test_xrpl_tokens.py --config xrpl_wallets.json
```

## Security

### Best Practices

1. **Cold Wallets**: Keep seeds offline and secure
2. **Hot Wallets**: Monitor activity and set limits
3. **Testnet First**: Always test on testnet before mainnet
4. **Validation**: Verify all transaction results
5. **Backups**: Backup wallet configurations securely

### Production Checklist

- [ ] Cold wallet seeds stored securely offline
- [ ] Hot wallet monitoring implemented
- [ ] Rate limiting configured
- [ ] Alert system set up
- [ ] Backup procedures tested
- [ ] Network switched to mainnet
- [ ] Transaction validation enabled
- [ ] Error handling implemented

## Resources

- [XRPL Documentation](https://xrpl.org/)
- [xrpl-py Library](https://github.com/XRPLF/xrpl-py)
- [Testnet Explorer](https://testnet.xrpl.org/)
- [Testnet Faucet](https://xrpl.org/xrp-testnet-faucet.html)

## License

Part of IGNYTE Solana AI Studio project.
