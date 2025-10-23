import './App.css'
import { useState, useEffect } from 'react';
import { Github, CheckCircle } from 'lucide-react';
import { api, createAgentWebSocket, createMarketWebSocket } from './services/api';
import type { Agent, AgentMetrics, MarketData, Transaction } from './types/agent';
import Dashboard from './components/Dashboard'; // Import Dashboard
import { WalletContextProvider } from './components/WalletContextProvider';
import { useWallet } from '@solana/wallet-adapter-react';
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui';

function AppContent() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { connected, connect, disconnecting } = useWallet();

  // Data states, moved from Dashboard to App for centralized fetching
  const [agents, setAgents] = useState<Agent[]>([]);
  const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [walletBalance, setWalletBalance] = useState<number | null>(null);

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  // Handle login by connecting wallet
  const handleLogin = async () => {
    if (!connected) {
      try {
        await connect();
      } catch (error) {
        console.error("Failed to connect wallet:", error);
      }
    }
  };

  // Fetch initial data only if logged in
  useEffect(() => {
    if (!connected) return;

    const fetchData = async () => {
      try {
        const [agentsRes, metricsRes, marketRes, transactionsRes, walletRes] = await Promise.all([
          api.getAgents(),
          api.getMetrics(),
          api.getMarketPrice('SOL'), // Assuming SOL is the primary token
          api.getTransactions(),
          api.getWalletBalance()
        ]);

        if (agentsRes.data) setAgents(agentsRes.data as Agent[]);
        if (metricsRes.data) setMetrics(metricsRes.data as AgentMetrics);
        if (marketRes.data) setMarketData(marketRes.data as MarketData);
        if (transactionsRes.data) setTransactions(transactionsRes.data as Transaction[]);
        if (walletRes.data && typeof walletRes.data === 'object' && 'balance' in walletRes.data) {
          setWalletBalance((walletRes.data as { balance: number }).balance);
        }
      } catch (error) {
        console.error("Failed to fetch initial data:", error);
      }
    };

    fetchData();
  }, [connected]); // Dependency on connected state

  // Set up WebSockets for real-time updates only if logged in
  useEffect(() => {
    if (!connected) return;

    const agentWs = createAgentWebSocket((data) => {
      console.log("Agent WebSocket message:", data);
      // Assuming the WebSocket sends updates for individual agents or a list of agents
      if (Array.isArray(data)) {
        setAgents(data);
      } else if (data.id) {
        setAgents(prev => prev.map(agent => agent.id === data.id ? data : agent));
      }
    });

    const marketWs = createMarketWebSocket((data) => {
      console.log("Market WebSocket message:", data);
      if (data.token) {
        setMarketData(data);
      }
    });

    return () => {
      agentWs.disconnect();
      marketWs.disconnect();
    };
  }, [connected]); // Dependency on connected state

  return (
    <div className="app-container">
      <header className="navbar">
        <div className="navbar-brand">
          <span className="logo-text">Solana Swarm</span>
        </div>
        <nav className="navbar-nav">
          <a href="#" className="nav-item">Home</a>
          <a href="#" className="nav-item">Docs</a>
          <a href="https://github.com/solana-swarm/solana-swarm" target="_blank" rel="noopener noreferrer" className="nav-item github-icon">
            <Github size={20} />
          </a>
        </nav>
        <button className="menu-toggle" onClick={toggleMenu}>
          ☰
        </button>
        {menuOpen && (
          <div className="mobile-menu">
            <a href="#" className="mobile-nav-item">Home</a>
            <a href="#" className="mobile-nav-item">Docs</a>
            <a href="https://github.com/solana-swarm/solana-swarm" target="_blank" rel="noopener noreferrer" className="mobile-nav-item github-icon">
              <Github size={20} /> GitHub
            </a>
          </div>
        )}
      </header>

      {connected ? (
        <Dashboard
          agents={agents}
          metrics={metrics}
          marketData={marketData}
          transactions={transactions}
          walletBalance={walletBalance}
        />
      ) : (
        <>
          <main className="hero-section">
            <div className="hero-content">
              <h1 className="hero-title">
                YOUR ON-CHAIN <br />
                <span className="highlight">AI & DEFI HUB</span> | ON SOLANA
              </h1>
              <p className="hero-subtitle">UNLIMITLESS AI X DEFI ECOSYSTEM</p>
              <div className="hero-actions">
                <WalletMultiButton className="btn-primary" />
                <button className="btn-secondary">
                  DOCS
                </button>
              </div>
            </div>
            <div className="hero-diagram-placeholder">
              <img src="/multi-agentic-ai-copilot.png" alt="Multi Agentic AI Copilot Diagram" style={{ maxWidth: '100%', height: 'auto' }} />
            </div>
          </main>

          <section className="content-section">
            <div className="content-block reverse">
              <div className="content-text">
                <p className="section-label">SOLANA AI</p>
                <h2>Multi Agentic AI Copilot</h2>
                <p>Solana AI Hub offers a unique Model Context Protocol and Intent-based structure to give users the best experience possible with an AI Copilot on the Solana Ecosystem. Adapted with all of the features on core Solana Infrastructures and much more.</p>
                <ul className="feature-list">
                  <li><CheckCircle size={16} className="feature-icon" /> Whole token analysis with a single prompt</li>
                  <li><CheckCircle size={16} className="feature-icon" /> Adapted to all Solana Infrastructures</li>
                  <li><CheckCircle size={16} className="feature-icon" /> Unlimited AI-Capabilities</li>
                </ul>
                <div className="section-actions">
                  <WalletMultiButton className="btn-primary">Open App</WalletMultiButton>
                  <button className="btn-secondary">Check Docs</button>
                </div>
              </div>
              <div className="content-diagram">
                <img src="/multi-agentic-ai-copilot.png" alt="Multi Agentic AI Copilot Diagram" style={{ maxWidth: '100%', height: 'auto' }} />
              </div>
            </div>
          </section>

          <section className="content-section">
            <div className="content-block">
              <div className="content-text">
                <p className="section-label">SOLANA SWARM</p>
                <h2>TOKENIZATION OF AI AGENTS</h2>
                <p>Creating value for AI Agents by embedding their knowledge to the chain. Their knowledges are being fetched from the Solana chain itself as SPL standard tokens.</p>
                <ul className="feature-list">
                  <li><CheckCircle size={16} className="feature-icon" /> Works with Solana Swarm's Core LLM Intent Engine</li>
                  <li><CheckCircle size={16} className="feature-icon" /> Ownership security based privacy for each Agent</li>
                  <li><CheckCircle size={16} className="feature-icon" /> On-Chain knowledge</li>
                </ul>
                <div className="section-actions">
                  <WalletMultiButton className="btn-primary">Open App</WalletMultiButton>
                  <button className="btn-secondary">Check Docs</button>
                </div>
              </div>
              <div className="content-diagram">
                <img src="/tokenization-of-ai-agents.png" alt="Tokenization of AI Agents Diagram" style={{ maxWidth: '100%', height: 'auto' }} />
              </div>
            </div>
          </section>
        </>
      )}

      <footer className="footer">
        <div className="footer-content">
          <span>© {new Date().getFullYear()} Solana AI Hub. All rights reserved.</span>
          <div className="footer-social">
            <a href="https://github.com/solana-swarm/solana-swarm" aria-label="GitHub" target="_blank" rel="noopener noreferrer"><Github size={20} /></a>
          </div>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <WalletContextProvider>
      <AppContent />
    </WalletContextProvider>
  );
}

export default App;
