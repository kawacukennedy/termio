import sqlite3
import json
from cryptography.fernet import Fernet
import os
import time

class ConversationMemoryModule:
    def __init__(self, config):
        self.config = config
        self.short_term = config['memory_management']['short_term']
        self.long_term = config['memory_management']['long_term']
        self.short_term_memory = []
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
        self.conn = sqlite3.connect('memory.db')
        self._init_db()

    def _load_or_generate_key(self):
        key_file = 'memory_key.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def _init_db(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY,
            user TEXT,
            ai TEXT,
            timestamp REAL
        )''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, content TEXT)''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT)''')

    def add_turn(self, user, ai):
        # Add to short term
        self.short_term_memory.append({'user': user, 'ai': ai, 'timestamp': time.time()})
        if len(self.short_term_memory) > self.short_term['max_turns']:
            self.short_term_memory.pop(0)

        # Add to long term (encrypted)
        encrypted_user = self.cipher.encrypt(user.encode())
        encrypted_ai = self.cipher.encrypt(ai.encode())
        self.conn.execute("INSERT INTO turns (user, ai, timestamp) VALUES (?, ?, ?)",
                         (encrypted_user, encrypted_ai, time.time()))
        self.conn.commit()

    def get_recent_turns(self, n=3):
        cursor = self.conn.execute("SELECT user, ai FROM turns ORDER BY id DESC LIMIT ?", (n,))
        turns = []
        for row in cursor:
            user = self.cipher.decrypt(row[0]).decode()
            ai = self.cipher.decrypt(row[1]).decode()
            turns.append({'user': user, 'ai': ai})
        return turns[::-1]  # Reverse to chronological order

    def prune_memory(self):
        # LRU pruning - keep only recent entries
        self.conn.execute("DELETE FROM turns WHERE id NOT IN (SELECT id FROM turns ORDER BY timestamp DESC LIMIT 100)")
        self.conn.commit()