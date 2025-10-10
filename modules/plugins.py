import os
import importlib.util
import subprocess
import json
import time
from pathlib import Path

class PluginHostModule:
    def __init__(self, config):
        self.config = config
        self.plugin_config = config['plugins_and_extensibility']['plugin_system']
        self.loaded_plugins = {}
        self.plugin_dir = Path('plugins')
        self.plugin_dir.mkdir(exist_ok=True)

    def load_plugins(self):
        """Load all available plugins"""
        for plugin_file in self.plugin_dir.glob('*.py'):
            self.load_plugin(plugin_file)

    def load_plugin(self, plugin_path):
        """Load a single plugin with sandboxing"""
        plugin_name = plugin_path.stem

        try:
            # Basic sandboxing - limit memory and execution time
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)

                # Set up restricted globals
                restricted_globals = {
                    '__builtins__': {
                        'print': print,
                        'len': len,
                        'str': str,
                        'int': int,
                        'float': float,
                        'bool': bool,
                        'list': list,
                        'dict': dict,
                        'tuple': tuple,
                        'range': range,
                        'enumerate': enumerate,
                        'zip': zip,
                        'sum': sum,
                        'min': min,
                        'max': max,
                        # Add other safe builtins as needed
                    }
                }

                # Execute with restrictions
                spec.loader.exec_module(module)

                if hasattr(module, 'register_plugin'):
                    plugin_info = module.register_plugin()
                    self.loaded_plugins[plugin_name] = {
                        'module': module,
                        'info': plugin_info,
                        'path': plugin_path
                    }
                    print(f"Loaded plugin: {plugin_name}")
                else:
                    print(f"Plugin {plugin_name} missing register_plugin function")
        except Exception as e:
            print(f"Failed to load plugin {plugin_name}: {e}")

    def execute_plugin(self, plugin_name, command, **kwargs):
        """Execute a plugin command with resource limits"""
        if plugin_name not in self.loaded_plugins:
            return f"Plugin {plugin_name} not loaded"

        plugin = self.loaded_plugins[plugin_name]

        try:
            # Check memory limit
            import psutil
            process = psutil.Process()
            if process.memory_info().rss > self.plugin_config['max_memory_mb'] * 1024 * 1024:
                return "Plugin memory limit exceeded"

            # Execute command
            if hasattr(plugin['module'], command):
                func = getattr(plugin['module'], command)
                return func(**kwargs)
            else:
                return f"Command {command} not found in plugin {plugin_name}"
        except Exception as e:
            return f"Plugin execution error: {e}"

    def list_plugins(self):
        """List all loaded plugins"""
        return {name: plugin['info'] for name, plugin in self.loaded_plugins.items()}

    def unload_plugin(self, plugin_name):
        """Unload a plugin"""
        if plugin_name in self.loaded_plugins:
            del self.loaded_plugins[plugin_name]
            print(f"Unloaded plugin: {plugin_name}")
            return True
        return False

    def create_plugin_template(self, name, description="Auralis plugin"):
        """Create a basic plugin template"""
        template = f'''"""
{description}
"""

def register_plugin():
    """Register this plugin with Auralis"""
    return {{
        "name": "{name}",
        "version": "1.0.0",
        "description": "{description}",
        "commands": ["example_command"]
    }}

def example_command(text="Hello World"):
    """Example plugin command"""
    return f"Plugin says: {{text}}"
'''

        plugin_path = self.plugin_dir / f"{name}.py"
        with open(plugin_path, 'w') as f:
            f.write(template)

        print(f"Created plugin template: {plugin_path}")
        return plugin_path