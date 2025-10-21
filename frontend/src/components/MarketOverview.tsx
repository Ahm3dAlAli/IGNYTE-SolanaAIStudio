import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import type { MarketData } from '../types/agent';

interface MarketOverviewProps {
  data: MarketData;
}

const MarketOverview = ({ data }: MarketOverviewProps) => {
  const isPositive = data.change24h >= 0;

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
        <DollarSign size={20} color="var(--color-solana)" />
        <h3 style={{ margin: 0, fontSize: '1.125rem' }}>Market Overview</h3>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'baseline',
        gap: '12px',
        marginBottom: '16px'
      }}>
        <span style={{
          fontSize: '2.5rem',
          fontWeight: 700,
          color: 'var(--color-text-primary)'
        }}>
          ${data.price.toFixed(2)}
        </span>
        <span style={{
          fontSize: '1rem',
          color: 'var(--color-text-secondary)'
        }}>
          {data.token}
        </span>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '20px'
      }}>
        {isPositive ? (
          <TrendingUp size={20} color="var(--color-success)" />
        ) : (
          <TrendingDown size={20} color="var(--color-error)" />
        )}
        <span style={{
          fontSize: '1.25rem',
          fontWeight: 600,
          color: isPositive ? 'var(--color-success)' : 'var(--color-error)'
        }}>
          {isPositive ? '+' : ''}{data.change24h.toFixed(2)}%
        </span>
        <span style={{
          color: 'var(--color-text-secondary)',
          fontSize: '0.875rem'
        }}>
          24h
        </span>
      </div>

      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        paddingTop: '16px',
        borderTop: '1px solid var(--color-bg-tertiary)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between'
        }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>Volume (24h)</span>
          <span style={{ fontWeight: 600 }}>
            ${(data.volume24h / 1000000000).toFixed(2)}B
          </span>
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between'
        }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>Liquidity</span>
          <span style={{ fontWeight: 600 }}>
            ${(data.liquidity / 1000000).toFixed(2)}M
          </span>
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between'
        }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>Source</span>
          <span style={{
            padding: '4px 10px',
            borderRadius: '12px',
            background: 'var(--color-bg-hover)',
            fontSize: '0.75rem',
            fontWeight: 600
          }}>
            {data.source}
          </span>
        </div>
      </div>
    </div>
  );
};

export default MarketOverview;
