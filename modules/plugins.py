import os
import importlib.util

class PluginModule:
    def __init__(self):
        self.plugins = {}

    def load_plugins(self):
        plugin_dir = 'plugins'
        if os.path.exists(plugin_dir):
            for file in os.listdir(plugin_dir):
                if file.endswith('.py'):
                    name = file[:-3]
                    spec = importlib.util.spec_from_file_location(name, os.path.join(plugin_dir, file))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        self.plugins[name] = module

    def execute(self, name, *args):
        if name in self.plugins and hasattr(self.plugins[name], 'run'):
            return self.plugins[name].run(*args)
        return "Plugin not found or no run function"

    def list_plugins(self):
        return list(self.plugins.keys())