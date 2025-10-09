from collections import deque
import sqlite3
import os
from datetime import datetime
from cryptography.fernet import Fernet
import base64

class ConversationMemory:
    def __init__(self, max_turns=3, enable_long_term=False):
        self.memory = deque(maxlen=max_turns)
        self.enable_long_term = enable_long_term
        self.key_path = os.path.expanduser('~/.auralis_key')
        self.key = self.load_or_generate_key()
        self.cipher = Fernet(self.key)
        if self.enable_long_term:
            self.db_path = os.path.expanduser('~/.auralis_memory.db')
            self.conn = sqlite3.connect(self.db_path)
            self.create_table()
        else:
            self.conn = None

    def load_or_generate_key(self):
        if os.path.exists(self.key_path):
            with open(self.key_path, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(key)
            return key

    def encrypt(self, text):
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt(self, text):
        return self.cipher.decrypt(text.encode()).decode()

    def create_table(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS interactions
                             (id INTEGER PRIMARY KEY, timestamp TEXT, user TEXT, response TEXT)''')
        self.conn.commit()

    def add_interaction(self, user_input, response):
        self.memory.append({"user": user_input, "response": response})
        if self.enable_long_term and self.conn:
            encrypted_user = self.encrypt(user_input)
            encrypted_response = self.encrypt(response)
            self.conn.execute("INSERT INTO interactions (timestamp, user, response) VALUES (?, ?, ?)",
                              (datetime.now().isoformat(), encrypted_user, encrypted_response))
            self.conn.commit()

    def get_context(self):
        return list(self.memory)

    def get_long_term_context(self, limit=10):
        if self.enable_long_term and self.conn:
            cursor = self.conn.execute("SELECT user, response FROM interactions ORDER BY id DESC LIMIT ?", (limit,))
            return [{"user": self.decrypt(row[0]), "response": self.decrypt(row[1])} for row in cursor.fetchall()]
        return []

    def get_last_response(self):
        if self.memory:
            return self.memory[-1]["response"]
        return None