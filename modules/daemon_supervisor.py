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

class AuralisDaemon:
    def __init__(self, config):
        self.config = config
        self.workers = {}
        self.queues = {}
        self.running = False
        self.logger = logging.getLogger('daemon')

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
            target=InferenceWorker(self.config, self.queues).run,
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
                    target=InferenceWorker(self.config, self.queues).run,
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
        """Start local API server for CLI communication"""
        def server():
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            socket_path = '/tmp/auralis.sock'

            # Remove existing socket
            try:
                os.unlink(socket_path)
            except OSError:
                pass

            sock.bind(socket_path)
            sock.listen(1)

            while self.running:
                try:
                    conn, addr = sock.accept()
                    self._handle_api_request(conn)
                except:
                    break

            sock.close()
            try:
                os.unlink(socket_path)
            except OSError:
                pass

        thread = threading.Thread(target=server, daemon=True)
        thread.start()

    def _handle_api_request(self, conn):
        """Handle API request from CLI"""
        try:
            data = conn.recv(4096)
            if data:
                request = json.loads(data.decode())
                response = self._process_api_request(request)
                conn.sendall(json.dumps(response).encode())
        except Exception as e:
            self.logger.error(f"API request error: {e}")
        finally:
            conn.close()

    def _process_api_request(self, request):
        """Process API request"""
        action = request.get('action')

        if action == 'status':
            return {
                'status': 'running',
                'workers': {name: p.is_alive() for name, p in self.workers.items()},
                'performance': self._get_performance_stats(),
                'queues': self.queue_manager.get_queue_stats()
            }
        elif action == 'shutdown':
            self.running = False
            return {'status': 'shutting_down'}
        elif action == 'input':
            # Send input to inference worker
            self.queue_manager.put_message('stt->nlp', {
                'type': 'text_input',
                'text': request.get('text', ''),
                'source': 'api'
            })
            return {'status': 'input_queued'}

        return {'error': 'unknown_action'}

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