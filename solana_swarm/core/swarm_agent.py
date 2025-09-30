"""
Fixed Swarm Agent Module
Implements swarm intelligence for Solana agents with LLM-powered decision making
"""

import logging
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from solana_swarm.core.agent import AgentConfig
from solana_swarm.core.llm_provider import LLMProvider, create_llm_provider, LLMConfig
from solana_swarm.plugins.base import AgentPlugin, PluginConfig

logger = logging.getLogger(__name__)

@dataclass
class SwarmConfig:
    """Swarm agent configuration."""
    role: str
    min_confidence: float = 0.7
    min_votes: int = 2
    timeout: float = 1.0
    max_retries: int = 3
    llm: Optional[LLMConfig] = None

    def __post_init__(self):
        """Validate configuration."""
        if not self.role:
            raise ValueError("role is required")
        if self.min_confidence < 0 or self.min_confidence > 1:
            raise ValueError("min_confidence must be between 0 and 1")
        if self.min_votes < 1:
            raise ValueError("min_votes must be at least 1")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

class SwarmAgent(AgentPlugin):
    """Swarm agent with plugin support and LLM-powered decision making."""

    def __init__(self, config: SwarmConfig):
        """Initialize swarm agent."""
        # Create compatible AgentConfig and PluginConfig
        agent_config = AgentConfig(name=f"swarm_{config.role}")
        plugin_config = PluginConfig(
            name=f"swarm_{config.role}",
            role=config.role,
            capabilities=["swarm_intelligence", "decision_making", "consensus"]
        )
        
        # Initialize parent class
        super().__init__(agent_config, plugin_config)
        
        self.config = config
        self.llm = None
        self.swarm_peers: List['SwarmAgent'] = []
        self._is_running = False
        logger.info(f"Initialized swarm agent with role: {config.role}")

    async def initialize(self) -> None:
        """Initialize agent resources."""
        if self._is_initialized:
            return

        try:
            # Initialize LLM if configured
            if self.config.llm:
                self.llm = create_llm_provider(self.config.llm)

            self._is_initialized = True
            self._is_running = True
            logger.info(f"Initialized SwarmAgent with role: {self.config.role}")

        except Exception as e:
            logger.error(f"Error initializing SwarmAgent: {str(e)}")
            raise

    async def join_swarm(self, peers: List['SwarmAgent']):
        """Join a swarm of agents."""
        self.swarm_peers = peers
        for peer in peers:
            if self not in peer.swarm_peers:
                peer.swarm_peers.append(self)
        logger.info(f"Joined swarm with {len(peers)} peers")

    async def propose_action(self, action_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Propose an action to the swarm."""
        if not self._is_running:
            raise RuntimeError("Cannot propose action - Agent is not running")

        proposal = {
            "type": action_type,
            "params": params,
            "proposer": self.config.role
        }

        # Collect votes from peers
        votes = []
        for peer in self.swarm_peers:
            vote = await peer.evaluate_proposal(proposal)
            votes.append(vote)

        # Calculate consensus
        total_votes = len(votes)
        positive_votes = sum(1 for v in votes if v["decision"] == "approve")
        approval_rate = positive_votes / total_votes if total_votes > 0 else 0

        # Check if consensus is reached
        consensus = (
            approval_rate >= self.config.min_confidence and
            positive_votes >= self.config.min_votes
        )

        result = {
            "consensus": consensus,
            "approval_rate": approval_rate,
            "total_votes": total_votes,
            "votes": votes,
            "reasons": [v["reasoning"] for v in votes]
        }

        logger.info(f"Proposal result: consensus={consensus}, approval_rate={approval_rate}")
        return result

    async def evaluate_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a proposal using role-specific expertise."""
        if not self._is_running:
            return {"decision": "reject", "confidence": 0.0, "reasoning": "Agent is not running"}

        try:
            # Get role-specific evaluation prompt
            role_prompt = self._get_role_prompt()
            
            # Add proposal context
            context = {
                "proposal": proposal,
                "role": self.config.role,
                "role_prompt": role_prompt
            }

            # Use plugin's evaluate method
            result = await self.evaluate(context)

            # Ensure proper response format
            if "error" in result:
                return {
                    "decision": "reject",
                    "confidence": 0.0,
                    "reasoning": f"Evaluation error: {result['error']}"
                }

            # Convert evaluation result to vote format
            confidence = result.get('confidence', 0.5)
            reasoning = result.get('reasoning', result.get('conclusion', 'No reasoning provided'))
            
            # Decision based on confidence
            if confidence >= self.config.min_confidence:
                decision = "approve"
            elif confidence >= 0.4:
                decision = "abstain"
            else:
                decision = "reject"

            return {
                "decision": decision,
                "confidence": confidence,
                "reasoning": reasoning
            }

        except Exception as e:
            logger.error(f"Error evaluating proposal: {str(e)}")
            return {
                "decision": "reject",
                "confidence": 0.0,
                "reasoning": f"Evaluation failed: {str(e)}"
            }

    def _get_role_prompt(self) -> str:
        """Get role-specific evaluation prompt."""
        if self.config.role == "risk_manager":
            return """As a Risk Manager on Solana, evaluate this proposal focusing on:
1. Position Size Analysis
2. Smart Contract Security Assessment
3. Slippage and MEV Risk
4. Solana Network Conditions

Your primary responsibility is protecting assets and maintaining risk parameters."""

        elif self.config.role == "market_analyzer":
            return """As a Market Analyzer on Solana, evaluate this proposal focusing on:
1. Token Price Analysis on Solana DEXs
2. Liquidity Conditions on Jupiter/Raydium
3. Volume and Trading Patterns
4. Cross-DEX Arbitrage Opportunities

Your primary responsibility is market analysis and trend identification."""

        elif self.config.role == "strategy_optimizer":
            return """As a Strategy Optimizer on Solana, evaluate this proposal focusing on:
1. Transaction Cost Optimization
2. Route Optimization across Solana DEXs
3. Performance Metrics
4. MEV Protection Strategies

Your primary responsibility is optimizing execution and performance."""

        return f"As a {self.config.role}, evaluate this proposal based on your expertise."

    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate using LLM and return decision."""
        if not self._is_initialized:
            await self.initialize()

        try:
            # If no LLM configured, provide basic response
            if not self.llm:
                return {
                    "observation": f"Evaluating as {self.config.role}",
                    "reasoning": f"Basic evaluation without LLM for {self.config.role}",
                    "conclusion": "Analysis complete with limited capability",
                    "confidence": 0.6
                }

            # Format context for LLM
            prompt = self._format_prompt(context)

            # Get LLM response
            response = await self.llm.query(prompt, expect_json=True)

            # Parse and validate response
            result = self._parse_response(response)

            return result

        except Exception as e:
            logger.error(f"Error in evaluation: {str(e)}")
            return {
                "observation": f"Error in {self.config.role} evaluation",
                "reasoning": f"Failed to complete evaluation: {str(e)}",
                "conclusion": "Unable to provide recommendation due to error",
                "confidence": 0.0,
                "error": str(e)
            }

    def _format_prompt(self, context: Dict[str, Any]) -> str:
        """Format context into LLM prompt."""
        proposal = context.get("proposal", {})
        role_prompt = context.get("role_prompt", "")

        return f"""
        {role_prompt}

        Proposal to Evaluate:
        Type: {proposal.get('type')}
        Parameters: {json.dumps(proposal.get('params', {}), indent=2)}
        Proposer: {proposal.get('proposer')}

        Provide your analysis in JSON format with:
        - observation: string (what you observe)
        - reasoning: string (your analysis)
        - conclusion: string (your recommendation)
        - confidence: float (0-1)
        """

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM response."""
        try:
            result = json.loads(response)
            required_fields = ["observation", "reasoning", "conclusion", "confidence"]

            # Fill in missing fields with defaults
            for field in required_fields:
                if field not in result:
                    if field == "confidence":
                        result[field] = 0.5
                    else:
                        result[field] = f"No {field} provided"

            # Validate confidence range
            if not isinstance(result["confidence"], (int, float)) or not 0 <= result["confidence"] <= 1:
                result["confidence"] = 0.5

            return result

        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic response
            return {
                "observation": f"Response from {self.config.role}",
                "reasoning": "LLM response could not be parsed as JSON",
                "conclusion": "Unable to provide structured analysis",
                "confidence": 0.3
            }

    async def execute(self, operation: Optional[str] = None, **kwargs) -> Any:
        """Execute swarm operations."""
        try:
            if operation == "propose_action":
                action_type = kwargs.get("action_type", "unknown")
                params = kwargs.get("params", {})
                return await self.propose_action(action_type, params)
            
            elif operation == "evaluate_proposal":
                proposal = kwargs.get("proposal", {})
                return await self.evaluate_proposal(proposal)
            
            elif operation == "join_swarm":
                peers = kwargs.get("peers", [])
                await self.join_swarm(peers)
                return {"status": "success", "peers_joined": len(peers)}
            
            elif operation == "status":
                return {
                    "role": self.config.role,
                    "initialized": self._is_initialized,
                    "running": self._is_running,
                    "peers": len(self.swarm_peers),
                    "capabilities": self.capabilities
                }
            
            else:
                # Default evaluation
                context = kwargs
                return await self.evaluate(context)

        except Exception as e:
            logger.error(f"Error executing operation {operation}: {str(e)}")
            return {"error": str(e), "operation": operation}

    async def cleanup(self) -> None:
        """Clean up agent resources."""
        try:
            if self.llm:
                await self.llm.close()
            
            self._initialized = False
            self._is_running = False
            self.swarm_peers = []
            logger.info("SwarmAgent cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
        return None