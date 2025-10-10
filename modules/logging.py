import json
import os

class LoggingModule:
    def __init__(self, config):
        self.config = config
        os.makedirs('logs', exist_ok=True)

    def log(self, message):
        # Log to JSONL
        with open('logs/conversation.jsonl', 'a') as f:
            f.write(json.dumps(message) + '\n')