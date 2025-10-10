import json
import os

class Settings:
    def __init__(self):
        self.user_config_dir = os.path.expanduser('~/.auralis')
        self.user_config_file = os.path.join(self.user_config_dir, 'config.json')
        self.default_config_file = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        
        # Load defaults
        with open(self.default_config_file, 'r') as f:
            self.defaults = json.load(f)
        
        # Load or create user config
        if os.path.exists(self.user_config_file):
            with open(self.user_config_file, 'r') as f:
                self.config = json.load(f)
        else:
            os.makedirs(self.user_config_dir, exist_ok=True)
            self.config = self.defaults.get('settings_and_persistence', {}).get('default_settings', {})
            self.save()

    def get(self, key, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key, value):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
        self.save()

    def save(self):
        with open(self.user_config_file, 'w') as f:
            json.dump(self.config, f, indent=2)