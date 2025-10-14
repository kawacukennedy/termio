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
import psutil
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
        """Start all worker processes"""
        from audio_worker import AudioWorker
        from inference_worker import InferenceWorker
        from action_worker import ActionWorker
        from ui_worker import UIWorker
        from security import SecurityModule
        from settings import SettingsModule

        # Initialize shared modules
        settings = SettingsModule(self.config)
        security = SecurityModule(self.config, settings)

        # Check first-run permissions
        if not security.check_first_run_permissions():
            self.logger.error("First-run permissions not granted. Exiting.")
            self.running = False
            return

        # Audio worker
        self.workers['audio'] = Process(
            target=AudioWorker(self.config, self.queues).run,
            name='audio_worker'
        )
        self.workers['audio'].start()

        # Inference worker
        self.workers['inference'] = Process(
            target=InferenceWorker(self.config, self.queues, self.memory).run,
            name='inference_worker'
        )
        self.workers['inference'].start()

        # Action worker (with security)
        action_worker = ActionWorker(self.config, self.queues)
        action_worker.security = security
        self.workers['action'] = Process(
            target=action_worker.run,
            name='action_worker'
        )
        self.workers['action'].start()

        # UI worker
        self.workers['ui'] = Process(
            target=UIWorker(self.config, self.queues).run,
            name='ui_worker'
        )
        self.workers['ui'].start()

    def _start_health_monitor(self):
        """Monitor worker health and restart if needed"""
        def monitor():
            while self.running:
                for name, process in self.workers.items():
                    if not process.is_alive():
                        self.logger.warning(f"Worker {name} died, restarting...")
                        self._restart_worker(name)
                time.sleep(5)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def _restart_worker(self, worker_name):
        """Restart a dead worker"""
        if worker_name in self.workers:
            # Clean up old process
            if self.workers[worker_name].is_alive():
                self.workers[worker_name].terminate()
                self.workers[worker_name].join(timeout=5)
                if self.workers[worker_name].is_alive():
                    self.workers[worker_name].kill()

            # Restart worker
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

    def _start_api_server(self):
        """Start local HTTP API server"""
        def server():
            handler = lambda *args: APIHandler(self, *args)
            httpd = HTTPServer(('localhost', 8080), handler)
            httpd.serve_forever()

        self.api_thread = threading.Thread(target=server, daemon=True)
        self.api_thread.start()
        self.logger.info("Local API server started on http://localhost:8080")



    def _get_performance_stats(self):
        """Get performance statistics"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_mb': psutil.virtual_memory().used / 1024 / 1024,
            'workers_alive': sum(1 for p in self.workers.values() if p.is_alive())
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