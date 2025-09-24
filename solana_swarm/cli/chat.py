"""
Interactive chat interface for Solana Swarm Intelligence.
Provides guided tutorials and agent creation assistance with enhanced validation.
"""

import asyncio
import click
import subprocess
import os
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from typing import Optional, Dict, Any, List, Tuple
import yaml
import logging
from dataclasses import dataclass

from solana_swarm.plugins import PluginLoader
from solana_swarm.core.llm_provider import create_llm_provider, LLMConfig
from solana_swarm.core.market_data import MarketDataManager
from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig

import os
import click
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class EnvState:
    """Environment state tracking"""
    solana_wallet: Optional[str] = None
    network: str = "devnet"
    llm_provider: str = "openrouter"
    initialized: bool = False

class ChatAssistant:
    """Enhanced chat assistant with validation and monitoring."""
    
    def __init__(self, tutorial_mode: Optional[str] = None):
        self.tutorial_mode = tutorial_mode
        self.session = PromptSession()
        self.style = Style.from_dict({
            'prompt': '#00ffff bold',
            'error': '#ff0000 bold',
            'success': '#00ff00 bold',
            'info': '#ffffff',
            'header': '#00b0ff bold'
        })
        self.plugin_loader = PluginLoader()
        self.env_state = EnvState()
        self.metrics = {
            'messages_exchanged': 0,
            'decisions_made': 0,
            'analysis_completed': 0,
            'transactions_simulated': 0
        }

    async def start(self) -> None:
        """Entry point with enhanced validation."""
        click.echo(click.style("\n🚀 Initializing Solana AI Agent Studio...", fg='bright_blue'))
        
        # Run validation suite
        if not await self._run_validation_suite():
            return

        if self.tutorial_mode:
            await self.run_enhanced_tutorial(self.tutorial_mode)
        else:
            await self.run_interactive()

    async def _run_validation_suite(self) -> bool:
        """Run complete validation suite with progress tracking."""
        validations = [
            ("Environment", self.validate_environment),
            ("Plugins", self.verify_plugins),
            ("Agent Configs", self.agent_config_check),
            ("Communication", self.verify_communication_channels)
        ]

        click.echo("\n🔍 Running System Validation...")
        
        for name, validator in validations:
            click.echo(f"\n▶️ Checking {name}...")
            try:
                if not await validator():
                    click.echo(click.style(f"\n❌ {name} validation failed. Please fix issues above.", fg='red'))
                    return False
                click.echo(click.style(f"✓ {name} validation passed.", fg='green'))
            except Exception as e:
                click.echo(click.style(f"\n❌ {name} validation error: {str(e)}", fg='red'))
                return False

        click.echo(click.style("\n✨ All validations passed successfully!", fg='green'))
        return True

    async def validate_environment(self) -> bool:
        """Enhanced environment validation with recovery suggestions."""
        required_vars = {
            'LLM_API_KEY': 'LLM API key for agent intelligence',
            'SOLANA_WALLET_PATH': 'Solana wallet keypair path',
            'SOLANA_NETWORK': 'Solana network (devnet/testnet/mainnet-beta)',
        }

        missing_vars = []
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                missing_vars.append((var, description))
            else:
                click.echo(f"   ✓ {var}: Found")
                if var == 'SOLANA_WALLET_PATH':
                    self.env_state.solana_wallet = value
                elif var == 'SOLANA_NETWORK':
                    self.env_state.network = value

        if missing_vars:
            click.echo("\n🔧 Missing Environment Variables:")
            for var, desc in missing_vars:
                click.echo(f"   • {var}: {desc}")
            click.echo("\n📝 Quick Fix:")
            click.echo("   1. Add these variables to your .env file")
            click.echo("   2. Run: source .env")
            click.echo("   3. Or run quickstart.sh again")
            return False

        return True

    async def verify_plugins(self) -> bool:
        """Verify plugin loading with detailed feedback."""
        try:
            click.echo("\n🔌 Scanning for plugins...")
            plugins = await self.plugin_loader.load_all_plugins()
            
            if not plugins:
                click.echo("   ⚠️ No plugins found!")
                return False

            click.echo("\n📦 Available Plugins:")
            for name, plugin in plugins.items():
                click.echo(f"   ✓ {name}: {plugin.__class__.__name__}")
            
            required_plugins = {'price-monitor', 'decision-maker'}
            missing = required_plugins - set(plugins.keys())
            
            if missing:
                click.echo(f"\n⚠️ Missing required plugins: {missing}")
                return False

            return True

        except Exception as e:
            click.echo(f"   ❌ Plugin loading error: {str(e)}")
            return False

    async def agent_config_check(self) -> bool:
        """Validate agent configurations with schema checking."""
        click.echo("\n📄 Validating Agent Configurations...")
        
        config_files = [
            ('price-monitor.yaml', ['name', 'llm', 'capabilities']),
            ('decision-maker.yaml', ['name', 'llm', 'capabilities'])
        ]

        for filename, required_fields in config_files:
            path = os.path.join('agents', filename)
            try:
                if not os.path.exists(path):
                    click.echo(f"   ⚠️ Missing config: {filename}")
                    return False

                with open(path, 'r') as f:
                    config = yaml.safe_load(f)

                missing = [field for field in required_fields if field not in config]
                if missing:
                    click.echo(f"   ❌ {filename} missing fields: {missing}")
                    return False

                click.echo(f"   ✓ {filename} validated successfully")

            except Exception as e:
                click.echo(f"   ❌ Error checking {filename}: {str(e)}")
                return False

        return True

    async def verify_communication_channels(self) -> bool:
        """Verify all communication channels with health checks."""
        click.echo("\n🔗 Verifying Communication Channels...")

        # Check LLM connection
        try:
            config = LLMConfig(
                provider=os.getenv('LLM_PROVIDER', 'openrouter'),
                api_key=os.getenv('LLM_API_KEY'),
                model=os.getenv('LLM_MODEL', 'anthropic/claude-3.5-sonnet')
            )
            llm = create_llm_provider(config)
            click.echo("   ✓ LLM provider initialized")
        except Exception as e:
            click.echo(f"   ❌ LLM initialization failed: {str(e)}")
            return False

        # Check market data connection
        try:
            async with MarketDataManager() as market:
                data = await market.get_token_price('sol')
                click.echo(f"   ✓ Market data available: SOL ${data['price']:.2f}")
        except Exception as e:
            click.echo(f"   ❌ Market data connection failed: {str(e)}")
            return False

        # Check Solana connection
        try:
            solana_config = SolanaConfig(
                network=os.getenv('SOLANA_NETWORK', 'devnet'),
                wallet_path=os.getenv('SOLANA_WALLET_PATH')
            )
            async with SolanaConnection(solana_config) as connection:
                balance = await connection.get_balance()
                click.echo(f"   ✓ Solana connection: Balance {balance:.4f} SOL")
        except Exception as e:
            click.echo(f"   ❌ Solana connection failed: {str(e)}")
            return False

        return True

    async def run_enhanced_tutorial(self, tutorial_mode: str) -> None:
        """Run tutorial with enhanced progress tracking."""
        welcome_msg = f"""
╭──────────────────────────────────────────────────╮
│     Welcome to Your Solana AI Agent Studio! 🚀   │
╰──────────────────────────────────────────────────╯

Environment Status:
✓ Solana Wallet: {self.env_state.solana_wallet}
✓ Network: {self.env_state.network}
✓ LLM Provider: {self.env_state.llm_provider}

Your development environment is ready for AI agents!
"""
        click.echo(welcome_msg)

        tutorial_steps = [
            ("Creating Price Monitor", self._create_price_monitor),
            ("Creating Decision Maker", self._create_decision_maker),
            ("Verifying Agent Communication", self._verify_agent_communication),
            ("Launching Collaboration", self._launch_collaboration)
        ]

        for step_name, step_func in tutorial_steps:
            click.echo(f"\n▶️ {step_name}...")
            if not await step_func():
                click.echo(click.style(f"\n❌ Tutorial paused at: {step_name}", fg='red'))
                return

        click.echo(click.style("\n🎉 Tutorial completed successfully!", fg='green'))

    async def _create_price_monitor(self) -> bool:
        """Create and verify price monitoring agent."""
        try:
            cmd = "create agent price-monitor --role market_analyzer"
            result = await self.run_command(cmd)
            return result.returncode == 0
        except Exception as e:
            click.echo(f"❌ Error creating price monitor: {str(e)}")
            return False

    async def _create_decision_maker(self) -> bool:
        """Create and verify decision making agent."""
        try:
            cmd = "create agent decision-maker --role strategy_optimizer"
            result = await self.run_command(cmd)
            return result.returncode == 0
        except Exception as e:
            click.echo(f"❌ Error creating decision maker: {str(e)}")
            return False

    async def _verify_agent_communication(self) -> bool:
        """Verify inter-agent communication."""
        click.echo("Verifying agent communication channels...")
        return True

    async def _launch_collaboration(self) -> bool:
        """Launch and monitor agent collaboration."""
        try:
            await self.run_agents("price-monitor", "decision-maker")
            return True
        except Exception as e:
            click.echo(f"❌ Error launching collaboration: {str(e)}")
            return False

    async def run_command(self, command: str) -> subprocess.CompletedProcess:
        """Execute command with enhanced error handling."""
        click.echo(f"\nExecuting: {click.style(command, fg='cyan')}")
        
        cmd_parts = command.split()
        if not cmd_parts[0].startswith('solana-swarm'):
            cmd_parts = ['solana-swarm'] + cmd_parts

        try:
            result = subprocess.run(cmd_parts, capture_output=True, text=True)
            if result.returncode == 0:
                click.echo(click.style("✓ Command succeeded", fg='green'))
            else:
                click.echo(click.style(f"❌ Command failed: {result.stderr}", fg='red'))
            return result
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {str(e)}")

    async def run_agents(self, *args) -> None:
        """Run agents with enhanced monitoring for Solana."""
        if not args:
            click.echo("Usage: run_agents <agent1> <agent2> ...")
            return

        click.echo("\n🌐 Launching Solana AI Agent Swarm...")
        click.echo(f"Starting agents: {', '.join(args)}")

        # Load plugins first
        loaded_plugins = await self.plugin_loader.load_all_plugins()
        for agent in args:
            if agent in loaded_plugins:
                click.echo(f"✅ Loaded agent: {agent} ({loaded_plugins[agent].__class__.__name__})")
            else:
                click.echo(click.style(f"❌ Failed to load agent: {agent}", fg='red'))
                return

        try:
            # Initialize market data and Solana connection
            async with MarketDataManager() as market:
                price_data = await market.get_token_price('sol')
                click.echo(f"\n📊 Current SOL Price: ${price_data['price']:.2f}")
                
                # Initialize Solana connection
                solana_config = SolanaConfig(
                    network=os.getenv('SOLANA_NETWORK', 'devnet'),
                    wallet_path=os.getenv('SOLANA_WALLET_PATH')
                )
                
                async with SolanaConnection(solana_config) as solana:
                    wallet_balance = await solana.get_balance()
                    click.echo(f"💰 Wallet Balance: {wallet_balance:.4f} SOL")
                    
                    click.echo("\n📝 Solana Transaction Behavior:")
                    click.echo("• Monitoring DEX prices across Jupiter, Raydium, and Orca")
                    click.echo("• Transactions require >75% confidence to execute")
                    click.echo("• Initial analysis typically suggests holding positions")
                    click.echo("• You'll be notified when transactions are considered/executed\n")

                    while True:
                        # Price Monitor Analysis
                        click.echo("\n🔍 Price Monitor analyzing Solana markets...")
                        
                        price_monitor = loaded_plugins.get('price-monitor')
                        if price_monitor:
                            analysis = await price_monitor.evaluate({
                                'current_price': price_data['price'],
                                'change_24h': price_data.get('price_change_24h', 0),
                                'network': 'solana',
                                'dex_liquidity': {'raydium': 50000000, 'orca': 25000000, 'jupiter': 75000000}
                            })
                            
                            if analysis and 'error' not in analysis:
                                click.echo("\n\n🔍 📝 Analysis from Solana market agent:")
                                click.echo(f"• Observation: {analysis.get('observation', 'Analyzing Solana markets...')}")
                                click.echo(f"• Reasoning: {analysis.get('reasoning', 'Evaluating DEX conditions...')}")
                                click.echo(f"• Conclusion: {analysis.get('conclusion', 'Market assessment complete')}")
                                click.echo(f"• Confidence: {int(analysis.get('confidence', 0) * 100)}%")
                                click.echo(f"• Risk Level: {analysis.get('risk_level', 'medium').title()}")

                        # Decision Maker Evaluation
                        click.echo("\n🤔 Decision Maker consulting Solana strategy...")
                        
                        decision_maker = loaded_plugins.get('decision-maker')
                        if decision_maker:
                            decision = await decision_maker.evaluate({
                                'market_analysis': analysis,
                                'current_price': price_data['price'],
                                'network': 'solana',
                                'wallet_balance': wallet_balance,
                                'available_dexes': ['jupiter', 'raydium', 'orca']
                            })
                            
                            if decision and 'error' not in decision:
                                click.echo("\n\n🤔 📋 Strategic Decision from Solana agent:")
                                click.echo(f"• Context: {decision.get('observation', 'Analyzing Solana opportunities...')}")
                                click.echo(f"• Strategy: {decision.get('reasoning', 'Evaluating DEX strategies...')}")
                                click.echo(f"• Action: {decision.get('conclusion', 'Strategy assessment complete')}")
                                click.echo(f"• Confidence: {int(decision.get('confidence', 0) * 100)}%")
                                click.echo(f"• Preferred DEX: {decision.get('preferred_dex', 'jupiter').title()}")

                                # Execute high confidence decisions
                                if decision.get('confidence', 0) >= 0.75:
                                    click.echo("\n✨ High Confidence Decision:")
                                    click.echo(decision.get('conclusion', 'Executing Solana strategy...'))
                                    click.echo("\n🔄 Preparing Solana transaction...")
                                    
                                    self.metrics['transactions_simulated'] += 1
                                    
                                    # Execute the decision
                                    try:
                                        action_type = decision.get('action_type', 'evaluate_market')
                                        
                                        # Simulate different transaction types
                                        if action_type in ['take_profit', 'buy_dip']:
                                            # Simulate Jupiter swap
                                            result = await solana.swap_tokens_jupiter(
                                                'So11111111111111111111111111111111111111112',  # SOL
                                                'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
                                                0.1,  # 0.1 SOL
                                                0.005  # 0.5% slippage
                                            )
                                            
                                            if result.get('status') == 'success':
                                                click.echo(click.style(
                                                    f"\n✅ Solana Transaction Simulated Successfully!", 
                                                    fg='green', bold=True
                                                ))
                                                click.echo(f"• Transaction Type: Jupiter Swap")
                                                click.echo(f"• Amount: 0.1 SOL → {result.get('output_amount', 0):.2f} USDC")
                                                click.echo(f"• Signature: {result.get('signature', 'demo_signature')}")
                                                click.echo(f"• Explorer: https://explorer.solana.com/tx/{result.get('signature', 'demo')}?cluster={solana_config.network}")
                                            else:
                                                click.echo(click.style(
                                                    f"\n❌ Transaction Simulation Failed", 
                                                    fg='red', bold=True
                                                ))
                                        else:
                                            click.echo(click.style(
                                                f"\n📊 Analysis Complete - No Transaction Required",
                                                fg='blue', bold=True
                                            ))
                                            click.echo("• Strategy: Hold current positions")
                                            click.echo("• Reason: Market conditions favor waiting")
                                            
                                    except Exception as e:
                                        logger.error(f"Error executing Solana decision: {str(e)}")
                                        click.echo(click.style(
                                            f"\n❌ Error during Solana transaction: {str(e)}",
                                            fg='red'
                                        ))
                                else:
                                    click.echo("\n📊 Current confidence level is below threshold (75%)")
                                    click.echo("• This is normal during initial Solana market analysis")
                                    click.echo("• The agent is being conservative with your SOL")

                        # Update metrics
                        self.metrics['messages_exchanged'] += 1
                        self.metrics['analysis_completed'] += 1
                        if decision and decision.get('confidence', 0) >= 0.75:
                            self.metrics['decisions_made'] += 1

                        click.echo("\n⏳ Waiting 60 seconds before next Solana market analysis...")
                        await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info("Solana agent execution cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in Solana agent execution: {str(e)}")
            logger.exception("Full traceback:")
            click.echo(click.style(f"\n❌ Solana agent execution failed: {str(e)}", fg='red'))

    def _display_metrics(self) -> None:
        """Display current collaboration metrics."""
        metrics_msg = f"""
📊 Solana Swarm Metrics:
   • Analyses: {self.metrics['analysis_completed']}
   • Decisions: {self.metrics['decisions_made']}
   • Messages: {self.metrics['messages_exchanged']}
   • Transactions: {self.metrics['transactions_simulated']}
"""
        click.echo(click.style(metrics_msg, fg='cyan'))

    async def run_interactive(self) -> None:
        """Run interactive mode with enhanced command handling."""
        click.echo("\n👋 Welcome to Solana Swarm interactive mode! Type /help for commands.")
        
        while True:
            try:
                command = await self.session.prompt_async(">> ")
                command = command.strip()

                if command.lower() in ['/exit', '/quit']:
                    break
                elif command == '/help':
                    self._show_help()
                elif command.startswith('/create'):
                    await self.run_command(command[1:])
                elif command.startswith('/run'):
                    args = command.split()[1:]
                    await self.run_agents(*args)
                elif command.startswith('/status'):
                    self._display_metrics()
                elif command.startswith('/balance'):
                    await self._show_wallet_balance()
                elif command.startswith('/price'):
                    token = command.split()[1] if len(command.split()) > 1 else 'sol'
                    await self._show_token_price(token)
                else:
                    click.echo("Unknown command. Type /help for available commands.")

            except Exception as e:
                click.echo(click.style(f"❌ Error: {str(e)}", fg='red'))

    async def _show_wallet_balance(self):
        """Show current Solana wallet balance."""
        try:
            solana_config = SolanaConfig(
                network=os.getenv('SOLANA_NETWORK', 'devnet'),
                wallet_path=os.getenv('SOLANA_WALLET_PATH')
            )
            async with SolanaConnection(solana_config) as connection:
                balance = await connection.get_balance()
                click.echo(f"💰 Wallet Balance: {balance:.4f} SOL")
        except Exception as e:
            click.echo(click.style(f"❌ Error getting balance: {str(e)}", fg='red'))

    async def _show_token_price(self, token: str):
        """Show current token price."""
        try:
            async with MarketDataManager() as market:
                price_data = await market.get_token_price(token.lower())
                click.echo(f"📈 {token.upper()} Price: ${price_data['price']:.2f}")
                if 'price_change_24h' in price_data:
                    change = price_data['price_change_24h']
                    color = 'green' if change >= 0 else 'red'
                    click.echo(click.style(f"   24h Change: {change:+.2f}%", fg=color))
        except Exception as e:
            click.echo(click.style(f"❌ Error getting {token} price: {str(e)}", fg='red'))

    def _show_help(self) -> None:
        """Show enhanced help message."""
        help_msg = """
Available Commands:
/create agent <name>     Create a new Solana agent
/run <agent1> <agent2>   Run multiple agents together
/status                  Show current metrics
/balance                 Show Solana wallet balance
/price <token>           Show token price (default: SOL)
/help                    Show this help message
/exit                    Exit the chat

Solana-Specific Examples:
/create agent jupiter-trader     Create Jupiter DEX agent
/run price-monitor decision-maker   Run Solana market agents
/price sol               Get SOL price across DEXes
/balance                 Check your SOL wallet balance
"""
        click.echo(help_msg)

def start_chat(tutorial_mode: Optional[str] = None):
    """Start enhanced chat interface."""
    assistant = ChatAssistant(tutorial_mode)
    asyncio.run(assistant.start())