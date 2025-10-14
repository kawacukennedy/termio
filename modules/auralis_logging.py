import json
import os
import gzip
import time
import re
from pathlib import Path
from cryptography.fernet import Fernet

class LoggingModule:
    def __init__(self, config):
        self.config = config
        self.log_config = config['logging_and_storage']['conversation_logs']
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = self.log_dir / 'conversation.jsonl'
        self.audit_log_file = self.log_dir / 'audit.jsonl'
        self.max_size = self.log_config['rotation_policy'].split()[0]  # e.g., "1MB" -> "1"
        self.max_size_bytes = self._parse_size(self.max_size)

        # Audit encryption
        self.audit_key = self._load_or_generate_audit_key()
        self.audit_cipher = Fernet(self.audit_key)

    def _load_or_generate_audit_key(self):
        key_file = 'audit_key.key'
        if os.path.exists(key_file) and os.path.getsize(key_file) > 0:
            with open(key_file, 'rb') as f:
                key = f.read()
                try:
                    Fernet(key)
                    return key
                except:
                    pass
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

    def _parse_size(self, size_str):
        """Parse size string like '1MB' to bytes"""
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        return int(size_str)

    def _redact_pii(self, text):
        """Redact potential PII from text"""
        # Simple patterns for email, phone, SSN, etc.
        patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
            (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
            (r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]'),
            (r'\b\d{4} \d{4} \d{4} \d{4}\b', '[CARD]'),
        ]
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        return text

    def log(self, message):
        """Log message with rotation and compression"""
        # Redact PII
        if 'text' in message:
            message['text'] = self._redact_pii(message['text'])

        # Check if rotation needed
        if self.current_log_file.exists() and self.current_log_file.stat().st_size >= self.max_size_bytes:
            self._rotate_logs()

        # Log to JSONL
        with open(self.current_log_file, 'a') as f:
            f.write(json.dumps(message) + '\n')

    def audit_log(self, action, details):
        """Append-only encrypted audit log"""
        entry = {
            'timestamp': time.time(),
            'action': action,
            'details': details
        }
        encrypted_entry = self.audit_cipher.encrypt(json.dumps(entry).encode())
        with open(self.audit_log_file, 'ab') as f:
            f.write(encrypted_entry + b'\n')

    def _rotate_logs(self):
        """Compress old logs and create new log file"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        compressed_file = self.log_dir / f'conversation_{timestamp}.jsonl.gz'

        # Compress current log
        with open(self.current_log_file, 'rb') as f_in:
            with gzip.open(compressed_file, 'wb') as f_out:
                f_out.writelines(f_in)

        # Clear current log
        self.current_log_file.unlink()
        self.current_log_file.touch()

        # Clean up old compressed logs (keep last 7 days)
        self._cleanup_old_logs()

    def _cleanup_old_logs(self):
        """Remove logs older than retention period"""
        retention_days = 7  # From config
        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)

        for log_file in self.log_dir.glob('conversation_*.jsonl.gz'):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()