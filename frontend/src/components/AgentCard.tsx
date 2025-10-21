import type { Agent } from '../types/agent';
import { Bot, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface AgentCardProps {
  agent: Agent;
}

const AgentCard = ({ agent }: AgentCardProps) => {
  const getStatusColor = (status: Agent['status']) => {
    switch (status) {
      case 'active':
        return 'var(--color-success)';
      case 'analyzing':
        return 'var(--color-info)';
      case 'inactive':
        return 'var(--color-text-tertiary)';
      case 'error':
        return 'var(--color-error)';
      default:
        return 'var(--color-text-tertiary)';
    }
  };

  const getStatusIcon = (status: Agent['status']) => {
    switch (status) {
      case 'active':
        return <CheckCircle size={16} />;
      case 'analyzing':
        return <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />;
      case 'error':
        return <AlertCircle size={16} />;
      default:
        return null;
    }
  };

  const getRoleLabel = (role: Agent['role']) => {
    const labels = {
      market_analyzer: 'Market Analyzer',
      risk_manager: 'Risk Manager',
      strategy_optimizer: 'Strategy Optimizer',
      decision_maker: 'Decision Maker',
      price_monitor: 'Price Monitor',
      portfolio_manager: 'Portfolio Manager'
    };
    return labels[role] || role;
  };

  return (
    <div style={{
      background: 'var(--color-bg-secondary)',
      borderRadius: 'var(--border-radius)',
      padding: '20px',
      border: '1px solid var(--color-bg-tertiary)',
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      cursor: 'pointer'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-4px)';
      e.currentTarget.style.boxShadow = '0 8px 16px rgba(20, 241, 149, 0.1)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = 'none';
    }}
    >
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        marginBottom: '16px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: 'var(--border-radius-sm)',
            background: 'linear-gradient(135deg, var(--color-solana), var(--color-info))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Bot size={24} color="white" />
          </div>
          <div>
            <h3 style={{
              margin: 0,
              fontSize: '1.125rem',
              fontWeight: 600
            }}>
              {agent.name}
            </h3>
            <span style={{
              color: 'var(--color-text-secondary)',
              fontSize: '0.875rem'
            }}>
              {getRoleLabel(agent.role)}
            </span>
          </div>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 12px',
          borderRadius: '20px',
          background: `${getStatusColor(agent.status)}20`,
          color: getStatusColor(agent.status),
          fontSize: '0.75rem',
          fontWeight: 600,
          textTransform: 'uppercase'
        }}>
          {getStatusIcon(agent.status)}
          {agent.status}
        </div>
      </div>

      <div style={{
        background: 'var(--color-bg-tertiary)',
        borderRadius: 'var(--border-radius-sm)',
        padding: '12px',
        marginBottom: '16px'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '8px'
        }}>
          <span style={{
            color: 'var(--color-text-secondary)',
            fontSize: '0.875rem'
          }}>
            Confidence
          </span>
          <span style={{
            fontWeight: 600,
            fontSize: '1.125rem',
            color: agent.confidence >= 0.8 ? 'var(--color-success)' :
                   agent.confidence >= 0.6 ? 'var(--color-warning)' : 'var(--color-error)'
          }}>
            {Math.round(agent.confidence * 100)}%
          </span>
        </div>
        <div style={{
          width: '100%',
          height: '6px',
          background: 'var(--color-bg-hover)',
          borderRadius: '3px',
          overflow: 'hidden'
        }}>
          <div style={{
            width: `${agent.confidence * 100}%`,
            height: '100%',
            background: agent.confidence >= 0.8 ? 'var(--color-success)' :
                       agent.confidence >= 0.6 ? 'var(--color-warning)' : 'var(--color-error)',
            transition: 'width 0.3s ease'
          }} />
        </div>
      </div>

      {agent.lastAction && (
        <div style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '8px',
          padding: '12px',
          background: 'var(--color-bg-primary)',
          borderRadius: 'var(--border-radius-sm)',
          marginBottom: '12px'
        }}>
          <div style={{
            width: '4px',
            height: '4px',
            borderRadius: '50%',
            background: 'var(--color-solana)',
            marginTop: '8px',
            flexShrink: 0
          }} />
          <div>
            <div style={{
              color: 'var(--color-text-secondary)',
              fontSize: '0.75rem',
              marginBottom: '4px'
            }}>
              Last Action
            </div>
            <div style={{
              color: 'var(--color-text-primary)',
              fontSize: '0.875rem',
              lineHeight: 1.4
            }}>
              {agent.lastAction}
            </div>
          </div>
        </div>
      )}

      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '6px'
      }}>
        {agent.capabilities.map((cap, idx) => (
          <span
            key={idx}
            style={{
              padding: '4px 10px',
              borderRadius: '12px',
              background: 'var(--color-bg-hover)',
              color: 'var(--color-text-secondary)',
              fontSize: '0.75rem',
              fontWeight: 500
            }}
          >
            {cap.replace(/_/g, ' ')}
          </span>
        ))}
      </div>
    </div>
  );
};

export default AgentCard;
