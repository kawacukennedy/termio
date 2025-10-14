#!/usr/bin/env python3
"""
Auralis Daemon Supervisor as per microarchitecture spec.
Manages start/stop of modules, handles secrets, exposes local socket.
"""

import os
import sys
import time
import signal
import threading
import multiprocessing as mp
from multiprocessing import Process
import socket
import json
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Performance monitoring limited.")
import logging
from queue_manager import QueueManager
from memory import ConversationMemoryModule
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

class APIHandler(BaseHTTPRequestHandler):
    def __init__(self, daemon, *args, **kwargs):
        self.daemon = daemon
        super().__init__(*args, **kwargs)

    def do_POST(self):
        if self.path == '/input/text':
            self.handle_text_input()
        elif self.path == '/action/execute':
            self.handle_action_execute()
        else:
            self.send_error(404)

    def handle_text_input(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        text = data.get('text', '')

        # Send to NLP queue
        self.daemon.queues['stt->nlp'].put({
            'type': 'text_input',
            'text': text,
            'source': 'api'
        })

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'accepted'}).encode())

    def handle_action_execute(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        action = data.get('action', '')
        params = data.get('params', {})

        # Send to action queue
        self.daemon.queues['nlp->action'].put({
            'type': 'api_action',
            'action': action,
            'params': params
        })

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'executing'}).encode())

    def log_message(self, format, *args):
        # Suppress default logging
        pass

