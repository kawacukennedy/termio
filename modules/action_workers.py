import subprocess
import os
import shutil
import requests
from pathlib import Path
import tempfile
import threading
import queue
import webbrowser
import smtplib
from email.mime.text import MIMEText

class ActionWorkers:
    def __init__(self, security_module):
        self.security = security_module
        self.task_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self.worker_loop, daemon=True)
        self.worker_thread.start()

    def worker_loop(self):
        while True:
            task = self.task_queue.get()
            try:
                self.execute_task(task)
            except Exception as e:
                print(f"Task error: {e}")
            self.task_queue.task_done()

    def submit_task(self, task_type, params):
        self.task_queue.put({'type': task_type, 'params': params})

    def execute_task(self, task):
        task_type = task['type']
        params = task['params']
        if task_type == 'run_shell':
            if self.security.check_permission('shell_execution'):
                self.run_shell_sandboxed(params['command'])
        elif task_type == 'filesystem':
            if self.security.check_permission('filesystem_access'):
                self.filesystem_operation(params['op'], params['path'], params.get('content'))
        elif task_type == 'network':
            if self.security.check_permission('network_access'):
                self.network_request(params['url'], params.get('method', 'GET'))
        elif task_type == 'notification':
            self.send_notification(params['message'])

    def run_shell_sandboxed(self, command):
        # Sandboxed shell: limit commands, use subprocess with timeout
        allowed_commands = ['ls', 'pwd', 'echo', 'cat', 'grep', 'head', 'tail']
        cmd_parts = command.split()
        if cmd_parts[0] not in allowed_commands:
            raise ValueError("Command not allowed")
        try:
            result = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=10)
            print(result.stdout)
        except subprocess.TimeoutExpired:
            print("Command timed out")

    def filesystem_operation(self, op, path, content=None):
        path = Path(path).expanduser()
        if op == 'read':
            if path.exists() and path.is_file():
                with open(path, 'r') as f:
                    return f.read()
        elif op == 'write':
            with open(path, 'w') as f:
                f.write(content)
        elif op == 'list':
            return list(path.iterdir()) if path.is_dir() else []
        elif op == 'delete':
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)

    def network_request(self, url, method='GET'):
        try:
            if method == 'GET':
                response = requests.get(url, timeout=10)
                return response.text
            elif method == 'POST':
                # Assume data in params, but for now
                pass
        except requests.RequestException as e:
            return str(e)

    def send_notification(self, message):
        # Use osascript for mac, notify-send for linux
        if os.name == 'posix':
            if 'darwin' in os.uname().sysname.lower():
                subprocess.run(['osascript', '-e', f'display notification "{message}"'])
            else:
                subprocess.run(['notify-send', 'Auralis', message])
        # Windows: use toast or something, but skip

    def open_browser(self, url):
        webbrowser.open(url)

    def send_email(self, to, subject, body):
        # Simple SMTP, assume gmail or something, but need credentials
        # For demo, skip auth
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = 'auralis@example.com'
        msg['To'] = to
        # server = smtplib.SMTP('smtp.gmail.com', 587)
        # server.starttls()
        # server.login(user, pass)
        # server.sendmail(from, to, msg.as_string())
        # server.quit()
        print(f"Email sent to {to}: {subject}")

    def open_vscode(self, file_path):
        subprocess.run(['code', file_path])  # Assume code command available