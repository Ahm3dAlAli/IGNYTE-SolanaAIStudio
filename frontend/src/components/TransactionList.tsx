import type { Transaction } from '../types/agent';
import { ArrowRightLeft, CheckCircle, XCircle, Clock } from 'lucide-react';

interface TransactionListProps {
  transactions: Transaction[];
}

const TransactionList = ({ transactions }: TransactionListProps) => {
  const getStatusIcon = (status: Transaction['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle size={16} color="var(--color-success)" />;
      case 'failed':
        return <XCircle size={16} color="var(--color-error)" />;
      case 'pending':
        return <Clock size={16} color="var(--color-warning)" />;
    }
  };

  const getStatusColor = (status: Transaction['status']) => {
    switch (status) {
      case 'success':
        return 'var(--color-success)';
      case 'failed':
        return 'var(--color-error)';
      case 'pending':
        return 'var(--color-warning)';
    }
  };

  const getTypeLabel = (type: Transaction['type']) => {
    const labels = {
      swap: 'Token Swap',
      stake: 'Staking',
      provide_liquidity: 'Provide Liquidity',
      analyze: 'Market Analysis'
    };
    return labels[type] || type;
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
        <ArrowRightLeft size={20} color="var(--color-solana)" />
        <h3 style={{ margin: 0, fontSize: '1.125rem' }}>Recent Transactions</h3>
      </div>

      {transactions.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          color: 'var(--color-text-secondary)'
        }}>
          <ArrowRightLeft size={48} style={{ opacity: 0.3, marginBottom: '16px' }} />
          <div>No transactions yet</div>
          <div style={{ fontSize: '0.875rem', marginTop: '8px' }}>
            Agents will execute transactions when high confidence is reached
          </div>
        </div>
      ) : (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          {transactions.slice(0, 5).map(tx => (
            <div
              key={tx.id}
              style={{
                padding: '16px',
                background: 'var(--color-bg-tertiary)',
                borderRadius: 'var(--border-radius-sm)',
                transition: 'background 0.2s ease',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'var(--color-bg-hover)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'var(--color-bg-tertiary)';
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '8px'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  {getStatusIcon(tx.status)}
                  <span style={{ fontWeight: 600 }}>
                    {getTypeLabel(tx.type)}
                  </span>
                </div>
                <span style={{
                  padding: '4px 8px',
                  borderRadius: '12px',
                  background: `${getStatusColor(tx.status)}20`,
                  color: getStatusColor(tx.status),
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  textTransform: 'uppercase'
                }}>
                  {tx.status}
                </span>
              </div>

              {tx.fromToken && tx.toToken && (
                <div style={{
                  fontSize: '0.875rem',
                  color: 'var(--color-text-secondary)',
                  marginBottom: '8px'
                }}>
                  {tx.amount} {tx.fromToken} → {tx.toToken}
                  {tx.dex && ` via ${tx.dex}`}
                </div>
              )}

              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                fontSize: '0.75rem',
                color: 'var(--color-text-tertiary)'
              }}>
                <span>
                  Confidence: {Math.round(tx.confidence * 100)}%
                </span>
                <span>
                  {new Date(tx.timestamp).toLocaleTimeString()}
                </span>
              </div>

              {tx.signature && (
                <div style={{
                  marginTop: '8px',
                  fontSize: '0.75rem',
                  color: 'var(--color-text-tertiary)',
                  fontFamily: 'monospace',
                  wordBreak: 'break-all'
                }}>
                  Sig: {tx.signature.slice(0, 20)}...
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TransactionList;
