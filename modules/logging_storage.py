import os
import gzip
import json
from datetime import datetime

class LoggingAndStorage:
    def __init__(self, log_file='logs/conversations.json.gz'):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.logs = self.load_logs()

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
        # Keep only last 100 or something, but for now all
        with gzip.open(self.log_file, 'wt') as f:
            json.dump(self.logs, f)

    def clear_logs(self):
        self.logs = []
        if os.path.exists(self.log_file):
            os.remove(self.log_file)