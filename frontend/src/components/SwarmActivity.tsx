import { Activity } from 'lucide-react';
import type { AgentMetrics } from '../types/agent';

interface SwarmActivityProps {
  metrics: AgentMetrics;
}

const SwarmActivity = ({ metrics }: SwarmActivityProps) => {
  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  return (
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
        marginBottom: '20px'
      }}>
        <Activity size={20} color="var(--color-solana)" />
        <h3 style={{ margin: 0, fontSize: '1.125rem' }}>Swarm Activity</h3>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '16px'
      }}>
        <MetricItem
          label="Messages Exchanged"
          value={metrics.messagesExchanged}
          color="var(--color-purple)"
        />
        <MetricItem
          label="Decisions Made"
          value={metrics.decisionsMade}
          color="var(--color-info)"
        />
        <MetricItem
          label="Analysis Completed"
          value={metrics.analysisCompleted}
          color="var(--color-success)"
        />
        <MetricItem
          label="Transactions"
          value={metrics.transactionsSimulated}
          color="var(--color-warning)"
        />
      </div>

      <div style={{
        marginTop: '20px',
        paddingTop: '20px',
        borderTop: '1px solid var(--color-bg-tertiary)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px'
        }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>
            Average Confidence
          </span>
          <span style={{
            fontSize: '1.25rem',
            fontWeight: 700,
            color: metrics.averageConfidence >= 0.8 ? 'var(--color-success)' :
                   metrics.averageConfidence >= 0.6 ? 'var(--color-warning)' : 'var(--color-error)'
          }}>
            {Math.round(metrics.averageConfidence * 100)}%
          </span>
        </div>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>
            Uptime
          </span>
          <span style={{
            fontSize: '1rem',
            fontWeight: 600,
            color: 'var(--color-solana)'
          }}>
            {formatUptime(metrics.uptime)}
          </span>
        </div>
      </div>

      <div style={{
        marginTop: '20px',
        padding: '16px',
        background: 'linear-gradient(135deg, rgba(20, 241, 149, 0.1), rgba(59, 130, 246, 0.1))',
        borderRadius: 'var(--border-radius-sm)',
        border: '1px solid rgba(20, 241, 149, 0.2)'
      }}>
        <div style={{
          fontSize: '0.875rem',
          color: 'var(--color-text-secondary)',
          marginBottom: '8px'
        }}>
          Swarm Status
        </div>
        <div style={{
          fontSize: '1rem',
          fontWeight: 600,
          color: 'var(--color-solana)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: 'var(--color-solana)',
            animation: 'pulse 2s ease-in-out infinite'
          }} />
          Active & Coordinating
        </div>
      </div>
    </div>
  );
};

interface MetricItemProps {
  label: string;
  value: number;
  color: string;
}

const MetricItem = ({ label, value, color }: MetricItemProps) => {
  return (
    <div style={{
      padding: '16px',
      background: 'var(--color-bg-tertiary)',
      borderRadius: 'var(--border-radius-sm)',
      textAlign: 'center'
    }}>
      <div style={{
        fontSize: '1.75rem',
        fontWeight: 700,
        color,
        marginBottom: '4px'
      }}>
        {value}
      </div>
      <div style={{
        fontSize: '0.75rem',
        color: 'var(--color-text-secondary)'
      }}>
        {label}
      </div>
    </div>
  );
};

export default SwarmActivity;
