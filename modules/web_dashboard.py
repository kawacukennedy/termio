from flask import Flask, render_template, jsonify, request
import threading
import time
import psutil
import os
from pathlib import Path

class WebDashboard:
    def __init__(self, config, performance_module, memory_module, backup_module):
        self.config = config
        self.performance = performance_module
        self.memory = memory_module
        self.backup = backup_module
        self.app = Flask(__name__,
                        template_folder='../templates',
                        static_folder='../static')
        self.setup_routes()
        self.server_thread = None
        self.is_running = False

    def setup_routes(self):
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html',
                                 app_name=self.config['app_identity']['name'],
                                 version=self.config['app_identity']['version'])

        @self.app.route('/api/status')
        def get_status():
            try:
                perf_status = self.performance.get_status()
                memory_stats = {
                    'total_conversations': len(self.memory.get_recent_turns(1000)),
                    'short_term_count': len(self.memory.short_term_memory),
                    'long_term_size': self._get_db_size()
                }

                return jsonify({
                    'performance': perf_status,
                    'memory': memory_stats,
                    'uptime': time.time() - getattr(self, 'start_time', time.time()),
                    'timestamp': time.time()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/backups')
        def get_backups():
            try:
                backups = self.backup.list_backups()
                return jsonify(backups)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/cleanup', methods=['POST'])
        def run_cleanup():
            try:
                # Run cleanup in background
                def cleanup_task():
                    os.system('python3 scripts/cleanup.py')

                thread = threading.Thread(target=cleanup_task, daemon=True)
                thread.start()

                return jsonify({'message': 'Cleanup started in background'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/logs')
        def get_logs():
            try:
                logs_dir = Path('logs')
                if not logs_dir.exists():
                    return jsonify([])

                log_files = []
                for log_file in logs_dir.glob('*.jsonl'):
                    size = log_file.stat().st_size
                    modified = log_file.stat().st_mtime
                    log_files.append({
                        'name': log_file.name,
                        'size_kb': round(size / 1024, 1),
                        'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modified))
                    })

                return jsonify(log_files)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def _get_db_size(self):
        """Get database file size"""
        db_path = Path('memory.db')
        if db_path.exists():
            return round(db_path.stat().st_size / (1024 * 1024), 2)  # MB
        return 0

    def start(self, host='localhost', port=5000):
        """Start the web dashboard"""
        if self.is_running:
            return False

        self.start_time = time.time()
        self.server_thread = threading.Thread(
            target=self.app.run,
            kwargs={'host': host, 'port': port, 'debug': False, 'use_reloader': False},
            daemon=True
        )
        self.server_thread.start()
        self.is_running = True
        print(f"🌐 Web dashboard started at http://{host}:{port}")
        return True

    def stop(self):
        """Stop the web dashboard"""
        self.is_running = False
        # Flask doesn't have a built-in stop method, but since it's daemon thread, it will stop with main process

    def is_active(self):
        """Check if dashboard is running"""
        return self.is_running