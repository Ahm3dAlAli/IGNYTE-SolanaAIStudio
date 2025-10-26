import { useState } from 'react';
import './App.css';
import ChainAiHub from './components/ChainAiHub';
import Header from './components/Header';

function App() {
  const [isConnected, setIsConnected] = useState(false);

  const handleConnect = () => {
    // Logic to connect to the wallet
    setIsConnected(true);
  };

  return (
    <div className="App">
      <Header onConnect={handleConnect} isConnected={isConnected} />
      <main>
        <ChainAiHub />
      </main>
    </div>
  );
}

export default App;
