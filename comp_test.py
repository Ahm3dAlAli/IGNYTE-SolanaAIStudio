
"""
Comprehensive Test Suite for Solana Swarm Intelligence Framework
Tests all integrations, agents, and swarm functionality
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class TestRunner:
    """Orchestrates comprehensive testing"""
    
    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'total': 0
        }
        self.test_details = []
        self.start_time = None
    
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
    
    def print_test(self, name: str, status: str, details: str = ""):
        """Print test result"""
        self.results['total'] += 1
        
        if status == "PASS":
            self.results['passed'] += 1
            icon = f"{Colors.GREEN}✅{Colors.ENDC}"
        elif status == "FAIL":
            self.results['failed'] += 1
            icon = f"{Colors.RED}❌{Colors.ENDC}"
        else:  # WARNING
            self.results['warnings'] += 1
            icon = f"{Colors.YELLOW}⚠️{Colors.ENDC}"
        
        print(f"{icon} {name}")
        if details:
            print(f"   {Colors.CYAN}{details}{Colors.ENDC}")
        
        self.test_details.append({
            'name': name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    async def test_environment(self) -> bool:
        """Test 1: Environment Configuration"""
        self.print_header("TEST 1: Environment Configuration")
        
        required_vars = {
            'LLM_API_KEY': 'LLM API key for agent intelligence',
            'SOLANA_WALLET_PATH': 'Solana wallet path',
            'SOLANA_NETWORK': 'Solana network configuration',
        }
        
        all_good = True
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                self.print_test(
                    f"Environment: {var}",
                    "PASS",
                    f"Found: {value[:20]}..." if len(value) > 20 else f"Found: {value}"
                )
            else:
                self.print_test(
                    f"Environment: {var}",
                    "FAIL",
                    f"Missing: {description}"
                )
                all_good = False
        
        return all_good
    
    async def test_solana_connection(self) -> bool:
        """Test 2: Solana Blockchain Connection"""
        self.print_header("TEST 2: Solana Blockchain Connection")
        
        try:
            from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig
            
            config = SolanaConfig(
                network=os.getenv('SOLANA_NETWORK', 'devnet'),
                wallet_path=os.getenv('SOLANA_WALLET_PATH', '~/.config/solana/id.json')
            )
            
            async with SolanaConnection(config) as connection:
                # Test 2.1: Connection initialization
                self.print_test(
                    "Solana Connection: Initialize",
                    "PASS",
                    f"Connected to {config.network}"
                )
                
                # Test 2.2: Public key
                pubkey = str(connection.public_key)
                self.print_test(
                    "Solana Connection: Public Key",
                    "PASS",
                    f"Wallet: {pubkey[:8]}...{pubkey[-8:]}"
                )
                
                # Test 2.3: Balance check
                balance = await connection.get_balance()
                status = "PASS" if balance >= 0 else "FAIL"
                self.print_test(
                    "Solana Connection: Balance Check",
                    status,
                    f"Balance: {balance:.4f} SOL"
                )
                
                # Test 2.4: Network statistics
                stats = await connection.get_network_stats()
                self.print_test(
                    "Solana Connection: Network Stats",
                    "PASS",
                    f"TPS: {stats.get('tps', 0):.0f}, Slot: {stats.get('current_slot', 0):,}"
                )
                
                # Test 2.5: Account info
                account_info = await connection.get_account_info(connection.public_key)
                if account_info:
                    self.print_test(
                        "Solana Connection: Account Info",
                        "PASS",
                        f"Lamports: {account_info.get('lamports', 0):,}"
                    )
                else:
                    self.print_test(
                        "Solana Connection: Account Info",
                        "WARNING",
                        "Account info not available"
                    )
                
                return True
                
        except Exception as e:
            self.print_test(
                "Solana Connection: Critical Failure",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_market_data(self) -> bool:
        """Test 3: Market Data Integration"""
        self.print_header("TEST 3: Market Data Integration")
        
        try:
            from solana_swarm.core.market_data import MarketDataManager
            
            async with MarketDataManager() as market:
                # Test 3.1: SOL price
                sol_data = await market.get_token_price('sol')
                self.print_test(
                    "Market Data: SOL Price",
                    "PASS",
                    f"${sol_data['price']:.2f} (24h: {sol_data.get('price_change_24h', 0):+.2f}%)"
                )
                
                # Test 3.2: USDC price
                usdc_data = await market.get_token_price('usdc')
                self.print_test(
                    "Market Data: USDC Price",
                    "PASS",
                    f"${usdc_data['price']:.4f}"
                )
                
                # Test 3.3: Market overview
                overview = await market.get_market_overview()
                token_count = len(overview.get('tokens', {}))
                self.print_test(
                    "Market Data: Market Overview",
                    "PASS",
                    f"Retrieved {token_count} token prices"
                )
                
                return True
                
        except Exception as e:
            self.print_test(
                "Market Data: Critical Failure",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_jupiter_integration(self) -> bool:
        """Test 4: Jupiter DEX Integration"""
        self.print_header("TEST 4: Jupiter DEX Integration")
        
        try:
            from solana_swarm.integrations.jupiter.client import JupiterClient
            
            client = JupiterClient()
            
            # Test 4.1: Supported tokens
            tokens = await client.get_supported_tokens()
            self.print_test(
                "Jupiter: Supported Tokens",
                "PASS",
                f"Found {len(tokens)} supported tokens"
            )
            
            # Test 4.2: Price quote
            sol_mint = "So11111111111111111111111111111111111111112"
            usdc_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            
            price_data = await client.get_price(sol_mint, usdc_mint, 1000000000)
            self.print_test(
                "Jupiter: Price Quote",
                "PASS",
                f"1 SOL = ${price_data['price']:.2f} USDC"
            )
            
            # Test 4.3: Route quote
            quote = await client.get_quote(sol_mint, usdc_mint, 1000000000, 50)
            self.print_test(
                "Jupiter: Route Quote",
                "PASS",
                f"Impact: {quote.price_impact_pct}%, Routes: {len(quote.route_plan)}"
            )
            
            await client.close()
            return True
            
        except Exception as e:
            self.print_test(
                "Jupiter: Critical Failure",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_dex_integrations(self) -> bool:
        """Test 5: All DEX Integrations"""
        self.print_header("TEST 5: DEX Integrations (Raydium, Orca)")
        
        try:
            from solana_swarm.core.market_data import MarketDataManager
            
            async with MarketDataManager() as market:
                dexs = ['raydium', 'orca', 'jupiter']
                all_success = True
                
                for dex_name in dexs:
                    try:
                        dex_data = await market.get_dex_data(dex_name)
                        self.print_test(
                            f"DEX Integration: {dex_name.title()}",
                            "PASS",
                            f"TVL: ${dex_data.tvl:,.0f}, Volume: ${dex_data.volume_24h:,.0f}"
                        )
                    except Exception as e:
                        self.print_test(
                            f"DEX Integration: {dex_name.title()}",
                            "WARNING",
                            str(e)
                        )
                        all_success = False
                
                return all_success
                
        except Exception as e:
            self.print_test(
                "DEX Integration: Critical Failure",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_agent_loading(self) -> bool:
        """Test 6: Agent Loading System"""
        self.print_header("TEST 6: Agent Loading System")
        
        try:
            from solana_swarm.plugins.loader import PluginLoader
            
            loader = PluginLoader()
            required_agents = ['price-monitor', 'decision-maker']
            loaded_agents = {}
            
            for agent_name in required_agents:
                try:
                    agent = await loader.load_plugin(agent_name)
                    loaded_agents[agent_name] = agent
                    self.print_test(
                        f"Agent Loading: {agent_name}",
                        "PASS",
                        f"Role: {agent.role}, Capabilities: {len(agent.capabilities)}"
                    )
                except Exception as e:
                    self.print_test(
                        f"Agent Loading: {agent_name}",
                        "FAIL",
                        str(e)
                    )
                    return False
            
            await loader.cleanup()
            return True
            
        except Exception as e:
            self.print_test(
                "Agent Loading: Critical Failure",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_agent_evaluation(self) -> bool:
        """Test 7: Agent Evaluation"""
        self.print_header("TEST 7: Agent Evaluation & Decision Making")
        
        try:
            from solana_swarm.plugins.loader import PluginLoader
            from solana_swarm.core.market_data import MarketDataManager
            
            loader = PluginLoader()
            
            # Test 7.1: Price Monitor Evaluation
            price_agent = await loader.load_plugin('price-monitor')
            
            async with MarketDataManager() as market:
                sol_data = await market.get_token_price('sol')
                
                context = {
                    'token': 'sol',
                    'price': sol_data['price'],
                    'network': 'devnet',
                    'current_price': sol_data['price']
                }
                
                result = await price_agent.evaluate(context)
                
                if 'error' not in result:
                    self.print_test(
                        "Agent Evaluation: Price Monitor",
                        "PASS",
                        f"Confidence: {result.get('confidence', 0):.2f}, Risk: {result.get('risk_level', 'unknown')}"
                    )
                else:
                    self.print_test(
                        "Agent Evaluation: Price Monitor",
                        "FAIL",
                        result['error']
                    )
                    return False
                
                # Test 7.2: Decision Maker Evaluation
                decision_agent = await loader.load_plugin('decision-maker')
                
                decision_context = {
                    'market_analysis': result,
                    'current_price': sol_data['price'],
                    'network': 'devnet'
                }
                
                decision = await decision_agent.evaluate(decision_context)
                
                if 'error' not in decision:
                    self.print_test(
                        "Agent Evaluation: Decision Maker",
                        "PASS",
                        f"Confidence: {decision.get('confidence', 0):.2f}, Action: {decision.get('action_type', 'unknown')}"
                    )
                else:
                    self.print_test(
                        "Agent Evaluation: Decision Maker",
                        "FAIL",
                        decision['error']
                    )
                    return False
            
            await loader.cleanup()
            return True
            
        except Exception as e:
            self.print_test(
                "Agent Evaluation: Critical Failure",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_swarm_functionality(self) -> bool:
        """Test 8: Swarm Intelligence"""
        self.print_header("TEST 8: Swarm Intelligence & Consensus")
        
        try:
            from solana_swarm.core.swarm_agent import SwarmAgent, SwarmConfig
            from solana_swarm.core.llm_provider import LLMConfig
            
            # Create LLM config
            llm_config = LLMConfig(
                provider=os.getenv('LLM_PROVIDER', 'openrouter'),
                api_key=os.getenv('LLM_API_KEY', 'demo'),
                model=os.getenv('LLM_MODEL', 'anthropic/claude-3.5-sonnet')
            )
            
            # Test 8.1: Create multiple agents
            agents = []
            roles = ['market_analyzer', 'risk_manager', 'strategy_optimizer']
            
            for role in roles:
                config = SwarmConfig(
                    role=role,
                    min_confidence=0.7,
                    llm=llm_config
                )
                agent = SwarmAgent(config)
                await agent.initialize()
                agents.append(agent)
            
            self.print_test(
                "Swarm: Agent Creation",
                "PASS",
                f"Created {len(agents)} specialized agents"
            )
            
            # Test 8.2: Form swarm network
            await agents[0].join_swarm(agents[1:])
            self.print_test(
                "Swarm: Network Formation",
                "PASS",
                f"Formed network with {len(agents[0].swarm_peers)} peers"
            )
            
            # Test 8.3: Proposal and consensus
            proposal_params = {
                "token": "SOL",
                "action": "analyze_market",
                "amount": 1.0,
                "network": "devnet"
            }
            
            result = await agents[0].propose_action("analysis", proposal_params)
            
            consensus_status = "PASS" if result.get('total_votes', 0) > 0 else "WARNING"
            self.print_test(
                "Swarm: Consensus Mechanism",
                consensus_status,
                f"Votes: {result.get('total_votes', 0)}, Approval: {result.get('approval_rate', 0):.1%}"
            )
            
            # Test 8.4: Individual evaluations
            for i, agent in enumerate(agents):
                try:
                    eval_result = await agent.evaluate({'test': 'data'})
                    if 'error' not in eval_result:
                        self.print_test(
                            f"Swarm: Agent {roles[i]} Evaluation",
                            "PASS",
                            f"Confidence: {eval_result.get('confidence', 0):.2f}"
                        )
                    else:
                        self.print_test(
                            f"Swarm: Agent {roles[i]} Evaluation",
                            "WARNING",
                            "Evaluation returned error"
                        )
                except Exception as e:
                    self.print_test(
                        f"Swarm: Agent {roles[i]} Evaluation",
                        "WARNING",
                        str(e)
                    )
            
            # Cleanup
            for agent in agents:
                await agent.cleanup()
            
            return True
            
        except Exception as e:
            self.print_test(
                "Swarm: Critical Failure",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_memory_system(self) -> bool:
        """Test 9: Memory & Learning System"""
        self.print_header("TEST 9: Memory & Learning System")
        
        try:
            from solana_swarm.core.memory_manager import MemoryManager, StrategyOutcome
            
            memory = MemoryManager()
            
            # Test 9.1: Store data
            test_data = {
                'strategy': 'arbitrage',
                'profit': 0.05,
                'execution_time': 2.5
            }
            
            await memory.store('strategies', test_data, {'network': 'solana'})
            self.print_test(
                "Memory: Data Storage",
                "PASS",
                "Stored strategy data successfully"
            )
            
            # Test 9.2: Retrieve data
            retrieved = await memory.retrieve('strategies', limit=5)
            self.print_test(
                "Memory: Data Retrieval",
                "PASS",
                f"Retrieved {len(retrieved)} records"
            )
            
            # Test 9.3: Strategy outcome recording
            outcome = StrategyOutcome(
                strategy_id='test_strategy',
                timestamp=datetime.now().isoformat(),
                success=True,
                confidence_scores={'agent1': 0.8, 'agent2': 0.9},
                actual_profit=0.05,
                predicted_profit=0.04,
                execution_time=2.5,
                agents_involved=['agent1', 'agent2']
            )
            
            await memory.record_strategy_outcome(outcome)
            self.print_test(
                "Memory: Strategy Outcome",
                "PASS",
                "Recorded strategy outcome"
            )
            
            # Test 9.4: Performance metrics
            performance = await memory.get_strategy_performance()
            self.print_test(
                "Memory: Performance Metrics",
                "PASS",
                f"Executions: {performance['total_executions']}, Success: {performance['success_rate']:.1%}"
            )
            
            return True
            
        except Exception as e:
            self.print_test(
                "Memory: Critical Failure",
                "FAIL",
                str(e)
            )
            return False
    
    async def test_end_to_end_workflow(self) -> bool:
        """Test 10: End-to-End Workflow"""
        self.print_header("TEST 10: End-to-End Trading Workflow Simulation")
        
        try:
            from solana_swarm.plugins.loader import PluginLoader
            from solana_swarm.core.market_data import MarketDataManager
            from solana_swarm.core.solana_integration import SolanaConnection, SolanaConfig
            
            # Step 1: Load agents
            loader = PluginLoader()
            price_agent = await loader.load_plugin('price-monitor')
            decision_agent = await loader.load_plugin('decision-maker')
            
            self.print_test(
                "E2E: Agent Initialization",
                "PASS",
                "Loaded price-monitor and decision-maker"
            )
            
            # Step 2: Get market data
            async with MarketDataManager() as market:
                sol_data = await market.get_token_price('sol')
                
                self.print_test(
                    "E2E: Market Data Retrieval",
                    "PASS",
                    f"SOL: ${sol_data['price']:.2f}"
                )
                
                # Step 3: Analyze market
                analysis = await price_agent.evaluate({
                    'token': 'sol',
                    'price': sol_data['price'],
                    'network': 'devnet'
                })
                
                self.print_test(
                    "E2E: Market Analysis",
                    "PASS",
                    f"Confidence: {analysis.get('confidence', 0):.2f}"
                )
                
                # Step 4: Make decision
                decision = await decision_agent.evaluate({
                    'market_analysis': analysis,
                    'current_price': sol_data['price'],
                    'network': 'devnet'
                })
                
                self.print_test(
                    "E2E: Strategic Decision",
                    "PASS",
                    f"Action: {decision.get('action_type', 'unknown')}, Confidence: {decision.get('confidence', 0):.2f}"
                )
                
                # Step 5: Simulate execution (if high confidence)
                if decision.get('confidence', 0) >= 0.75:
                    config = SolanaConfig(
                        network='devnet',
                        wallet_path=os.getenv('SOLANA_WALLET_PATH')
                    )
                    
                    async with SolanaConnection(config) as solana:
                        # Simulate transaction
                        result = await solana.swap_tokens_jupiter(
                            'So11111111111111111111111111111111111111112',
                            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                            0.1,
                            0.005
                        )
                        
                        self.print_test(
                            "E2E: Transaction Simulation",
                            "PASS",
                            f"Signature: {result.get('signature', 'N/A')[:16]}..."
                        )
                else:
                    self.print_test(
                        "E2E: Transaction Simulation",
                        "WARNING",
                        "Skipped: Confidence below threshold"
                    )
            
            await loader.cleanup()
            return True
            
        except Exception as e:
            self.print_test(
                "E2E: Critical Failure",
                "FAIL",
                str(e)
            )
            return False
    
    def print_summary(self):
        """Print test summary"""
        duration = time.time() - self.start_time
        
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
        
        print(f"Total Tests:     {self.results['total']}")
        print(f"{Colors.GREEN}Passed:          {self.results['passed']}{Colors.ENDC}")
        print(f"{Colors.YELLOW}Warnings:        {self.results['warnings']}{Colors.ENDC}")
        print(f"{Colors.RED}Failed:          {self.results['failed']}{Colors.ENDC}")
        print(f"Duration:        {duration:.2f}s")
        
        success_rate = (self.results['passed'] / self.results['total'] * 100) if self.results['total'] > 0 else 0
        
        print(f"\n{Colors.BOLD}Success Rate:    {success_rate:.1f}%{Colors.ENDC}")
        
        if self.results['failed'] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL CRITICAL TESTS PASSED! 🎉{Colors.ENDC}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED - REVIEW REQUIRED{Colors.ENDC}")
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.ENDC}\n")

async def main():
    """Main test execution"""
    runner = TestRunner()
    runner.start_time = time.time()
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   SOLANA SWARM INTELLIGENCE FRAMEWORK                     ║")
    print("║   Comprehensive Integration Test Suite                    ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Network: {os.getenv('SOLANA_NETWORK', 'devnet')}\n")
    
    # Run all tests
    tests = [
        ("Environment Configuration", runner.test_environment),
        ("Solana Connection", runner.test_solana_connection),
        ("Market Data", runner.test_market_data),
        ("Jupiter Integration", runner.test_jupiter_integration),
        ("DEX Integrations", runner.test_dex_integrations),
        ("Agent Loading", runner.test_agent_loading),
        ("Agent Evaluation", runner.test_agent_evaluation),
        ("Swarm Functionality", runner.test_swarm_functionality),
        ("Memory System", runner.test_memory_system),
        ("End-to-End Workflow", runner.test_end_to_end_workflow),
    ]
    
    for test_name, test_func in tests:
        try:
            await test_func()
        except Exception as e:
            runner.print_test(
                f"{test_name}: Unexpected Error",
                "FAIL",
                str(e)
            )
    
    # Print final summary
    runner.print_summary()
    
    # Return exit code
    return 0 if runner.results['failed'] == 0 else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Critical error: {e}{Colors.ENDC}")
        sys.exit(1)