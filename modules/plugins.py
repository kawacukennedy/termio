import os
import importlib.util
import subprocess
import sys

class PluginModule:
    def __init__(self, screen_reader=None, screen_control=None, tts=None):
        self.plugins = {}
        self.plugin_dir = os.path.expanduser('~/.auralis/plugins')
        os.makedirs(self.plugin_dir, exist_ok=True)
        self.screen_reader = screen_reader
        self.screen_control = screen_control
        self.tts = tts

    def load_plugins(self):
        if os.path.exists(self.plugin_dir):
            for file in os.listdir(self.plugin_dir):
                if file.endswith('.py') and os.path.getsize(os.path.join(self.plugin_dir, file)) <= 1024 * 1024:  # 1MB limit
                    name = file[:-3]
                    spec = importlib.util.spec_from_file_location(name, os.path.join(self.plugin_dir, file))
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        self.plugins[name] = module

    def execute(self, name, *args):
        if name in self.plugins and hasattr(self.plugins[name], 'run'):
            env = {
                'send_text': lambda text: print(text),  # Placeholder, should be connected to main loop
                'read_screen_text': self.screen_reader.read_screen_area if self.screen_reader else None,
                'perform_action': lambda action: self._perform_action(action)
            }
            # Run in subprocess for security
            try:
                result = subprocess.run([sys.executable, '-c', f'import {name}; print({name}.run({env}, {args}))'], capture_output=True, text=True, timeout=10)
                return result.stdout.strip()
            except subprocess.TimeoutExpired:
                return "Plugin execution timed out"
            except Exception as e:
                return f"Plugin error: {e}"
        return "Plugin not found or no run function"

    def _perform_action(self, action):
        # Placeholder for confirmation
        print(f"Confirm action: {action} (Y/N)")
        # In real, get user input
        return "Action requires confirmation"

    def list_plugins(self):
        return list(self.plugins.keys())