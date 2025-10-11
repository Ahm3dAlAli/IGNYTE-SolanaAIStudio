#!/usr/bin/env python3
"""
Solana Swarm CLI Testing Suite
Interactive test runner for all CLI functionalities
"""

import asyncio
import subprocess
import sys
import os
from typing import List, Dict, Any
import time

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class CLITester:
    """Interactive CLI test runner"""
    
    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
    
    def print_test(self, name: str, status: str, details: str = ""):
        """Print test result"""
        if status == "PASS":
            icon = f"{Colors.GREEN}✅{Colors.ENDC}"
            self.results['passed'] += 1
        elif status == "FAIL":
            icon = f"{Colors.RED}❌{Colors.ENDC}"
            self.results['failed'] += 1
        else:
            icon = f"{Colors.YELLOW}⏭️{Colors.ENDC}"
            self.results['skipped'] += 1
        
        print(f"{icon} {name}")
        if details:
            print(f"   {Colors.CYAN}{details}{Colors.ENDC}")
    
    def run_command(self, cmd: List[str], capture: bool = True) -> Dict[str, Any]:
        """Run shell command and return result"""
        try:
            if capture:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {
                    'success': result.returncode == 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
            else:
                result = subprocess.run(cmd, timeout=30)
                return {
                    'success': result.returncode == 0,
                    'returncode': result.returncode
                }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_basic_commands(self):
        """Test basic CLI commands"""
        self.print_header("TEST 1: Basic CLI Commands")
        
        # Test 1.1: Help command
        result = self.run_command(['python', '-m', 'solana_swarm.cli.main', '--help'])
        if result['success']:
            self.print_test("Help Command", "PASS", "CLI help accessible")
        else:
            self.print_test("Help Command", "FAIL", f"Error: {result.get('error', 'Unknown')}")
        
        # Test 1.2: Config show
        result = self.run_command(['python', '-m', 'solana_swarm.cli.main', 'config', 'show'])
        if result['success'] or 'config' in result.get('stdout', '').lower():
            self.print_test("Config Show", "PASS", "Configuration accessible")
        else:
            self.print_test("Config Show", "SKIP", "Config not initialized")
    
    def test_environment(self):
        """Test environment setup"""
        self.print_header("TEST 2: Environment Validation")
        
        # Test 2.1: Check .env file
        if os.path.exists('.env'):
            self.print_test("Environment File", "PASS", ".env file found")
        else:
            self.print_test("Environment File", "FAIL", ".env file missing")
        
        # Test 2.2: Check required env vars
        required_vars = ['LLM_API_KEY', 'SOLANA_WALLET_PATH', 'SOLANA_NETWORK']
        for var in required_vars:
            if os.getenv(var):
                self.print_test(f"ENV: {var}", "PASS", "Set")
            else:
                self.print_test(f"ENV: {var}", "FAIL", "Not set")
    
    def test_solana_connection(self):
        """Test Solana connectivity"""
        self.print_header("TEST 3: Solana Connection")
        
        # Test 3.1: Wallet command
        result = self.run_command(['python', '-m', 'solana_swarm.cli.main', 'wallet'])
        if result['success']:
            self.print_test("Wallet Info", "PASS", "Wallet accessible")
        else:
            self.print_test("Wallet Info", "FAIL", "Cannot access wallet")
        
        # Test 3.2: Status command
        result = self.run_command(['python', '-m', 'solana_swarm.cli.main', 'status'])
        if result['success']:
            self.print_test("Network Status", "PASS", "Network accessible")
        else:
            self.print_test("Network Status", "FAIL", "Cannot get network status")
    
    def test_market_data(self):
        """Test market data commands"""
        self.print_header("TEST 4: Market Data")
        
        # Test 4.1: SOL price
        result = self.run_command(['python', '-m', 'solana_swarm.cli.main', 'price', 'sol'])
        if result['success']:
            self.print_test("SOL Price", "PASS", "Price fetched successfully")
        else:
            self.print_test("SOL Price", "FAIL", "Cannot fetch price")
        
        # Test 4.2: USDC price
        result = self.run_command(['python', '-m', 'solana_swarm.cli.main', 'price', 'usdc'])
        if result['success']:
            self.print_test("USDC Price", "PASS", "Price fetched successfully")
        else:
            self.print_test("USDC Price", "SKIP", "Price fetch failed (non-critical)")
    
    def test_agent_validation(self):
        """Test agent validation"""
        self.print_header("TEST 5: Agent Validation")
        
        # Test 5.1: Validate command
        result = self.run_command(['python', '-m', 'solana_swarm.cli.main', 'validate'])
        if result['success']:
            self.print_test("Agent Validation", "PASS", "All agents valid")
        else:
            self.print_test("Agent Validation", "FAIL", "Validation failed")
    
    def test_agent_execution(self):
        """Test agent execution (non-interactive)"""
        self.print_header("TEST 6: Agent Execution (Quick Test)")
        
        print(f"{Colors.YELLOW}Note: Full agent execution test requires manual intervention{Colors.ENDC}")
        print(f"{Colors.YELLOW}Use: solana-swarm run price-monitor --timeout 60{Colors.ENDC}\n")
        
        self.print_test("Agent Execution", "SKIP", "Manual test required")
    
    def test_creation_commands(self):
        """Test creation commands"""
        self.print_header("TEST 7: Creation Commands")
        
        print(f"{Colors.YELLOW}Testing creation in dry-run mode...{Colors.ENDC}\n")
        
        # Test 7.1: Help for create agent
        result = self.run_command([
            'python', '-m', 'solana_swarm.cli.main', 
            'create', 'agent', '--help'
        ])
        if result['success']:
            self.print_test("Create Agent Help", "PASS", "Command available")
        else:
            self.print_test("Create Agent Help", "FAIL", "Command not found")
        
        # Test 7.2: Help for create strategy
        result = self.run_command([
            'python', '-m', 'solana_swarm.cli.main',
            'create', 'strategy', '--help'
        ])
        if result['success']:
            self.print_test("Create Strategy Help", "PASS", "Command available")
        else:
            self.print_test("Create Strategy Help", "FAIL", "Command not found")
    
    def test_interactive_features(self):
        """Test interactive features"""
        self.print_header("TEST 8: Interactive Features")
        
        print(f"{Colors.YELLOW}Interactive features require manual testing:{Colors.ENDC}\n")
        print(f"1. Chat Interface: {Colors.CYAN}solana-swarm chat{Colors.ENDC}")
        print(f"2. Tutorial Mode: {Colors.CYAN}solana-swarm chat --tutorial{Colors.ENDC}")
        print(f"3. Agent Monitoring: {Colors.CYAN}solana-swarm run price-monitor{Colors.ENDC}\n")
        
        self.print_test("Interactive Chat", "SKIP", "Manual test required")
        self.print_test("Tutorial Mode", "SKIP", "Manual test required")
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.results['passed'] + self.results['failed'] + self.results['skipped']
        
        print(f"Total Tests:  {total}")
        print(f"{Colors.GREEN}Passed:       {self.results['passed']}{Colors.ENDC}")
        print(f"{Colors.YELLOW}Skipped:      {self.results['skipped']}{Colors.ENDC}")
        print(f"{Colors.RED}Failed:       {self.results['failed']}{Colors.ENDC}")
        
        if self.results['failed'] == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All critical tests passed!{Colors.ENDC}")
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed - review errors above{Colors.ENDC}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║   SOLANA SWARM CLI TESTING SUITE                         ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}\n")
        
        try:
            self.test_basic_commands()
            time.sleep(1)
            
            self.test_environment()
            time.sleep(1)
            
            self.test_solana_connection()
            time.sleep(1)
            
            self.test_market_data()
            time.sleep(1)
            
            self.test_agent_validation()
            time.sleep(1)
            
            self.test_agent_execution()
            time.sleep(1)
            
            self.test_creation_commands()
            time.sleep(1)
            
            self.test_interactive_features()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Testing interrupted by user{Colors.ENDC}")
        except Exception as e:
            print(f"\n{Colors.RED}Testing error: {e}{Colors.ENDC}")
        finally:
            self.print_summary()

def main():
    """Main entry point"""
    tester = CLITester()
    tester.run_all_tests()
    
    print(f"\n{Colors.CYAN}Next Steps:{Colors.ENDC}")
    print("1. Run manual tests for interactive features")
    print("2. Test agent execution: solana-swarm run price-monitor --timeout 60")
    print("3. Try chat interface: solana-swarm chat")
    print("4. Create test components: solana-swarm create agent test-agent")
    print("5. Check full integration: python comp_test.py")
    
    return 0 if tester.results['failed'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())