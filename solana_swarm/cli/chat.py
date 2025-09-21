"""
Interactive chat interface for Solana Swarm agents
"""

import asyncio
import os
from typing import Optional, Dict, Any

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

from solana_swarm.plugins.loader import PluginLoader
from solana_swarm.core.market_data import MarketDataManager

console = Console()

class ChatSession:
    """Interactive chat session with Solana Swarm agents."""
    
    def __init__(self):
        self.loader = PluginLoader()
        self.active_agents = {}
        self.market_data = None
        self.session_active = True
    
    async def initialize(self, agent_name: Optional[str] = None):
        """Initialize chat session."""
        rprint("🚀 [cyan]Initializing Solana Swarm Chat...[/cyan]")
        
        # Initialize market data
        self.market_data = MarketDataManager()
        
        # Load agents
        if agent_name:
            try:
                agent = await self.loader.load_plugin(agent_name)
                self.active_agents[agent_name] = agent
                rprint(f"✅ Loaded agent: {agent_name}")
            except Exception as e:
                rprint(f"❌ [red]Failed to load agent {agent_name}: {e}[/red]")
                return False
        else:
            # Load all available agents
            try:
                self.active_agents = await self.loader.load_all_plugins()
                rprint(f"✅ Loaded {len(self.active_agents)} agents")
            except Exception as e:
                rprint(f"❌ [red]Failed to load agents: {e}[/red]")
                return False
        
        return True
    
    async def show_welcome(self):
        """Display welcome message and help."""
        welcome_text = """
# 🤖 Solana Swarm Intelligence Chat

Welcome to the interactive chat interface! You can:

- **Ask questions** about market conditions
- **Request analysis** from specific agents  
- **Get price updates** for tokens
- **Execute strategies** (simulation mode)

## Available Commands:
- `/help` - Show this help message
- `/agents` - List active agents
- `/status` - Show system status
- `/price <token>` - Get token price
- `/market` - Get market overview
- `/quit` - Exit chat

## Example Queries:
- "What's the current SOL price?"
- "Analyze the market conditions for arbitrage"
- "Should I buy SOL right now?"
- "Show me the risks of trading USDC/SOL"
        """
        
        console.print(Panel(
            Markdown(welcome_text),
            title="Welcome to Solana Swarm Chat",
            border_style="cyan"
        ))
    
    async def process_command(self, message: str) -> bool:
        """Process chat commands."""
        message = message.strip()
        
        if message == "/quit":
            return False
        
        elif message == "/help":
            await self.show_welcome()
        
        elif message == "/agents":
            await self.show_agents()
        
        elif message == "/status":
            await self.show_status()
        
        elif message.startswith("/price"):
            parts = message.split()
            token = parts[1] if len(parts) > 1 else "sol"
            await self.show_price(token)
        
        elif message == "/market":
            await self.show_market_overview()
        
        else:
            await self.process_query(message)
        
        return True
    
    async def show_agents(self):
        """Show active agents."""
        if not self.active_agents:
            rprint("❌ [red]No agents loaded[/red]")
            return
        
        rprint("🤖 [cyan]Active Agents:[/cyan]")
        for name, agent in self.active_agents.items():
            role = getattr(agent, "role", "unknown")
            capabilities = getattr(agent, "capabilities", [])
            rprint(f"  • **{name}** ({role}) - {', '.join(capabilities) if capabilities else 'No capabilities listed'}")
    
    async def show_status(self):
        """Show system status."""
        try:
            # Get market data
            async with MarketDataManager() as market_data:
                sol_data = await market_data.get_token_price("sol")
                network_stats = await market_data.get_solana_network_stats()
            
            status_text = f"""
## 📊 System Status

**Market Data:**
- SOL Price: ${sol_data.get('price', 0):.2f}
- 24h Change: {sol_data.get('change_24h', 0):+.2f}%
- Source: {sol_data.get('source', 'unknown')}

**Solana Network:**
- TPS: {network_stats.get('tps', 0):,.0f}
- Active Validators: {network_stats.get('active_validators', 0):,}

**Agents:**
- Loaded: {len(self.active_agents)}
- Active: {len([a for a in self.active_agents.values() if getattr(a, '_is_initialized', False)])}
            """
            
            console.print(Panel(Markdown(status_text), title="System Status", border_style="green"))
            
        except Exception as e:
            rprint(f"❌ [red]Error getting status: {e}[/red]")
    
    async def show_price(self, token: str):
        """Show token price information."""
        try:
            async with MarketDataManager() as market_data:
                price_data = await market_data.get_token_price(token.lower())
            
            price = price_data.get("price", 0)
            change = price_data.get("change_24h", 0)
            volume = price_data.get("volume_24h", 0)
            source = price_data.get("source", "unknown")
            
            change_color = "green" if change >= 0 else "red"
            arrow = "📈" if change >= 0 else "📉"
            
            price_text = f"""
## {arrow} {token.upper()} Price Information

**Current Price:** ${price:.2f}
**24h Change:** [{change_color}]{change:+.2f}%[/{change_color}]
**24h Volume:** ${volume:,.0f}
**Data Source:** {source}
**Last Updated:** {price_data.get('last_updated', 'Unknown')}
            """
            
            console.print(Panel(Markdown(price_text), title=f"{token.upper()} Price", border_style="blue"))
            
        except Exception as e:
            rprint(f"❌ [red]Error getting price for {token}: {e}[/red]")
    
    async def show_market_overview(self):
        """Show market overview."""
        try:
            async with MarketDataManager() as market_data:
                context = await market_data.get_market_context()
            
            sol_price = context.get("sol", {}).get("price", 0)
            dex_data = context.get("dex_ecosystem", {})
            network_data = context.get("network", {})
            indicators = context.get("indicators", {})
            
            overview_text = f"""
## 🌊 Solana Market Overview

**SOL Performance:**
- Current Price: ${sol_price:.2f}
- Market Sentiment: {indicators.get('market_sentiment', 'unknown').title()}
- Trend Strength: {indicators.get('trend_strength', 'unknown').title()}

**DeFi Ecosystem:**
- Total DEX TVL: ${dex_data.get('raydium_tvl', 0) + dex_data.get('orca_tvl', 0):,.0f}
- 24h DEX Volume: ${dex_data.get('total_dex_volume', 0):,.0f}
- DEX Health: {indicators.get('dex_health', 'unknown').title()}

**Network Stats:**
- Current TPS: {network_data.get('tps', 0):,.0f}
- Active Validators: {network_data.get('validators', 0):,}
- 24h Network Fees: {network_data.get('fees_24h', 0):,.0f} SOL
            """
            
            console.print(Panel(Markdown(overview_text), title="Market Overview", border_style="magenta"))
            
        except Exception as e:
            rprint(f"❌ [red]Error getting market overview: {e}[/red]")
    
    async def process_query(self, query: str):
        """Process user query with agents."""
        if not self.active_agents:
            rprint("❌ [red]No agents available to process query[/red]")
            return
        
        rprint(f"🤔 [dim]Processing: {query}[/dim]")
        
        # Determine which agents to use based on query
        relevant_agents = self.select_agents_for_query(query)
        
        if not relevant_agents:
            rprint("❌ [red]No relevant agents found for this query[/red]")
            return
        
        # Get market context
        try:
            async with MarketDataManager() as market_data:
                market_context = await market_data.get_market_context()
        except Exception:
            market_context = {}
        
        # Process query with each relevant agent
        responses = {}
        for agent_name in relevant_agents:
            try:
                agent = self.active_agents[agent_name]
                context = {
                    "query": query,
                    "market_context": market_context,
                    "timestamp": market_context.get("timestamp")
                }
                
                result = await agent.evaluate(context)
                responses[agent_name] = result
                
            except Exception as e:
                responses[agent_name] = {"error": str(e)}
        
        # Display responses
        await self.display_agent_responses(query, responses)
    
    def select_agents_for_query(self, query: str) -> list:
        """Select relevant agents based on query content."""
        query_lower = query.lower()
        selected = []
        
        # Keywords for different agent types
        price_keywords = ["price", "cost", "value", "worth", "expensive", "cheap"]
        risk_keywords = ["risk", "safe", "dangerous", "volatility", "loss", "protect"]
        strategy_keywords = ["strategy", "trade", "buy", "sell", "invest", "opportunity"]
        market_keywords = ["market", "trend", "analysis", "condition", "sentiment"]
        
        for agent_name, agent in self.active_agents.items():
            role = getattr(agent, "role", "")
            
            # Select based on role and query content
            if "market_analyzer" in role and any(kw in query_lower for kw in market_keywords + price_keywords):
                selected.append(agent_name)
            elif "risk_manager" in role and any(kw in query_lower for kw in risk_keywords):
                selected.append(agent_name)
            elif "strategy_optimizer" in role and any(kw in query_lower for kw in strategy_keywords):
                selected.append(agent_name)
            elif "decision_maker" in role:
                selected.append(agent_name)  # Decision makers are generally relevant
        
        # If no specific agents selected, use all available
        if not selected:
            selected = list(self.active_agents.keys())[:2]  # Limit to 2 agents
        
        return selected
    
    async def display_agent_responses(self, query: str, responses: Dict[str, Any]):
        """Display agent responses in a formatted way."""
        console.print(f"\n💭 [bold]Query:[/bold] {query}")
        
        for agent_name, response in responses.items():
            if "error" in response:
                rprint(f"\n❌ [red]{agent_name}: Error - {response['error']}[/red]")
                continue
            
            # Format response based on agent type
            agent = self.active_agents[agent_name]
            role = getattr(agent, "role", "unknown")
            
            if role == "market_analyzer":
                await self.format_market_response(agent_name, response)
            elif role == "risk_manager":
                await self.format_risk_response(agent_name, response)
            elif role == "strategy_optimizer":
                await self.format_strategy_response(agent_name, response)
            else:
                await self.format_generic_response(agent_name, response)
    
    async def format_market_response(self, agent_name: str, response: Dict[str, Any]):
        """Format market analyzer response."""
        observation = response.get("observation", "No observation available")
        reasoning = response.get("reasoning", "No reasoning provided")
        conclusion = response.get("conclusion", "No conclusion reached")
        confidence = response.get("confidence", 0)
        
        response_text = f"""
**Market Analysis from {agent_name}:**

*Observation:* {observation}

*Analysis:* {reasoning}

*Conclusion:* {conclusion}

*Confidence:* {confidence:.1%}
        """
        
        console.print(Panel(Markdown(response_text), title="📊 Market Analysis", border_style="blue"))
    
    async def format_risk_response(self, agent_name: str, response: Dict[str, Any]):
        """Format risk manager response."""
        risk_level = response.get("risk_level", "unknown")
        assessment = response.get("assessment", "No assessment available")
        recommendations = response.get("recommendations", [])
        
        risk_color = {"low": "green", "medium": "yellow", "high": "red"}.get(risk_level, "white")
        
        response_text = f"""
**Risk Assessment from {agent_name}:**

*Risk Level:* [{risk_color}]{risk_level.title()}[/{risk_color}]

*Assessment:* {assessment}

*Recommendations:*
{chr(10).join(f"• {rec}" for rec in recommendations) if recommendations else "• No specific recommendations"}
        """
        
        console.print(Panel(Markdown(response_text), title="⚖️ Risk Analysis", border_style="yellow"))
    
    async def format_strategy_response(self, agent_name: str, response: Dict[str, Any]):
        """Format strategy optimizer response."""
        strategy = response.get("strategy", "No strategy provided")
        confidence = response.get("confidence", 0)
        expected_outcome = response.get("expected_outcome", "Unknown")
        
        response_text = f"""
**Strategy Recommendation from {agent_name}:**

*Strategy:* {strategy}

*Expected Outcome:* {expected_outcome}

*Confidence:* {confidence:.1%}
        """
        
        console.print(Panel(Markdown(response_text), title="🎯 Strategy Optimization", border_style="green"))
    
    async def format_generic_response(self, agent_name: str, response: Dict[str, Any]):
        """Format generic agent response."""
        # Try to extract meaningful information
        decision = response.get("decision", "")
        reasoning = response.get("reasoning", "")
        confidence = response.get("confidence", 0)
        
        if decision and reasoning:
            response_text = f"""
**Response from {agent_name}:**

*Decision:* {decision}

*Reasoning:* {reasoning}

*Confidence:* {confidence:.1%}
            """
        else:
            # Fallback to raw response
            response_text = f"""
**Response from {agent_name}:**

{str(response)}
            """
        
        console.print(Panel(Markdown(response_text), title=f"🤖 {agent_name}", border_style="cyan"))
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.loader.cleanup()
        if self.market_data:
            await self.market_data.close()

async def start_chat(agent_name: Optional[str] = None, config_file: Optional[str] = None):
    """Start interactive chat session."""
    session = ChatSession()
    
    try:
        # Initialize session
        if not await session.initialize(agent_name):
            return
        
        # Show welcome message
        await session.show_welcome()
        
        # Main chat loop
        while session.session_active:
            try:
                # Get user input
                message = Prompt.ask("\n[cyan]You[/cyan]", default="")
                
                if not message.strip():
                    continue
                
                # Process message
                continue_chat = await session.process_command(message)
                if not continue_chat:
                    break
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as e:
                rprint(f"❌ [red]Chat error: {e}[/red]")
    
    finally:
        await session.cleanup()
        rprint("\n👋 [yellow]Chat session ended. Thank you for using Solana Swarm![/yellow]")

def main():
    """Main entry point for chat CLI."""
    import typer
    
    app = typer.Typer()
    
    @app.command()
    def chat(
        agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Specific agent to chat with"),
        config: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file")
    ):
        """Start interactive chat with Solana Swarm agents."""
        try:
            asyncio.run(start_chat(agent, config))
        except KeyboardInterrupt:
            rprint("\n👋 [yellow]Chat ended[/yellow]")
    
    app()

if __name__ == "__main__":
    main()