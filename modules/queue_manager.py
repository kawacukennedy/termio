#!/usr/bin/env python3
"""
Interprocess Queue Manager with overflow policies as per spec.
"""

import time
import logging
from multiprocessing import Queue
from collections import deque
import threading

class PriorityQueue:
    """Queue with prioritization support"""

    def __init__(self, maxsize=0):
        self.maxsize = maxsize
        self._queue = deque()
        self._lock = threading.Lock()

    def put(self, item, priority=0, block=True, timeout=None):
        """Put item with priority (higher priority = processed first)"""
        with self._lock:
            if self.maxsize > 0 and len(self._queue) >= self.maxsize:
                # Remove lowest priority item if full
                self._queue = deque(sorted(self._queue, key=lambda x: x[1], reverse=True)[:self.maxsize-1])

            self._queue.append((item, priority, time.time()))
            # Sort by priority (highest first)
            self._queue = deque(sorted(self._queue, key=lambda x: x[1], reverse=True))

    def get(self, block=True, timeout=None):
        """Get highest priority item"""
        with self._lock:
            if not self._queue:
                raise Exception("Queue empty")

            item, priority, timestamp = self._queue.popleft()
            return item

    def empty(self):
        with self._lock:
            return len(self._queue) == 0

    def full(self):
        with self._lock:
            return self.maxsize > 0 and len(self._queue) >= self.maxsize

    def qsize(self):
        with self._lock:
            return len(self._queue)

class DropOldestQueue(Queue):
    """Queue that drops oldest items on overflow"""

    def __init__(self, maxsize=0):
        super().__init__(maxsize)
        self._buffer = deque(maxlen=maxsize) if maxsize > 0 else deque()

    def put(self, item, block=True, timeout=None):
        """Put item, dropping oldest if full"""
        if self.maxsize > 0:
            if len(self._buffer) >= self.maxsize:
                # Drop oldest
                self._buffer.popleft()
            self._buffer.append(item)
        else:
            self._buffer.append(item)

    def get(self, block=True, timeout=None):
        """Get oldest item"""
        if not self._buffer:
            raise Exception("Queue empty")
        return self._buffer.popleft()

    def empty(self):
        return len(self._buffer) == 0

    def full(self):
        return self.maxsize > 0 and len(self._buffer) >= self.maxsize

    def qsize(self):
        return len(self._buffer)

class QueueManager:
    """Manages interprocess queues with spec-compliant policies"""

    def __init__(self):
        self.logger = logging.getLogger('queue_manager')

        # Create queues as per spec
        self.queues = {
            'audio->stt': DropOldestQueue(maxsize=8),  # drop_oldest_on_overflow
            'stt->nlp': PriorityQueue(maxsize=4),       # prioritization=wakeword_input
            'nlp->tts': Queue(maxsize=2)                 # standard queue
        }

    def get_queue(self, name):
        """Get queue by name"""
        return self.queues.get(name)

    def put_message(self, queue_name, message, priority=0):
        """Put message in queue with optional priority"""
        queue = self.queues.get(queue_name)
        if not queue:
            self.logger.error(f"Unknown queue: {queue_name}")
            return

        try:
            if queue_name == 'stt->nlp':
                # Wakeword messages get highest priority
                msg_priority = 10 if message.get('source') == 'wakeword' else priority
                queue.put(message, priority=msg_priority)
            else:
                queue.put(message)

            self.logger.debug(f"Message queued in {queue_name}: {message.get('type', 'unknown')}")
        except Exception as e:
            self.logger.error(f"Failed to queue message in {queue_name}: {e}")

    def get_message(self, queue_name, timeout=None):
        """Get message from queue"""
        queue = self.queues.get(queue_name)
        if not queue:
            self.logger.error(f"Unknown queue: {queue_name}")
            return None

        try:
            if timeout:
                # For timeout support, we'd need more complex implementation
                return queue.get(timeout=timeout)
            else:
                return queue.get()
        except Exception as e:
            self.logger.debug(f"No message in {queue_name}: {e}")
            return None

    def get_queue_stats(self):
        """Get statistics for all queues"""
        stats = {}
        for name, queue in self.queues.items():
            stats[name] = {
                'size': queue.qsize(),
                'maxsize': getattr(queue, 'maxsize', 0),
                'empty': queue.empty(),
                'full': queue.full()
            }
        return stats

    def clear_queues(self):
        """Clear all queues"""
        for name, queue in self.queues.items():
            while not queue.empty():
                try:
                    queue.get()
                except:
                    break
            self.logger.info(f"Cleared queue: {name}")