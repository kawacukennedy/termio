from collections import deque
import sqlite3
import os
from datetime import datetime
from cryptography.fernet import Fernet
import base64
import hnswlib
import numpy as np
from sentence_transformers import SentenceTransformer

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
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.index_path = os.path.expanduser('~/.auralis_index.bin')
            self.index = hnswlib.Index(space='cosine', dim=384)
            if os.path.exists(self.index_path):
                self.index.load_index(self.index_path)
            else:
                self.index.init_index(max_elements=10000, ef_construction=200, M=16)
            self.current_id = self.get_max_id() + 1
        else:
            self.conn = None
            self.model = None
            self.index = None

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

    def get_max_id(self):
        cursor = self.conn.execute("SELECT MAX(id) FROM interactions")
        result = cursor.fetchone()[0]
        return result if result else 0

    def add_interaction(self, user_input, response):
        self.memory.append({"user": user_input, "response": response})
        if self.enable_long_term and self.conn:
            encrypted_user = self.encrypt(user_input)
            encrypted_response = self.encrypt(response)
            cursor = self.conn.execute("INSERT INTO interactions (timestamp, user, response) VALUES (?, ?, ?)",
                              (datetime.now().isoformat(), encrypted_user, encrypted_response))
            self.conn.commit()
            interaction_id = cursor.lastrowid
            # Embed and add to index
            text = user_input + " " + response
            embedding = self.model.encode(text)
            self.index.add_items(np.array([embedding]), np.array([interaction_id]))
            self.index.save_index(self.index_path)
            self.current_id += 1

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

    def retrieve_similar(self, query, k=5):
        if not self.enable_long_term or not self.index:
            return []
        query_embedding = self.model.encode(query)
        labels, distances = self.index.knn_query(np.array([query_embedding]), k=k)
        ids = labels[0]
        interactions = []
        for id in ids:
            cursor = self.conn.execute("SELECT user, response FROM interactions WHERE id = ?", (int(id),))
            row = cursor.fetchone()
            if row:
                interactions.append({"user": self.decrypt(row[0]), "response": self.decrypt(row[1])})
        return interactions