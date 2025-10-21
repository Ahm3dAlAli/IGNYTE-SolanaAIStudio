export interface Agent {
  id: string;
  name: string;
  role: 'market_analyzer' | 'risk_manager' | 'strategy_optimizer' | 'decision_maker' | 'price_monitor' | 'portfolio_manager';
  status: 'active' | 'inactive' | 'analyzing' | 'error';
  confidence: number;
  lastAction?: string;
  timestamp?: string;
  capabilities: string[];
}

export interface AgentDecision {
  agentId: string;
  agentName: string;
  decision: 'approve' | 'reject' | 'abstain';
  confidence: number;
  reasoning: string;
  timestamp: string;
}

export interface SwarmConsensus {
  proposalId: string;
  consensus: boolean;
  approvalRate: number;
  totalVotes: number;
  votes: AgentDecision[];
  timestamp: string;
}

export interface MarketData {
  token: string;
  price: number;
  change24h: number;
  volume24h: number;
  liquidity: number;
  timestamp: string;
  source: string;
}

export interface Transaction {
  id: string;
  type: 'swap' | 'stake' | 'provide_liquidity' | 'analyze';
  status: 'pending' | 'success' | 'failed';
  fromToken?: string;
  toToken?: string;
  amount?: number;
  dex?: string;
  signature?: string;
  timestamp: string;
  confidence: number;
}

export interface AgentMetrics {
  messagesExchanged: number;
  decisionsMade: number;
  analysisCompleted: number;
  transactionsSimulated: number;
  averageConfidence: number;
  uptime: number;
}
