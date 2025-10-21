import { useState, useEffect } from 'react';
import { Activity, Brain, TrendingUp, Wallet, Network, Zap } from 'lucide-react';
import type { Agent, AgentMetrics, MarketData, Transaction } from '../types/agent';
import AgentCard from './AgentCard';
import MarketOverview from './MarketOverview';
import TransactionList from './TransactionList';
import SwarmActivity from './SwarmActivity';

const Dashboard = () => {
  const [agents] = useState<Agent[]>([
    {
      id: '1',
      name: 'Price Monitor',
      role: 'price_monitor',
      status: 'active',
      confidence: 0.87,
      lastAction: 'Analyzing SOL/USDC on Jupiter',
      capabilities: ['price_monitoring', 'dex_analysis'],
      timestamp: new Date().toISOString()
    },
    {
      id: '2',
      name: 'Risk Manager',
      role: 'risk_manager',
      status: 'active',
      confidence: 0.92,
      lastAction: 'Assessing position sizes',
      capabilities: ['risk_assessment', 'portfolio_management'],
      timestamp: new Date().toISOString()
    },
    {
      id: '3',
      name: 'Strategy Optimizer',
      role: 'strategy_optimizer',
      status: 'analyzing',
      confidence: 0.78,
      lastAction: 'Optimizing route via Raydium',
      capabilities: ['strategy_optimization', 'execution'],
      timestamp: new Date().toISOString()
    }
  ]);

  const [metrics, setMetrics] = useState<AgentMetrics>({
    messagesExchanged: 0,
    decisionsMade: 0,
    analysisCompleted: 0,
    transactionsSimulated: 0,
    averageConfidence: 0.85,
    uptime: 0
  });

  const [marketData, setMarketData] = useState<MarketData>({
    token: 'SOL',
    price: 142.35,
    change24h: 5.32,
    volume24h: 2840000000,
    liquidity: 425000000,
    timestamp: new Date().toISOString(),
    source: 'Jupiter'
  });

  const [transactions] = useState<Transaction[]>([
    {
      id: '1',
      type: 'analyze',
      status: 'success',
      timestamp: new Date().toISOString(),
      confidence: 0.87
    }
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        messagesExchanged: prev.messagesExchanged + Math.floor(Math.random() * 3),
        analysisCompleted: prev.analysisCompleted + (Math.random() > 0.7 ? 1 : 0),
        uptime: prev.uptime + 1
      }));

      setMarketData(prev => ({
        ...prev,
        price: prev.price + (Math.random() - 0.5) * 2,
        change24h: prev.change24h + (Math.random() - 0.5) * 0.5,
        timestamp: new Date().toISOString()
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{
      padding: '24px',
      maxWidth: '1400px',
      margin: '0 auto'
    }}>
      <div style={{
        marginBottom: '32px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          marginBottom: '8px'
        }}>
          <Brain size={32} color="var(--color-solana)" />
          <h1 style={{ margin: 0 }}>Solana AI Hub</h1>
        </div>
        <p style={{
          color: 'var(--color-text-secondary)',
          fontSize: '1.125rem'
        }}>
          Multi-Agent Trading Intelligence for Solana DeFi
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '32px'
      }}>
        <MetricCard
          icon={<Activity size={20} />}
          label="Active Agents"
          value={agents.filter(a => a.status === 'active').length.toString()}
          color="var(--color-solana)"
        />
        <MetricCard
          icon={<Zap size={20} />}
          label="Decisions Made"
          value={metrics.decisionsMade.toString()}
          color="var(--color-info)"
        />
        <MetricCard
          icon={<TrendingUp size={20} />}
          label="Analysis Completed"
          value={metrics.analysisCompleted.toString()}
          color="var(--color-success)"
        />
        <MetricCard
          icon={<Network size={20} />}
          label="Messages Exchanged"
          value={metrics.messagesExchanged.toString()}
          color="var(--color-purple)"
        />
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '24px',
        marginBottom: '32px'
      }}>
        <MarketOverview data={marketData} />

        <div style={{
          background: 'var(--color-bg-secondary)',
          borderRadius: 'var(--border-radius)',
          padding: '24px',
          border: '1px solid var(--color-bg-tertiary)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            marginBottom: '16px'
          }}>
            <Wallet size={20} color="var(--color-solana)" />
            <h3 style={{ margin: 0, fontSize: '1.125rem' }}>Wallet Status</h3>
          </div>
          <div style={{ marginTop: '16px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: '12px'
            }}>
              <span style={{ color: 'var(--color-text-secondary)' }}>Balance</span>
              <span style={{ fontWeight: 600 }}>2.45 SOL</span>
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: '12px'
            }}>
              <span style={{ color: 'var(--color-text-secondary)' }}>Network</span>
              <span style={{ fontWeight: 600 }}>Devnet</span>
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between'
            }}>
              <span style={{ color: 'var(--color-text-secondary)' }}>Status</span>
              <span style={{
                color: 'var(--color-success)',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: 'var(--color-success)',
                  animation: 'pulse 2s ease-in-out infinite'
                }} />
                Connected
              </span>
            </div>
          </div>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
        gap: '24px',
        marginBottom: '32px'
      }}>
        {agents.map(agent => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '24px',
        marginBottom: '32px'
      }}>
        <SwarmActivity metrics={metrics} />
        <TransactionList transactions={transactions} />
      </div>
    </div>
  );
};

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}

const MetricCard = ({ icon, label, value, color }: MetricCardProps) => {
  return (
    <div style={{
      background: 'var(--color-bg-secondary)',
      borderRadius: 'var(--border-radius)',
      padding: '20px',
      border: '1px solid var(--color-bg-tertiary)',
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      cursor: 'default'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-2px)';
      e.currentTarget.style.boxShadow = 'var(--shadow-lg)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = 'none';
    }}
    >
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        marginBottom: '8px'
      }}>
        <div style={{ color }}>{icon}</div>
        <span style={{
          color: 'var(--color-text-secondary)',
          fontSize: '0.875rem'
        }}>
          {label}
        </span>
      </div>
      <div style={{
        fontSize: '2rem',
        fontWeight: 700,
        color
      }}>
        {value}
      </div>
    </div>
  );
};

export default Dashboard;
