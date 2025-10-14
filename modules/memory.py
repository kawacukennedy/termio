import sqlite3
import json
from cryptography.fernet import Fernet
import os
import time
from collections import deque
import hashlib
import logging
import math

class ConversationMemoryModule:
    def __init__(self, config):
        self.config = config
        self.short_term_config = config.get('memory_management', {}).get('short_term', {})
        self.long_term_config = config.get('memory_management', {}).get('long_term', {})
        self.logger = logging.getLogger('memory')

        # Short-term: in-memory ring buffer, max_turns=3, no persistence
        self.short_term_memory = deque(maxlen=3)

        # Long-term: encrypted SQLite, enabled by default = false
        self.long_term_enabled = self.long_term_config.get('enabled_by_default', False)
        self.rag_enabled = self.long_term_config.get('rag_enabled', False)
        self.embedding_model = None

        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
        self.conn = None

        if self.long_term_enabled:
            self.conn = sqlite3.connect('memory.db')
            self._init_db()

        # Initialize RAG if enabled
        if self.rag_enabled:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.logger.info("RAG enabled with MiniLM embeddings")
            except ImportError:
                self.logger.warning("sentence-transformers not installed, disabling RAG")
                self.rag_enabled = False

    def _load_or_generate_key(self):
        key_file = 'memory_key.key'
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

    def _init_db(self):
        # Main turns table
        self.conn.execute('''CREATE TABLE IF NOT EXISTS turns (
            id INTEGER PRIMARY KEY,
            user_hash TEXT,
            ai_hash TEXT,
            user_encrypted TEXT,
            ai_encrypted TEXT,
            timestamp REAL,
            embedding TEXT
        )''')

        # Additional tables
        self.conn.execute('''CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, content TEXT, timestamp REAL)''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT)''')

        # Create indexes for performance
        self.conn.execute('''CREATE INDEX IF NOT EXISTS idx_turns_timestamp ON turns(timestamp)''')
        self.conn.execute('''CREATE INDEX IF NOT EXISTS idx_turns_user_hash ON turns(user_hash)''')

    def add_turn(self, user, ai):
        timestamp = time.time()
        # Add to short term
        self.short_term_memory.append({'user': user, 'ai': ai, 'timestamp': timestamp})

        # Compute embedding if RAG enabled
        embedding = None
        if self.embedding_model:
            embedding = json.dumps(self.embedding_model.encode(user).tolist())

        # Add to long term (encrypted) if enabled
        if self.conn:
            user_hash = hashlib.sha256(user.encode()).hexdigest()
            ai_hash = hashlib.sha256(ai.encode()).hexdigest()
            encrypted_user = self.cipher.encrypt(user.encode())
            encrypted_ai = self.cipher.encrypt(ai.encode())
            self.conn.execute("INSERT INTO turns (user_hash, ai_hash, user_encrypted, ai_encrypted, timestamp, embedding) VALUES (?, ?, ?, ?, ?, ?)",
                              (user_hash, ai_hash, encrypted_user, encrypted_ai, timestamp, embedding))
            self.conn.commit()

    def get_recent_turns(self, n=3):
        if not self.conn:
            return list(self.short_term_memory)[-n:]  # Return from short term if long term disabled
        cursor = self.conn.execute("SELECT user_encrypted, ai_encrypted, timestamp FROM turns ORDER BY id DESC LIMIT ?", (n,))
        turns = []
        for row in cursor:
            user = self.cipher.decrypt(row[0]).decode()
            ai = self.cipher.decrypt(row[1]).decode()
            timestamp = row[2]
            turns.append({'user': user, 'ai': ai, 'timestamp': timestamp})
        return turns[::-1]  # Reverse to chronological order

    def get_all_conversations(self):
        """Get all conversations for export"""
        if not self.conn:
            return [(turn['user'], turn['ai'], turn['timestamp']) for turn in self.short_term_memory]
        cursor = self.conn.execute("SELECT user_encrypted, ai_encrypted, timestamp FROM turns ORDER BY id")
        conversations = []
        for row in cursor:
            user = self.cipher.decrypt(row[0]).decode()
            ai = self.cipher.decrypt(row[1]).decode()
            timestamp = row[2]
            conversations.append((user, ai, timestamp))
        return conversations

    def get_relevant_turns(self, query, top_k=3):
        """Retrieve relevant turns using embeddings for RAG"""
        if not self.embedding_model or not self.conn:
            return self.get_recent_turns(top_k)

        # Compute query embedding
        query_emb = self.embedding_model.encode(query)

        # Get all turns with embeddings
        cursor = self.conn.execute("SELECT id, user_encrypted, ai_encrypted, timestamp, embedding FROM turns WHERE embedding IS NOT NULL")
        turns = []
        for row in cursor:
            emb = json.loads(row[4])
            similarity = self._cosine_similarity(query_emb, emb)
            turns.append({
                'id': row[0],
                'user': self.cipher.decrypt(row[1]).decode(),
                'ai': self.cipher.decrypt(row[2]).decode(),
                'timestamp': row[3],
                'similarity': similarity
            })

        # Sort by similarity descending
        turns.sort(key=lambda x: x['similarity'], reverse=True)
        return turns[:top_k]

    def _cosine_similarity(self, a, b):
        """Compute cosine similarity between two vectors"""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x ** 2 for x in a))
        norm_b = math.sqrt(sum(x ** 2 for x in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0

    def prune_memory(self):
        # LRU pruning with semantic decay - keep only recent entries and delete old ones
        if self.conn:
            # Delete turns older than 30 days (semantic decay)
            cutoff = time.time() - (30 * 24 * 60 * 60)
            self.conn.execute("DELETE FROM turns WHERE timestamp < ?", (cutoff,))
            # Keep only 100 most recent
            self.conn.execute("DELETE FROM turns WHERE id NOT IN (SELECT id FROM turns ORDER BY timestamp DESC LIMIT 100)")
            self.conn.commit()