class AuralisDaemon:
    def __init__(self, config):
        self.config = config
        self.workers = {}
        self.queues = {}
        self.running = False
        self.logger = logging.getLogger('daemon')

        # Initialize memory module
        self.memory = ConversationMemoryModule(config)

        # Create interprocess queues with spec-compliant policies
        self.queue_manager = QueueManager()
        self.queues = self.queue_manager.queues

        # Failure mode tracking
        self.worker_restart_counts = {}
        self.api_server_failed = False
        self.memory_failed = False
        self.queue_failed = False
        self.degraded_mode = False

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

    def start(self):
        """Start the daemon and all workers"""
        self.logger.info("Starting Auralis daemon...")
        self.running = True

        # Start workers
        self._start_workers()

        # Start health monitoring
        self._start_health_monitor()

        # Start local API server
        self._start_api_server()

        self.logger.info("Auralis daemon started")

        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def _start_workers(self):
        """Start all worker processes with failure handling"""
        from audio_worker import AudioWorker
        from inference_worker import InferenceWorker
        from action_worker import ActionWorker
        from ui_worker import UIWorker
        from security import SecurityModule
        from settings import SettingsModule

        # Initialize shared modules with error handling
        try:
            settings = SettingsModule(self.config)
            security = SecurityModule(self.config, settings)
        except ImportError as e:
            self.logger.warning(f"Security module not available: {e}")
            self.degraded_mode = True
            security = None
            settings = None
        except Exception as e:
            self.logger.error(f"Failed to initialize shared modules: {e}")
            self.degraded_mode = True
            security = None

        # Check first-run permissions
        if security and not security.check_first_run_permissions():
            self.logger.error("First-run permissions not granted. Exiting.")
            self.running = False
            return

        # Start workers with individual error handling
        workers_to_start = [
            ('audio', AudioWorker),
            ('inference', InferenceWorker),
            ('action', ActionWorker),
            ('ui', UIWorker)
        ]

        for worker_name, worker_class in workers_to_start:
            try:
                if worker_name == 'inference':
                    worker_instance = worker_class(self.config, self.queues, self.memory)
                elif worker_name == 'action':
                    worker_instance = worker_class(self.config, self.queues)
                    if security:
                        worker_instance.security = security
                else:
                    worker_instance = worker_class(self.config, self.queues)

                self.workers[worker_name] = Process(
                    target=worker_instance.run,
                    name=f'{worker_name}_worker'
                )
                self.workers[worker_name].start()
                self.worker_restart_counts[worker_name] = 0

            except Exception as e:
                self.logger.error(f"Failed to start {worker_name} worker: {e}")
                self.degraded_mode = True
                # Continue with other workers

    def _start_health_monitor(self):
        """Monitor worker health and restart if needed with backoff"""
        def monitor():
            consecutive_failures = {}
            max_consecutive_failures = 3
            backoff_times = {}

            while self.running:
                try:
                    # Check worker health
                    for name, process in list(self.workers.items()):
                        if not process.is_alive():
                            consecutive_failures[name] = consecutive_failures.get(name, 0) + 1

                            if consecutive_failures[name] >= max_consecutive_failures:
                                self.logger.error(f"Worker {name} failed {consecutive_failures[name]} times, entering degraded mode")
                                self.degraded_mode = True
                                # Remove from workers to stop restart attempts
                                del self.workers[name]
                                continue

                            # Check backoff
                            if name in backoff_times:
                                elapsed = time.time() - backoff_times[name]
                                backoff_duration = min(30, 2 ** self.worker_restart_counts.get(name, 0))  # Exponential backoff
                                if elapsed < backoff_duration:
                                    continue

                            self.logger.warning(f"Worker {name} died, restarting... (attempt {self.worker_restart_counts.get(name, 0) + 1})")
                            self._restart_worker(name)
                            backoff_times[name] = time.time()
                        else:
                            # Reset failure count on success
                            consecutive_failures[name] = 0

                    # Check memory health
                    if hasattr(self.memory, 'check_health'):
                        if not self.memory.check_health():
                            self.logger.warning("Memory module health check failed")
                            self.memory_failed = True

                    # Check queue health
                    try:
                        # Simple queue health check - try to put and get a test message
                        test_queue = self.queues.get('stt->nlp')
                        if test_queue:
                            test_queue.put({'type': 'health_check', 'timestamp': time.time()}, timeout=1)
                            # Don't block on get, just check if queue is responsive
                    except Exception as e:
                        self.logger.warning(f"Queue health check failed: {e}")
                        self.queue_failed = True

                except Exception as e:
                    self.logger.error(f"Health monitor error: {e}")

                time.sleep(5)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def _restart_worker(self, worker_name):
        """Restart a dead worker with tracking"""
        if worker_name in self.workers:
            # Clean up old process
            if self.workers[worker_name].is_alive():
                self.workers[worker_name].terminate()
                self.workers[worker_name].join(timeout=5)
                if self.workers[worker_name].is_alive():
                    self.workers[worker_name].kill()

            # Increment restart count
            self.worker_restart_counts[worker_name] = self.worker_restart_counts.get(worker_name, 0) + 1

            # Restart worker
            try:
                if worker_name == 'audio':
                    from audio_worker import AudioWorker
                    self.workers[worker_name] = Process(
                        target=AudioWorker(self.config, self.queues).run,
                        name='audio_worker'
                    )
                elif worker_name == 'inference':
                    from inference_worker import InferenceWorker
                    self.workers[worker_name] = Process(
                        target=InferenceWorker(self.config, self.queues, self.memory).run,
                        name='inference_worker'
                    )
                elif worker_name == 'action':
                    from action_worker import ActionWorker
                    self.workers[worker_name] = Process(
                        target=ActionWorker(self.config, self.queues).run,
                        name='action_worker'
                    )
                elif worker_name == 'ui':
                    from ui_worker import UIWorker
                    self.workers[worker_name] = Process(
                        target=UIWorker(self.config, self.queues).run,
                        name='ui_worker'
                    )

                self.workers[worker_name].start()
                self.logger.info(f"Restarted {worker_name} worker (attempt {self.worker_restart_counts[worker_name]})")

            except Exception as e:
                self.logger.error(f"Failed to restart {worker_name} worker: {e}")
                self.degraded_mode = True

    def _start_api_server(self):
        """Start local HTTP API server with failure handling"""
        def server():
            try:
                handler = lambda *args: APIHandler(self, *args)
                httpd = HTTPServer(('localhost', 8080), handler)
                httpd.serve_forever()
            except Exception as e:
                self.logger.error(f"API server failed: {e}")
                self.api_server_failed = True

        try:
            self.api_thread = threading.Thread(target=server, daemon=True)
            self.api_thread.start()
            self.logger.info("Local API server started on http://localhost:8080")
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            self.api_server_failed = True



    def _get_performance_stats(self):
        """Get performance statistics"""
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent()
            memory_mb = psutil.virtual_memory().used / 1024 / 1024
        else:
            cpu_percent = 0.0
            memory_mb = 0.0

        return {
            'cpu_percent': cpu_percent,
            'memory_mb': memory_mb,
            'workers_alive': sum(1 for p in self.workers.values() if p.is_alive())
        }

    def get_health_status(self):
        """Get comprehensive health status"""
        stats = self._get_performance_stats()
        worker_status = {}
        for name, process in self.workers.items():
            worker_status[name] = {
                'alive': process.is_alive(),
                'pid': process.pid if process.is_alive() else None,
                'restarts': self.worker_restart_counts.get(name, 0)
            }

        return {
            'overall_health': 'degraded' if self.degraded_mode else 'healthy',
            'workers': worker_status,
            'performance': stats,
            'failures': {
                'api_server': self.api_server_failed,
                'memory': self.memory_failed,
                'queue': self.queue_failed
            }
        }

    def shutdown(self, signum=None, frame=None):
        """Shutdown all workers gracefully"""
        self.logger.info("Shutting down Auralis daemon...")
        self.running = False

        # Stop workers
        for name, process in self.workers.items():
            if process.is_alive():
                process.terminate()

        # Wait for workers to finish
        for name, process in self.workers.items():
            process.join(timeout=10)
            if process.is_alive():
                process.kill()

        # Clear queues
        self.queue_manager.clear_queues()

        self.logger.info("Auralis daemon shutdown complete")
        sys.exit(0)