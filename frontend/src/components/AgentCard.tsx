import React from 'react';
import './AgentCard.css';

interface AgentCardProps {
  name: string;
  description: string;
}

const AgentCard: React.FC<AgentCardProps> = ({ name, description }) => {
  return (
    <div className="agent-card">
      <h3>{name}</h3>
      <p>{description}</p>
      <button className="deploy-btn">Deploy</button>
    </div>
  );
};

export default AgentCard;
