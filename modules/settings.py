import json

class Settings:
    def __init__(self, config_file='../config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)

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
        with open('../config.json', 'w') as f:
            json.dump(self.config, f, indent=2)