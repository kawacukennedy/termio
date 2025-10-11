import json
import os
from pathlib import Path

class SettingsModule:
    def __init__(self, config):
        self.config = config
        self.settings_file = Path('user_settings.json')
        self.user_settings = self._load_settings()

    def _load_settings(self):
        """Load user settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_settings(self):
        """Save user settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.user_settings, f, indent=2)

    def get_setting(self, key, default=None):
        """Get setting from user settings or config"""
        # First check user settings
        keys = key.split('.')
        value = self.user_settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, None)
            else:
                value = None
                break

        if value is not None:
            return value

        # Fall back to config
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default

        return value

    def set_setting(self, key, value):
        """Set a user setting"""
        keys = key.split('.')
        current = self.user_settings

        # Navigate to the parent of the final key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the value
        current[keys[-1]] = value
        self._save_settings()
        return True

    def reset_setting(self, key):
        """Reset a setting to default (remove from user settings)"""
        keys = key.split('.')
        current = self.user_settings

        # Navigate to the parent
        for k in keys[:-1]:
            if k in current:
                current = current[k]
            else:
                return False

        # Remove the key
        if keys[-1] in current:
            del current[keys[-1]]
            self._save_settings()
            return True
        return False

    def list_settings(self, prefix=None):
        """List all settings with optional prefix"""
        settings = {}

        # Get config settings
        def flatten_dict(d, prefix=''):
            for k, v in d.items():
                key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    flatten_dict(v, key)
                else:
                    settings[key] = v

        flatten_dict(self.config)

        # Override with user settings
        flatten_dict(self.user_settings)

        # Filter by prefix if provided
        if prefix:
            filtered = {k: v for k, v in settings.items() if k.startswith(prefix)}
            return filtered

        return settings

    def export_settings(self):
        """Export all settings"""
        return {
            'config': self.config,
            'user_settings': self.user_settings
        }

    def import_settings(self, settings_data):
        """Import user settings"""
        if 'user_settings' in settings_data:
            self.user_settings = settings_data['user_settings']
            self._save_settings()
            return True
        return False