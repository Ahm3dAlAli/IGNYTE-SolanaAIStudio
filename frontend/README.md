# Solana AI Hub Frontend

A modern web interface for the Solana Swarm Intelligence Framework - multi-agent trading intelligence for Solana DeFi.

## Features

- **Real-time Agent Monitoring**: Track the status and performance of all AI agents
- **Market Overview**: Live price data and market statistics from Solana DEXs
- **Transaction History**: View recent transactions and their confidence levels
- **Swarm Activity Dashboard**: Monitor agent communication and consensus decisions
- **Wallet Integration**: Connect and monitor your Solana wallet
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Lucide React** for beautiful icons
- **Solana Web3.js** for blockchain integration
- **Supabase** for data persistence
- **Recharts** for data visualization

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Solana wallet (for devnet testing)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Dashboard.tsx       # Main dashboard component
│   │   ├── AgentCard.tsx       # Individual agent display
│   │   ├── MarketOverview.tsx  # Market data component
│   │   ├── TransactionList.tsx # Transaction history
│   │   └── SwarmActivity.tsx   # Swarm metrics
│   ├── types/
│   │   └── agent.ts            # TypeScript type definitions
│   ├── App.tsx                 # Root component
│   ├── index.css               # Global styles
│   └── main.tsx                # Application entry
├── public/                     # Static assets
└── package.json
```

## Features in Detail

### Agent Monitoring

Monitor multiple AI agents in real-time:
- Price Monitor: Tracks token prices across DEXs
- Risk Manager: Assesses position sizes and risks
- Strategy Optimizer: Optimizes trading strategies
- Decision Maker: Coordinates agent consensus

### Market Data

Live market data including:
- Current token prices
- 24-hour price changes
- Trading volume
- Liquidity across DEXs

### Transaction Tracking

View all transactions with:
- Transaction type (swap, stake, liquidity)
- Status (pending, success, failed)
- Confidence levels
- Timestamps and signatures

### Swarm Metrics

Monitor agent collaboration:
- Messages exchanged
- Decisions made
- Analysis completed
- Average confidence levels
- System uptime

## Configuration

Create a `.env` file in the frontend directory:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_SOLANA_NETWORK=devnet
```

## Development

### Running the Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The build output will be in the `dist/` directory.

## Design System

The application uses a custom design system with:
- Dark theme optimized for trading
- Solana brand colors (#14F195)
- Consistent spacing (8px grid)
- Smooth transitions and animations
- Accessible color contrasts

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Contributing

Contributions are welcome! Please follow the main project's contribution guidelines.

## License

MIT License - see the main project LICENSE file for details.

## Support

For issues and questions:
- GitHub Issues: [solana-swarm issues](https://github.com/solana-swarm/solana-swarm/issues)
- Documentation: See main project README
