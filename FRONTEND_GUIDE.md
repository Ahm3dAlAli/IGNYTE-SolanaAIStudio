# Frontend Setup Guide

This guide will help you set up and run the web frontend for your Solana AI Hub.

## Quick Start

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

## What's Been Built

### Dashboard Features

1. **Agent Monitoring**
   - Real-time status of all AI agents
   - Confidence levels for each agent
   - Last actions performed
   - Agent capabilities display

2. **Market Overview**
   - Live SOL price tracking
   - 24-hour price changes
   - Volume and liquidity metrics
   - DEX source information

3. **Wallet Status**
   - Current SOL balance
   - Network connection status
   - Network selection (devnet/mainnet)

4. **Transaction History**
   - Recent transactions list
   - Transaction status tracking
   - Confidence levels
   - Signature links to Solana Explorer

5. **Swarm Activity**
   - Messages exchanged counter
   - Decisions made tracker
   - Analysis completion metrics
   - Average confidence display
   - System uptime

## Architecture

### Components

```
Dashboard.tsx          - Main container component
├── AgentCard.tsx      - Individual agent display
├── MarketOverview.tsx - Market data display
├── TransactionList.tsx - Transaction history
└── SwarmActivity.tsx  - Swarm metrics
```

### Data Flow

```
Dashboard (State Management)
    ↓
Component Props
    ↓
Visual Rendering
```

The dashboard currently uses local state with mock data that updates in real-time to simulate agent activity.

## Connecting to Backend

To connect the frontend to your Python backend:

1. Create a REST API endpoint in your Python code:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/agents")
async def get_agents():
    return {
        "agents": [
            {
                "id": "1",
                "name": "Price Monitor",
                "role": "price_monitor",
                "status": "active",
                "confidence": 0.87
            }
        ]
    }
```

2. Create an API service in the frontend:

```typescript
// src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const agentService = {
  async getAgents() {
    const response = await fetch(`${API_BASE_URL}/api/agents`);
    return response.json();
  }
};
```

3. Use the service in your components:

```typescript
// In Dashboard.tsx
import { agentService } from '../services/api';

useEffect(() => {
  const fetchAgents = async () => {
    const data = await agentService.getAgents();
    setAgents(data.agents);
  };
  fetchAgents();
}, []);
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_SOLANA_NETWORK=devnet
VITE_API_BASE_URL=http://localhost:8000
```

## Customization

### Colors

The color scheme is defined in `src/index.css`:

```css
--color-solana: #14F195;
--color-success: #10b981;
--color-warning: #f59e0b;
--color-error: #ef4444;
```

### Adding New Agent Types

Update `src/types/agent.ts`:

```typescript
export interface Agent {
  role: 'market_analyzer' | 'risk_manager' | 'your_new_role';
  // ... other fields
}
```

### Adding New Components

1. Create component in `src/components/`
2. Import in `Dashboard.tsx`
3. Add to the dashboard layout

## Building for Production

```bash
# Build the application
npm run build

# Preview the production build
npm run preview

# Deploy the dist/ folder to your hosting service
```

## Deployment Options

### Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

### Netlify
```bash
npm run build
# Drag and drop the dist/ folder to Netlify
```

### Traditional Hosting
```bash
npm run build
# Upload dist/ folder to your web server
```

## Next Steps

1. **Connect to Backend API**
   - Set up FastAPI or Flask endpoints
   - Update API service to fetch real data
   - Add WebSocket for real-time updates

2. **Add Wallet Integration**
   - Integrate @solana/wallet-adapter-react
   - Add wallet connection button
   - Display user's wallet balances

3. **Enhance Charts**
   - Add price charts with Recharts
   - Display agent performance over time
   - Add portfolio allocation charts

4. **Add Authentication**
   - Integrate Supabase Auth
   - Add user login/signup
   - Protect routes

5. **Real-time Updates**
   - Add WebSocket connection
   - Subscribe to agent events
   - Live transaction updates

## Troubleshooting

### Port Already in Use
```bash
# Change the port in vite.config.ts
export default defineConfig({
  server: {
    port: 3000
  }
})
```

### Build Errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Type Errors
```bash
# Regenerate types
npm run build
```

## Support

For questions or issues:
- Check the main project README
- Review the component documentation
- Open an issue on GitHub

---

Built with React, TypeScript, and Vite for the Solana AI Hub.
