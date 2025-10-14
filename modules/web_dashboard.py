from flask import Flask, render_template, jsonify, request
import threading
import time
import psutil
import os
from pathlib import Path

class WebDashboard:
    def __init__(self, config, performance_module, memory_module, backup_module, external_api_module=None, plugins_module=None, language_module=None, automation_module=None):
        self.config = config
        self.performance = performance_module
        self.memory = memory_module
        self.backup = backup_module
        self.external_api = external_api_module
        self.plugins = plugins_module
        self.language = language_module
        self.automation = automation_module
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

        @self.app.route('/api/export', methods=['POST'])
        def export_data():
            """GDPR export all user data"""
            try:
                conversations = self.memory.get_all_conversations()
                # In real app, save to file and provide download link
                # For now, return JSON
                return jsonify({
                    'data': conversations,
                    'exported_at': time.time(),
                    'message': 'Data exported successfully'
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/delete', methods=['POST'])
        def delete_data():
            """GDPR delete all user data"""
            try:
                # Clear short term
                self.memory.short_term_memory.clear()
                # Clear long term if enabled
                if self.memory.conn:
                    self.memory.conn.execute("DELETE FROM turns")
                    self.memory.conn.commit()
                return jsonify({'message': 'All user data deleted successfully'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/external/<service>')
        def get_external_data(service):
            if not self.external_api:
                return jsonify({'error': 'External API module not available'}), 503

            try:
                if service == 'weather':
                    data = self.external_api.get_weather('New York')  # Default location
                elif service == 'news':
                    data = self.external_api.get_news('technology')
                elif service == 'time':
                    data = self.external_api.get_world_time('Tokyo')
                elif service == 'stock':
                    data = self.external_api.get_stock_price('AAPL')
                elif service == 'recipe':
                    data = self.external_api.get_recipe()
                elif service == 'joke':
                    data = self.external_api.get_joke()
                elif service == 'quote':
                    data = self.external_api.get_quote()
                else:
                    return jsonify({'error': f'Unknown service: {service}'}), 400

                return jsonify({'result': data})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/voice/test', methods=['POST'])
        def test_voice():
            # Placeholder for voice testing
            return jsonify({'message': 'Voice test endpoint - implementation pending'})

        @self.app.route('/api/screen/test', methods=['POST'])
        def test_screen():
            # Placeholder for screen testing
            return jsonify({'message': 'Screen test endpoint - implementation pending'})

        @self.app.route('/api/plugins')
        def get_plugins():
            if not self.plugins:
                return jsonify({'error': 'Plugins module not available'}), 503

            try:
                plugins_list = self.plugins.list_plugins()
                return jsonify(plugins_list)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/language/supported')
        def get_supported_languages():
            if not self.language:
                return jsonify({'error': 'Language module not available'}), 503

            try:
                languages = self.language.get_supported_languages()
                return jsonify(languages)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/language/translate', methods=['POST'])
        def translate_text():
            if not self.language:
                return jsonify({'error': 'Language module not available'}), 503

            try:
                data = request.get_json()
                text = data.get('text', '')
                target_lang = data.get('target_lang', 'en')
                translated = self.language.translate_text(text, target_lang)
                return jsonify({'translated': translated})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/automation/tasks')
        def get_scheduled_tasks():
            if not self.automation:
                return jsonify({'error': 'Automation module not available'}), 503

            try:
                tasks = self.automation.list_scheduled_tasks()
                return jsonify(tasks)
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/automation/reminder', methods=['POST'])
        def create_reminder():
            if not self.automation:
                return jsonify({'error': 'Automation module not available'}), 503

            try:
                data = request.get_json()
                message = data.get('message', '')
                delay = int(data.get('delay_seconds', 60))
                result = self.automation.create_reminder(message, delay)
                return jsonify({'result': result})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/plugins/<plugin_name>', methods=['POST'])
        def run_plugin(plugin_name):
            if not self.plugins:
                return jsonify({'error': 'Plugins module not available'}), 503

            try:
                result = self.plugins.execute_plugin(plugin_name, {})
                return jsonify({'result': result})
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