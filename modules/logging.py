import json
import os
import gzip
import time
from pathlib import Path

class LoggingModule:
    def __init__(self, config):
        self.config = config
        self.log_config = config['logging_and_storage']['conversation_logs']
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = self.log_dir / 'conversation.jsonl'
        self.max_size = self.log_config['rotation_policy'].split()[0]  # e.g., "1MB" -> "1"
        self.max_size_bytes = self._parse_size(self.max_size)

    def _parse_size(self, size_str):
        """Parse size string like '1MB' to bytes"""
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        return int(size_str)

    def log(self, message):
        """Log message with rotation and compression"""
        # Check if rotation needed
        if self.current_log_file.exists() and self.current_log_file.stat().st_size >= self.max_size_bytes:
            self._rotate_logs()

        # Log to JSONL
        with open(self.current_log_file, 'a') as f:
            f.write(json.dumps(message) + '\n')

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