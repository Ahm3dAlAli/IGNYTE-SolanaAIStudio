import './Header.css';
import WalletConnect from './WalletConnect';

interface HeaderProps {
  onConnect: () => void;
  isConnected: boolean;
}

const Header = ({ onConnect, isConnected }: HeaderProps) => {
  return (
    <header className="app-header">
      <div className="logo">
        <a href="/">Chain AI Hub</a>
      </div>
      <div className="header-actions">
        <button className="launch-app-btn">Launch App</button>
        <WalletConnect onConnect={onConnect} isConnected={isConnected} />
      </div>
    </header>
  );
};

export default Header;
