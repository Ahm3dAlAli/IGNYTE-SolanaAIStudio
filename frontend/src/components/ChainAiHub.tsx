import React from 'react';
import './ChainAiHub.css';
import AgentCard from './AgentCard';

const ChainAiHub: React.FC = () => {
  // Placeholder data for AI agents
  const agents = [
    { name: 'Price Monitor', description: 'Monitors token prices and alerts on volatility.' },
    { name: 'Arbitrage Agent', description: 'Executes trades to profit from price differences.' },
    { name: 'DeFi Yield Farmer', description: 'Finds the best yields in DeFi protocols.' },
  ];

  return (
    <div className="chain-ai-hub">
      <h1>Chain AI Hub</h1>
      <p>Deploy AI agents with different functionalities on the Solana network.</p>
      <div className="agent-list">
        {agents.map((agent, index) => (
          <AgentCard key={index} name={agent.name} description={agent.description} />
        ))}
      </div>
    </div>
  );
};

export default ChainAiHub;
