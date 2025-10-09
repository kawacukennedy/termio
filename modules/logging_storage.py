import os
import gzip
import json
from datetime import datetime, timedelta

class LoggingAndStorage:
    def __init__(self, log_file='logs/conversations.json.gz', max_size_mb=1, max_age_days=7):
        self.log_file = log_file
        self.max_size = max_size_mb * 1024 * 1024  # bytes
        self.max_age = timedelta(days=max_age_days)
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.logs = self.load_logs()
        self.rotate_if_needed()

    def load_logs(self):
        if os.path.exists(self.log_file):
            with gzip.open(self.log_file, 'rt') as f:
                return json.load(f)
        return []

    def log_interaction(self, user_input, response):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "response": response
        }
        self.logs.append(entry)
        self.rotate_if_needed()
        with gzip.open(self.log_file, 'wt') as f:
            json.dump(self.logs, f)

    def rotate_if_needed(self):
        # Check size
        if os.path.exists(self.log_file) and os.path.getsize(self.log_file) > self.max_size:
            self.rotate_logs()
        # Check age
        if self.logs:
            oldest = datetime.fromisoformat(self.logs[0]['timestamp'])
            if datetime.now() - oldest > self.max_age:
                self.rotate_logs()

    def rotate_logs(self):
        # Simple rotation: keep last 50% or something, but for now, clear old
        cutoff = len(self.logs) // 2
        self.logs = self.logs[-cutoff:]

    def clear_logs(self):
        self.logs = []
        if os.path.exists(self.log_file):
            os.remove(self.log_file)