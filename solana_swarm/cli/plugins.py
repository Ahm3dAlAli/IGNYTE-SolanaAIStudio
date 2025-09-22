"""
Plugin Management CLI for Solana Swarm Intelligence
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from rich import print as rprint
from rich.table import Table
from rich.console import Console

from solana_swarm.plugins.loader import PluginLoader

console = Console()

async def manage_plugins(action: str, name: Optional[str] = None):
    """Manage plugins for Solana Swarm"""
    
    if action == "list":
        await list_plugins()
    elif action == "install" and name:
        await install_plugin(name)
    elif action == "remove" and name:
        await remove_plugin(name)
    elif action == "info" and name:
        await show_plugin_info(name)
    else:
        rprint("❌ [red]Invalid action or missing plugin name[/red]")
        rprint("Available actions: list, install, remove, info")

async def list_plugins():
    """List all available and loaded plugins"""
    
    # Show available plugins
    available_plugins = scan_available_plugins()
    
    table = Table(title="Available Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Role", style="dim")
    table.add_column("Location")
    
    loader = PluginLoader()
    loaded_plugins = loader.list_loaded_plugins()
    
    for plugin_name, info in available_plugins.items():
        status = "✅ Loaded" if plugin_name in loaded_plugins else "📦 Available"
        table.add_row(plugin_name, status, info["role"], info["path"])
    
    console.print(table)
    
    # Show loaded plugin details
    if loaded_plugins:
        rprint("\n🤖 [cyan]Loaded Plugins:[/cyan]")
        for name, plugin in loaded_plugins.items():
            role = getattr(plugin, "role", "unknown")
            capabilities = getattr(plugin, "capabilities", [])
            rprint(f"  • **{name}** ({role}) - {', '.join(capabilities)}")

def scan_available_plugins() -> dict:
    """Scan for available plugins in the system"""
    plugins = {}
    
    # Scan agent directories
    agent_dirs = [
        "solana_swarm/agents",
        "plugins"
    ]
    
    for base_dir in agent_dirs:
        if os.path.exists(base_dir):
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if os.path.isdir(item_path):
                    plugin_file = os.path.join(item_path, "plugin.py")
                    config_file = os.path.join(item_path, "agent.yaml")
                    
                    if os.path.exists(plugin_file):
                        role = "unknown"
                        if os.path.exists(config_file):
                            try:
                                import yaml
                                with open(config_file, 'r') as f:
                                    config = yaml.safe_load(f)
                                    role = config.get("role", "unknown")
                            except:
                                pass
                        
                        plugins[item] = {
                            "role": role,
                            "path": item_path,
                            "has_config": os.path.exists(config_file)
                        }
    
    return plugins

async def install_plugin(name: str):
    """Install a plugin from template or repository"""
    try:
        # For now, create from template
        rprint(f"🔧 [cyan]Installing plugin: {name}[/cyan]")
        
        # Create plugin directory
        plugin_dir = Path(f"plugins/{name}")
        plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy template files
        template_dir = Path("solana_swarm/templates/plugin_template")
        if template_dir.exists():
            for template_file in template_dir.glob("*"):
                if template_file.is_file():
                    content = template_file.read_text()
                    # Replace template variables
                    content = content.replace("{{plugin_name}}", name)
                    content = content.replace("{{plugin_role}}", name.replace("-", "_"))
                    content = content.replace("{{plugin_description}}", f"Custom {name} plugin")
                    content = content.replace("{{primary_capability}}", "analysis")
                    content = content.replace("{{plugin_class_name}}", f"{name.title().replace('-', '')}Plugin")
                    
                    dest_file = plugin_dir / template_file.name
                    dest_file.write_text(content)
        
        rprint(f"✅ [green]Plugin {name} installed successfully![/green]")
        rprint(f"📁 Location: {plugin_dir}")
        rprint("🔧 Next steps:")
        rprint(f"   1. Edit {plugin_dir}/plugin.py")
        rprint(f"   2. Configure {plugin_dir}/agent.yaml")
        rprint(f"   3. Test with: solana-swarm plugins info {name}")
        
    except Exception as e:
        rprint(f"❌ [red]Failed to install plugin {name}: {e}[/red]")

async def remove_plugin(name: str):
    """Remove a plugin"""
    try:
        plugin_paths = [
            Path(f"plugins/{name}"),
            Path(f"solana_swarm/agents/{name}")
        ]
        
        removed = False
        for plugin_path in plugin_paths:
            if plugin_path.exists():
                shutil.rmtree(plugin_path)
                rprint(f"✅ [green]Removed plugin: {plugin_path}[/green]")
                removed = True
        
        if not removed:
            rprint(f"⚠️ [yellow]Plugin {name} not found[/yellow]")
        
    except Exception as e:
        rprint(f"❌ [red]Failed to remove plugin {name}: {e}[/red]")

async def show_plugin_info(name: str):
    """Show detailed plugin information"""
    try:
        # Try to load plugin
        loader = PluginLoader()
        plugin = await loader.load_plugin(name)
        
        info_table = Table(title=f"Plugin Information: {name}")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="bold")
        
        info_table.add_row("Name", plugin.name)
        info_table.add_row("Role", plugin.role)
        info_table.add_row("Capabilities", ", ".join(plugin.capabilities))
        info_table.add_row("Status", "✅ Loaded" if plugin._is_initialized else "❌ Not Initialized")
        
        console.print(info_table)
        
        # Show configuration
        if hasattr(plugin, "plugin_config"):
            config = plugin.plugin_config
            rprint(f"\n⚙️ [cyan]Configuration:[/cyan]")
            for key, value in config.custom_settings.items():
                rprint(f"  • {key}: {value}")
        
    except Exception as e:
        rprint(f"❌ [red]Failed to get plugin info for {name}: {e}[/red]")
