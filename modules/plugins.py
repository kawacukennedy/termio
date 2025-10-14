import os
import importlib.util
import subprocess
import json
import time
import hashlib
import hmac
from pathlib import Path
import socket
import threading
import multiprocessing as mp
from multiprocessing import Process, Queue

class PluginHostModule:
    def __init__(self, config):
        self.config = config
        self.plugin_config = config.get('plugins_and_extensibility', {}).get('plugin_system', {})
        self.loaded_plugins = {}
        self.plugin_dir = Path('plugins')
        self.plugin_dir.mkdir(exist_ok=True)
        self.signing_key = b'auralis_plugin_signing_key'  # In production, use secure key
        self.isolation_processes = {}
        self.api_sockets = {}

        # Start plugin API server
        self.api_thread = threading.Thread(target=self._run_api_server, daemon=True)
        self.api_thread.start()

    def load_plugins(self):
        """Load all available plugins with validation"""
        for plugin_file in self.plugin_dir.glob('*.jpkg'):  # Plugin packages
            self.load_plugin_package(plugin_file)

    def validate_manifest(self, manifest):
        """Validate plugin manifest against schema"""
        required_fields = ['name', 'version', 'entry', 'permissions', 'size_limit_mb']

        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Missing required field: {field}")

        # Validate permissions
        valid_permissions = [
            'microphone', 'screen_read', 'screen_control', 'file_read',
            'file_write', 'network', 'system_info', 'tts', 'stt'
        ]

        for perm in manifest['permissions']:
            if perm not in valid_permissions:
                raise ValueError(f"Invalid permission: {perm}")

        # Validate size limit
        if manifest['size_limit_mb'] > 10:  # Max 10MB as per spec
            raise ValueError("Plugin size limit exceeds 10MB")

        return True

    def verify_signature(self, plugin_path, signature):
        """Verify plugin signature"""
        try:
            with open(plugin_path, 'rb') as f:
                plugin_data = f.read()

            expected_signature = hmac.new(self.signing_key, plugin_data, hashlib.sha256).hexdigest()
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False

    def sign_plugin(self, plugin_path):
        """Sign a plugin package"""
        try:
            with open(plugin_path, 'rb') as f:
                plugin_data = f.read()

            signature = hmac.new(self.signing_key, plugin_data, hashlib.sha256).hexdigest()

            # Save signature file
            sig_path = plugin_path.with_suffix('.sig')
            with open(sig_path, 'w') as f:
                f.write(signature)

            print(f"Plugin signed: {sig_path}")
            return signature
        except Exception as e:
            print(f"Plugin signing failed: {e}")
            return None

    def load_plugin_package(self, package_path):
        """Load a plugin package with manifest validation and isolation"""
        try:
            # Check for signature
            sig_path = package_path.with_suffix('.sig')
            if not sig_path.exists():
                print(f"Warning: Plugin {package_path.name} is not signed. Loading with warning.")
                user_override = input("Load unsigned plugin? (y/n): ").lower().strip()
                if user_override != 'y':
                    return

            # Load and validate manifest
            manifest_path = package_path.with_suffix('.json')
            if not manifest_path.exists():
                raise ValueError("Plugin manifest not found")

            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            self.validate_manifest(manifest)

            # Verify signature if present
            if sig_path.exists():
                with open(sig_path, 'r') as f:
                    signature = f.read().strip()

                if not self.verify_signature(package_path, signature):
                    raise ValueError("Plugin signature verification failed")

            # Extract and load plugin code
            plugin_name = manifest['name']

            # Start isolated process for plugin
            self._start_isolated_plugin(package_path, manifest)

            print(f"Loaded plugin: {plugin_name} v{manifest['version']}")

        except Exception as e:
            print(f"Failed to load plugin {package_path.name}: {e}")

    def _start_isolated_plugin(self, package_path, manifest):
        """Start plugin in isolated process"""
        plugin_name = manifest['name']

        # Create communication queues
        request_queue = Queue()
        response_queue = Queue()

        # Start plugin process
        process = Process(
            target=self._run_isolated_plugin,
            args=(package_path, manifest, request_queue, response_queue),
            name=f'plugin_{plugin_name}'
        )
        process.start()

        self.isolation_processes[plugin_name] = {
            'process': process,
            'request_queue': request_queue,
            'response_queue': response_queue,
            'manifest': manifest
        }

    def execute_plugin(self, plugin_name, command, **kwargs):
        """Execute a plugin command via isolated process"""
        if plugin_name not in self.isolation_processes:
            return f"Plugin {plugin_name} not loaded"

        plugin_data = self.isolation_processes[plugin_name]

        try:
            # Send request to plugin process
            request = {
                'command': command,
                'kwargs': kwargs,
                'timestamp': time.time()
            }

            plugin_data['request_queue'].put(request)

            # Wait for response with timeout
            if plugin_data['response_queue'].get(timeout=10):
                response = plugin_data['response_queue'].get(timeout=5)
                return response
            else:
                return "Plugin request timeout"

        except Exception as e:
            return f"Plugin execution error: {e}"

    def _run_isolated_plugin(self, package_path, manifest, request_queue, response_queue):
        """Run plugin in isolated process"""
        try:
            # Load plugin code
            plugin_name = manifest['name']
            entry_point = manifest['entry']

            # Import plugin module
            spec = importlib.util.spec_from_file_location(plugin_name, package_path / entry_point)
            if not spec or not spec.loader:
                raise ValueError("Invalid plugin entry point")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Plugin event loop
            while True:
                try:
                    # Wait for requests
                    request = request_queue.get(timeout=1)

                    command = request.get('command')
                    kwargs = request.get('kwargs', {})

                    # Execute command
                    if hasattr(module, command):
                        func = getattr(module, command)
                        result = func(**kwargs)

                        # Send response
                        response_queue.put({
                            'result': result,
                            'success': True
                        })
                    else:
                        response_queue.put({
                            'result': f"Command {command} not found",
                            'success': False
                        })

                except Exception as e:
                    response_queue.put({
                        'result': f"Plugin error: {e}",
                        'success': False
                    })

        except Exception as e:
            print(f"Isolated plugin {manifest['name']} error: {e}")

    def _run_api_server(self):
        """Run plugin API server for external communication"""
        try:
            server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            socket_path = '/tmp/auralis_plugins.sock'

            # Remove existing socket
            try:
                os.unlink(socket_path)
            except OSError:
                pass

            server_socket.bind(socket_path)
            server_socket.listen(5)

            while True:
                try:
                    client_socket, _ = server_socket.accept()
                    self._handle_plugin_api_request(client_socket)
                except:
                    break

            server_socket.close()
            try:
                os.unlink(socket_path)
            except OSError:
                pass

        except Exception as e:
            print(f"Plugin API server error: {e}")

    def _handle_plugin_api_request(self, client_socket):
        """Handle plugin API requests"""
        try:
            data = client_socket.recv(4096)
            if data:
                request = json.loads(data.decode())

                # Process request (simplified)
                plugin_name = request.get('plugin')
                command = request.get('command')
                kwargs = request.get('kwargs', {})

                result = self.execute_plugin(plugin_name, command, **kwargs)

                response = {
                    'result': result,
                    'timestamp': time.time()
                }

                client_socket.sendall(json.dumps(response).encode())

        except Exception as e:
            print(f"Plugin API request error: {e}")
        finally:
            client_socket.close()

    def list_plugins(self):
        """List all loaded plugins"""
        return {name: plugin['info'] for name, plugin in self.loaded_plugins.items()}

    def unload_plugin(self, plugin_name):
        """Unload a plugin"""
        if plugin_name in self.loaded_plugins:
            del self.loaded_plugins[plugin_name]
            print(f"Unloaded plugin: {plugin_name}")
            return True
        return False

    def create_plugin_template(self, name, description="Auralis plugin"):
        """Create a plugin package template with manifest"""
        # Create plugin directory
        plugin_dir = self.plugin_dir / name
        plugin_dir.mkdir(exist_ok=True)

        # Create manifest
        manifest = {
            "name": name,
            "version": "1.0.0",
            "entry": f"{name}.py",
            "permissions": ["system_info"],
            "size_limit_mb": 5,
            "description": description,
            "author": "Developer",
            "homepage": ""
        }

        manifest_path = plugin_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        # Create plugin code template
        template = f'''"""
{description}
"""

def register_plugin():
    """Register this plugin with Auralis"""
    return {{
        "name": "{name}",
        "version": "1.0.0",
        "description": "{description}",
        "commands": ["example_command"]
    }}

def example_command(text="Hello World"):
    """Example plugin command"""
    return f"Plugin {{__name__}} says: {{text}}"

def get_weather(city="New York"):
    """Get weather information (requires network permission)"""
    # This would make an API call
    return f"Weather in {{city}}: Sunny, 72°F"
'''

        plugin_path = plugin_dir / f"{name}.py"
        with open(plugin_path, 'w') as f:
            f.write(template)

        # Create __init__.py
        init_path = plugin_dir / "__init__.py"
        with open(init_path, 'w') as f:
            f.write("# Plugin package\n")

        print(f"Created plugin template: {plugin_dir}")
        return plugin_dir

    def package_plugin(self, plugin_name):
        """Package plugin into .jpkg format"""
        plugin_dir = self.plugin_dir / plugin_name
        if not plugin_dir.exists():
            return f"Plugin {plugin_name} not found"

        # Create package file
        import zipfile

        package_path = self.plugin_dir / f"{plugin_name}.jpkg"
        with zipfile.ZipFile(package_path, 'w') as zf:
            for file_path in plugin_dir.rglob('*'):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(plugin_dir))

        print(f"Packaged plugin: {package_path}")
        return package_path

    def sign_plugin_cli(self, plugin_name):
        """Sign plugin for distribution"""
        package_path = self.plugin_dir / f"{plugin_name}.jpkg"
        if not package_path.exists():
            return f"Plugin package {plugin_name}.jpkg not found"

        signature = self.sign_plugin(package_path)
        if signature:
            return f"Plugin signed successfully: {signature[:16]}..."
        return "Plugin signing failed"

    def install_plugin(self, package_path):
        """Install a plugin package"""
        if not package_path.exists():
            return f"Plugin package {package_path} not found"

        # Copy to plugins directory
        dest_path = self.plugin_dir / package_path.name
        import shutil
        shutil.copy2(package_path, dest_path)

        # Load the plugin
        self.load_plugin_package(dest_path)

        return f"Plugin {package_path.name} installed"

    def list_installed_plugins(self):
        """List all installed plugins with status"""
        plugins = {}
        for name, data in self.isolation_processes.items():
            manifest = data['manifest']
            plugins[name] = {
                'version': manifest['version'],
                'description': manifest.get('description', ''),
                'permissions': manifest['permissions'],
                'status': 'running' if data['process'].is_alive() else 'stopped'
            }

        return plugins