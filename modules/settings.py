class SettingsModule:
    def __init__(self, config):
        self.config = config

    def get_setting(self, key):
        # Get setting from config
        keys = key.split('.')
        value = self.config
        for k in keys:
            value = value.get(k, {})
        return value