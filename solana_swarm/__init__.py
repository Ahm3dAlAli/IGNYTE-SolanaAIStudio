"""
Solana Swarm Intelligence Framework
A multi-agent framework for building AI-powered trading strategies on Solana.
"""

__version__ = "0.1.0"

from solana_swarm.core.agent import AgentConfig
from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
from solana_swarm.core.consensus import ConsensusManager, Vote

__all__ = [
    "AgentConfig",
    "SwarmAgent",
    "SwarmConfig",
    "ConsensusManager",
    "Vote",
]