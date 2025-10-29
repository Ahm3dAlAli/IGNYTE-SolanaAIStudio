# XRPL Quick Start Guide

Get started with XRPL yield-bearing tokens in 5 minutes!

## Prerequisites

- Python 3.8+
- pip package manager
- Internet connection

## Step 1: Install Dependencies

```bash
pip install xrpl-py>=2.5.0
```

Or install all project dependencies:

```bash
pip install -r requirements.txt
```

## Step 2: Issue Tokens

Create RLUSD, mUSD, and RLUSD+ tokens on XRPL testnet:

```bash
python scripts/issue_xrpl_tokens.py --save-config
```

This will:
- Create 6 wallets (cold + hot for each token)
- Configure account settings
- Create trust lines between wallets
- Issue initial token supplies
- Save configuration to `xrpl_wallets.json`

**Expected output:**
```
============================================================
✓ Yield-Bearing Token Chain Created Successfully!
============================================================

XRPL Token Summary
============================================================

RLUSD:
  Cold Wallet (Issuer):      rN7n7otQDd6FczFgLdlqtyMVrn3HMgCYK9
  Hot Wallet (Distributor):  rLHzPsX6oXkzU9S7J7TTgfuaBUVLxKb2Ta

mUSD:
  Cold Wallet (Issuer):      rPEPPER7kfTD9w2To4CQk6UCfuHM9c6GDY
  Hot Wallet (Distributor):  rU6K7V3Po4snVhBBaU29sesqs2qTQJWDw1

RLUSD+:
  Cold Wallet (Issuer):      rLHzPsX6oXkzU9S7J7tygaBuVLxKb2Ta
  Hot Wallet (Distributor):  rN7n7otQDd6FczFgLdlqtyMVrn3HMgCYK9
```

## Step 3: Test the Tokens

Run the test script to create test users and demonstrate token functionality:

```bash
python scripts/test_xrpl_tokens.py --config xrpl_wallets.json
```

This will:
1. Create 2 test users with testnet XRP
2. Set up trust lines to all tokens
3. Distribute tokens to users
4. Test token transfers
5. Demonstrate the yield-bearing mechanism
6. Display final balances

## Step 4: Use the Tokens

### Python API

```python
from solana_swarm.integrations.xrpl import XRPLClient, TokenIssuer
from decimal import Decimal

# Initialize client
client = XRPLClient()

# Load wallet configuration
issuer = TokenIssuer(client)
issuer.load_wallet_config("xrpl_wallets.json")

# Check balances
balances = issuer.get_all_balances()
print(balances)

# Send tokens to a user
hot_wallet = client.get_wallet_from_seed("YOUR_HOT_WALLET_SEED")
client.send_token(
    from_wallet=hot_wallet,
    to_address="rUserAddress...",
    amount=Decimal("100"),
    currency="RLD",  # RLUSD
    issuer="rIssuerAddress...",
    destination_tag=1
)
```

### Command Line

Create a simple transfer script:

```python
#!/usr/bin/env python3
from solana_swarm.integrations.xrpl import XRPLClient
from decimal import Decimal
import sys

# Usage: python transfer.py <recipient> <amount>
recipient = sys.argv[1]
amount = Decimal(sys.argv[2])

client = XRPLClient()
hot_wallet = client.get_wallet_from_seed("YOUR_HOT_WALLET_SEED")

result = client.send_token(
    from_wallet=hot_wallet,
    to_address=recipient,
    amount=amount,
    currency="RLD",
    issuer="YOUR_COLD_WALLET_ADDRESS",
    destination_tag=1
)

print(f"✓ Sent {amount} RLUSD to {recipient}")
print(f"  TX: {result['hash']}")
```

## Understanding the Token Chain

```
XRP → RLUSD (RLD) → mUSD (MUD) → RLUSD+ (RLP)
```

### Token Flow

1. **XRP to RLUSD**: Users convert XRP to RLUSD (entry point)
2. **RLUSD to mUSD**: Users convert RLUSD to mUSD (intermediate)
3. **mUSD to RLUSD+**: Users convert mUSD to RLUSD+ (yield-bearing)

### Yield Generation

RLUSD+ generates yield through:
- **1% Transfer Fee**: Every transfer incurs a 1% fee
- **Fee Accumulation**: Fees accumulate in the ecosystem
- **Redistribution**: Can be redistributed to holders as yield

### Example: Earning Yield

```python
# User A holds 1000 RLUSD+
# User A sends 100 RLUSD+ to User B
# User B receives 99 RLUSD+ (1% fee)
# The 1 RLUSD+ fee stays in the ecosystem as yield
```

## Viewing on XRPL Explorer

View your transactions on the testnet explorer:

1. Go to https://testnet.xrpl.org/
2. Enter your wallet address
3. View transactions, balances, and trust lines

## Common Commands

### Issue tokens with custom supply
```bash
python scripts/issue_xrpl_tokens.py --supply 5000000 --save-config
```

### Test with existing wallets
```bash
python scripts/test_xrpl_tokens.py \
  --config xrpl_wallets.json \
  --skip-creation \
  --user1-seed sEdABC... \
  --user2-seed sEdXYZ...
```

### Load and check balances
```python
from solana_swarm.integrations.xrpl import XRPLClient, TokenIssuer

client = XRPLClient()
issuer = TokenIssuer(client)
issuer.load_wallet_config("xrpl_wallets.json")

balances = issuer.get_all_balances()
for token, info in balances.items():
    print(f"{token}:")
    print(f"  Hot wallet XRP: {info['hot_wallet']['xrp_balance']}")
```

## Next Steps

1. **Integrate with Frontend**: Add token functionality to your React/web app
2. **DEX Trading**: List tokens on XRPL DEX for trading
3. **Yield Distribution**: Implement yield distribution logic
4. **Production**: Move to mainnet for real usage

## Troubleshooting

### Issue: "xrpl-py not installed"
```bash
pip install xrpl-py>=2.5.0
```

### Issue: "Configuration file not found"
First issue the tokens:
```bash
python scripts/issue_xrpl_tokens.py --save-config
```

### Issue: "Insufficient XRP reserve"
Each trust line requires ~2 XRP reserve. Get more testnet XRP from:
https://xrpl.org/xrp-testnet-faucet.html

### Issue: "Transaction failed"
Check:
1. Network connectivity
2. XRP balance (enough for reserve + fees)
3. Trust lines are set up
4. Addresses are correct

## Resources

- **Full Documentation**: `docs/XRPL_TOKENS.md`
- **Integration Guide**: `solana_swarm/integrations/xrpl/README.md`
- **XRPL Docs**: https://xrpl.org/
- **Testnet Explorer**: https://testnet.xrpl.org/
- **xrpl-py Docs**: https://xrpl-py.readthedocs.io/

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review full documentation
3. Check XRPL documentation
4. Open an issue in the repository

---

**Happy building with XRPL! 🚀**
