#!/usr/bin/env python3
"""
Interprocess Queue Manager with overflow policies as per spec.
"""

import time
import logging
from multiprocessing import Queue, Manager
from collections import deque

class QueueManager:
    """Manages interprocess queues with spec-compliant policies"""

    def __init__(self):
        self.logger = logging.getLogger('queue_manager')
        self.manager = Manager()

        # Create queues as per spec using multiprocessing
        self.queues = {
            'audio->stt': self.manager.Queue(maxsize=8),  # drop_oldest_on_overflow - handled in put_message
            'stt->nlp': self.manager.Queue(maxsize=4),     # prioritization=wakeword_input - simplified
            'nlp->tts': self.manager.Queue(maxsize=2)      # standard queue
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
            if queue_name == 'audio->stt':
                # Drop oldest on overflow
                if queue.full():
                    try:
                        queue.get_nowait()  # Drop oldest
                    except:
                        pass
                queue.put(message)
            elif queue_name == 'stt->nlp':
                # Simplified priority - wakeword gets put first if space
                # For full implementation, would need priority queue
                if message.get('source') == 'wakeword' and queue.full():
                    # Try to make space by getting one
                    try:
                        queue.get_nowait()
                    except:
                        pass
                queue.put(message)
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
        maxsizes = {'audio->stt': 8, 'stt->nlp': 4, 'nlp->tts': 2}
        for name, queue in self.queues.items():
            try:
                stats[name] = {
                    'size': queue.qsize(),
                    'maxsize': maxsizes.get(name, 0),
                    'empty': queue.empty(),
                    'full': queue.full()
                }
            except Exception as e:
                stats[name] = {'error': str(e)}
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