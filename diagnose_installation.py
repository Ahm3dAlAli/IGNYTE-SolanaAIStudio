#!/usr/bin/env python3
"""
Diagnose Solana Swarm Installation
Checks what's working and what's not
"""

import sys
import os

def check_imports():
    """Check if core modules can be imported"""
    print("🔍 Checking Imports...")
    print("=" * 50)
    
    checks = {
        "solana_swarm": False,
        "solana_swarm.core": False,
        "solana_swarm.core.agent": False,
        "solana_swarm.core.swarm_agent": False,
        "solana_swarm.plugins": False,
        "solana_swarm.cli": False,
        "solana_swarm.cli.main": False,
    }
    
    for module_name in checks.keys():
        try:
            __import__(module_name)
            checks[module_name] = True
            print(f"✅ {module_name}")
        except Exception as e:
            print(f"❌ {module_name}: {e}")
    
    return all(checks.values())

def check_cli_entry_point():
    """Check if CLI entry point works"""
    print("\n🔍 Checking CLI Entry Point...")
    print("=" * 50)
    
    try:
        from solana_swarm.cli.main import cli
        print("✅ CLI module can be imported")
        
        # Try to get help
        from click.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        if result.exit_code == 0:
            print("✅ CLI --help works")
            print("\nCLI Help Output:")
            print(result.output[:500])
            return True
        else:
            print(f"❌ CLI --help failed with exit code {result.exit_code}")
            print(f"Error: {result.output}")
            return False
            
    except Exception as e:
        print(f"❌ CLI entry point check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_command_availability():
    """Check if solana-swarm command is available"""
    print("\n🔍 Checking Command Availability...")
    print("=" * 50)
    
    import subprocess
    
    # Check if command exists
    try:
        result = subprocess.run(
            ['which', 'solana-swarm'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ solana-swarm found at: {result.stdout.strip()}")
            return True
        else:
            print("❌ solana-swarm command not found in PATH")
            print("\n💡 Alternative: Use 'python -m solana_swarm.cli.main' instead")
            return False
    except Exception as e:
        print(f"❌ Error checking command: {e}")
        return False

def check_python_module():
    """Check if module can be run with python -m"""
    print("\n🔍 Checking Python Module Execution...")
    print("=" * 50)
    
    import subprocess
    
    try:
        result = subprocess.run(
            ['python', '-m', 'solana_swarm.cli.main', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ Can run with: python -m solana_swarm.cli.main")
            return True
        else:
            print("❌ Module execution failed")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running module: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("\n🔍 Checking Environment...")
    print("=" * 50)
    
    # Check if in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    print(f"Virtual Environment: {'✅ Active' if in_venv else '❌ Not Active'}")
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version}")
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("❌ .env file not found")
    
    return in_venv

def check_dependencies():
    """Check key dependencies"""
    print("\n🔍 Checking Key Dependencies...")
    print("=" * 50)
    
    dependencies = [
        'click',
        'rich',
        'pydantic',
        'aiohttp',
        'solana',
        'solders',
    ]
    
    all_good = True
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - NOT INSTALLED")
            all_good = False
    
    return all_good

def provide_fix_instructions(results):
    """Provide instructions based on what failed"""
    print("\n" + "=" * 50)
    print("📋 DIAGNOSIS SUMMARY")
    print("=" * 50)
    
    if all(results.values()):
        print("\n🎉 Everything looks good!")
        print("\n✨ You can use these commands:")
        print("   python -m solana_swarm.cli.main --help")
        print("   python -m solana_swarm.cli.main wallet")
        print("   python -m solana_swarm.cli.main chat")
        return
    
    print("\n⚠️  Issues Found. Here's how to fix them:\n")
    
    if not results['imports']:
        print("❌ Import Issues:")
        print("   Fix: pip uninstall solana-swarm && pip install -e .")
        print()
    
    if not results['cli']:
        print("❌ CLI Issues:")
        print("   The CLI module has import errors.")
        print("   Fix: Check solana_swarm/cli/main.py and plugins.py")
        print()
    
    if not results['command']:
        print("❌ Command Not Available:")
        print("   The 'solana-swarm' command is not in your PATH.")
        print("   Workaround: Use 'python -m solana_swarm.cli.main' instead")
        print()
        print("   To add the command to PATH:")
        print("   1. Add to ~/.zshrc or ~/.bashrc:")
        print("      alias solana-swarm='python -m solana_swarm.cli.main'")
        print("   2. Reload: source ~/.zshrc")
        print()
    
    if not results['module']:
        print("❌ Module Execution Failed:")
        print("   There are import or syntax errors.")
        print("   Check the error output above.")
        print()
    
    if not results['environment']:
        print("❌ Environment Issues:")
        print("   Make sure you're in the virtual environment:")
        print("   source venv/bin/activate")
        print()
    
    if not results['dependencies']:
        print("❌ Missing Dependencies:")
        print("   Fix: pip install -r requirements.txt")
        print()

def main():
    """Run all diagnostic checks"""
    print("\n🔧 Solana Swarm Installation Diagnostics")
    print("=" * 50)
    print()
    
    results = {
        'environment': check_environment(),
        'dependencies': check_dependencies(),
        'imports': check_imports(),
        'cli': check_cli_entry_point(),
        'module': check_python_module(),
        'command': check_command_availability(),
    }
    
    provide_fix_instructions(results)
    
    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    main()