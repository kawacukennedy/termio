import os
from cryptography.fernet import Fernet

class SecurityModule:
    def __init__(self, config, settings_module=None):
        self.config = config
        self.permissions = config['security_privacy']['permissions']
        self.user_controls = config['security_privacy']['user_controls']
        self.settings = settings_module

        # Initialize encryption
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self):
        key_file = 'security_key.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def check_permission(self, perm):
        return perm in self.permissions

    def request_microphone_permission(self):
        # In a real implementation, check system permissions
        return True

    def request_screen_permission(self):
        # Check if screen control is allowed
        return 'keyboard/mouse optional' in self.permissions

    def sanitize_input(self, text):
        # Basic sanitization
        return text.strip()

    def encrypt_api_key(self, api_key):
        """Encrypt API key for storage"""
        if not api_key:
            return ""
        return self.cipher.encrypt(api_key.encode()).decode('latin-1')

    def decrypt_api_key(self, encrypted_key):
        """Decrypt API key for use"""
        if not encrypted_key:
            return ""
        try:
            return self.cipher.decrypt(encrypted_key.encode('latin-1')).decode()
        except:
            return ""

    def store_api_key(self, service, api_key):
        """Securely store API key"""
        encrypted = self.encrypt_api_key(api_key)
        # Store in settings or secure location
        settings.set_setting(f"api_keys.{service}", encrypted)
        return f"API key for {service} stored securely"

    def get_api_key(self, service):
        """Retrieve and decrypt API key"""
        encrypted = settings.get_setting(f"api_keys.{service}")
        if encrypted:
            return self.decrypt_api_key(encrypted)
        return None

    def encrypt_data(self, data):
        """Encrypt arbitrary data"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode('latin-1')

    def decrypt_data(self, data):
        """Decrypt arbitrary data"""
        try:
            return self.cipher.decrypt(data.encode('latin-1')).decode()
        except:
            return data

    def clear_logs(self):
        # Clear conversation logs
        log_dir = 'logs'
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                os.remove(os.path.join(log_dir, file))

    def toggle_mode(self, mode):
        # Toggle between offline/online
        pass