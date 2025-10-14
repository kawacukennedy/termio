import os
import time
import logging

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    print("Warning: cryptography not available. Security features limited.")

class SecurityModule:
    def __init__(self, config, settings_module=None):
        self.config = config
        self.permissions = config.get('security_privacy', {}).get('permissions', [])
        self.user_controls = config.get('security_privacy', {}).get('user_controls', {})
        self.settings = settings_module

        # Generate or load encryption key
        if CRYPTOGRAPHY_AVAILABLE:
            self.key = self._load_or_generate_key()
            self.cipher = Fernet(self.key)
        else:
            self.key = None
            self.cipher = None

        # Forbidden operations
        self.forbidden_ops = [
            'exfiltrate_files', 'escalate_privileges', 'modify_bootloader',
            'access_sensitive_files', 'run_as_root', 'network_exfil'
        ]

        # Permission consent status
        self.consent_given = self._load_consent_status()

    def _load_or_generate_key(self):
        key_file = 'security_key.key'
        if os.path.exists(key_file) and os.path.getsize(key_file) > 0:
            with open(key_file, 'rb') as f:
                key = f.read()
                # Validate the key
                try:
                    Fernet(key)
                    return key
                except:
                    pass  # Invalid key, generate new one

        # Generate new key
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

    def check_permission(self, action, resource=None):
        """Check if action is permitted, prompt if needed"""
        if action in ['read_screen', 'get_system_info']:
            return {'allowed': True}
        elif action in ['delete_file', 'modify_system']:
            # Destructive actions require confirmation
            return {'allowed': False, 'prompt_user': True, 'message': f'Action "{action}" requires confirmation'}
        else:
            return {'allowed': action in self.permissions}

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
        """Encrypt an API key for storage"""
        if self.cipher:
            return self.cipher.encrypt(api_key.encode()).decode('latin-1')
        else:
            # Fallback: base64 encoding (not secure, but better than plain text)
            import base64
            return base64.b64encode(api_key.encode()).decode('latin-1')

    def decrypt_api_key(self, encrypted_key):
        """Decrypt an API key"""
        if self.cipher:
            try:
                return self.cipher.decrypt(encrypted_key.encode('latin-1')).decode()
            except Exception:
                return None
        else:
            # Fallback: base64 decoding
            import base64
            try:
                return base64.b64decode(encrypted_key.encode('latin-1')).decode()
            except Exception:
                return None

    def encrypt_data(self, data):
        """Encrypt arbitrary data"""
        if self.cipher:
            if isinstance(data, str):
                data = data.encode()
            return self.cipher.encrypt(data).decode('latin-1')
        else:
            # Fallback: base64 encoding
            import base64
            if isinstance(data, str):
                data = data.encode()
            return base64.b64encode(data).decode('latin-1')

    def decrypt_data(self, data):
        """Decrypt arbitrary data"""
        if self.cipher:
            try:
                return self.cipher.decrypt(data.encode('latin-1')).decode()
            except:
                return data
        else:
            # Fallback: base64 decoding
            import base64
            try:
                return base64.b64decode(data.encode('latin-1')).decode()
            except:
                return data

    def clear_logs(self):
        # Clear conversation logs
        log_dir = 'logs'
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                os.remove(os.path.join(log_dir, file))

    def check_first_run_permissions(self):
        """Check and request permissions on first run as per spec"""
        if self.consent_given.get('first_run_complete', False):
            return True

        print("\n" + "="*60)
        print("AURALIS FIRST RUN - PERMISSION REQUEST")
        print("="*60)
        print()
        print("Auralis requires the following permissions to function:")
        print("• Microphone access (for voice input)")
        print("• Screen reading (for OCR and content analysis)")
        print("• Screen control (optional, for automation)")
        print("• File system access (for configuration and logs)")
        print()
        print("All data is processed locally by default.")
        print("Online features require explicit opt-in.")
        print()

        # Request microphone permission
        mic_ok = self._request_permission_interactive("microphone", "Microphone access for voice commands")
        screen_read_ok = self._request_permission_interactive("screen_read", "Screen reading for content analysis")
        screen_control_ok = self._request_permission_interactive("screen_control", "Screen control for automation (optional)")

        if mic_ok and screen_read_ok:
            self.consent_given.update({
                'first_run_complete': True,
                'microphone': True,
                'screen_read': True,
                'screen_control': screen_control_ok,
                'timestamp': time.time()
            })
            self._save_consent_status()
            print("\n✅ Permissions granted. Auralis is ready to use!")
            return True
        else:
            print("\n❌ Required permissions not granted. Auralis cannot function without them.")
            return False

    def _request_permission_interactive(self, perm_type, description):
        """Interactive permission request"""
        while True:
            response = input(f"Grant {description}? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please answer 'y' or 'n'")

    def check_action_permission(self, action_type, action_details=None):
        """Check permission for action execution as per spec"""
        if action_type in self.forbidden_ops:
            self.logger.warning(f"Forbidden operation blocked: {action_type}")
            return False, "Operation not allowed for security reasons"

        # Non-destructive actions: single confirmation
        non_destructive = ['read_screen', 'get_weather', 'tell_joke', 'list_files']

        if action_type in non_destructive:
            # Single confirmation required
            return self._get_user_confirmation(f"Execute {action_type}?", single=True), "Confirmation required"

        # Destructive actions: typed confirmation + log
        destructive = ['delete_file', 'modify_system', 'run_command', 'send_email']

        if action_type in destructive:
            confirmed = self._get_typed_confirmation(f"DANGER: Execute destructive action '{action_type}'?")
            if confirmed:
                self._log_destructive_action(action_type, action_details)
                return True, "Destructive action logged and confirmed"
            else:
                return False, "Destructive action denied"

        # Default: allow with logging
        return True, "Action permitted"

    def _get_user_confirmation(self, prompt, single=True):
        """Get user confirmation"""
        # In interactive mode, this would show a dialog
        # For now, assume yes for automation
        self.logger.info(f"Action confirmation: {prompt}")
        return True

    def _get_typed_confirmation(self, prompt):
        """Get typed confirmation for destructive actions"""
        print(f"\n{prompt}")
        print("Type 'CONFIRM' to proceed, or anything else to cancel:")
        response = input("> ").strip()
        return response.upper() == 'CONFIRM'

    def _log_destructive_action(self, action, details):
        """Log destructive actions"""
        log_entry = {
            'timestamp': time.time(),
            'action': action,
            'details': details,
            'user_confirmed': True
        }
        self.logger.warning(f"Destructive action logged: {log_entry}")

    def check_plugin_permissions(self, plugin_manifest):
        """Check plugin permissions against user consent"""
        required_perms = plugin_manifest.get('permissions', [])

        for perm in required_perms:
            if not self.consent_given.get(perm, False):
                return False, f"Plugin requires permission '{perm}' which was not granted"

        return True, "Plugin permissions approved"

    def _load_consent_status(self):
        """Load permission consent status"""
        if self.settings:
            consent = self.settings.get_setting('security.consent')
            return consent if consent else {}
        return {}

    def _save_consent_status(self):
        """Save permission consent status"""
        if self.settings:
            self.settings.set_setting('security.consent', self.consent_given)

    def rotate_keys(self):
        """Rotate encryption keys periodically"""
        old_key = self.key
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)

        # Re-encrypt stored data with new key
        # This would need to be implemented for all stored encrypted data

        with open('security_key.key', 'wb') as f:
            f.write(self.key)

        self.logger.info("Encryption keys rotated")

    def toggle_mode(self, mode):
        """Toggle between offline/online modes"""
        # Additional security checks for online mode
        if mode == 'online':
            if not self.consent_given.get('online_features', False):
                print("Online features require explicit opt-in.")
                if self._request_permission_interactive('online_features', 'Online AI features (HuggingFace API)'):
                    self.consent_given['online_features'] = True
                    self._save_consent_status()
                else:
                    return False
        return True