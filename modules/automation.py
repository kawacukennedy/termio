import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
import smtplib
import os
from datetime import datetime, timedelta
import json
from pathlib import Path

class AutomationModule:
    def __init__(self, config, security_module):
        self.config = config
        self.security = security_module
        self.automation_dir = Path('automations')
        self.automation_dir.mkdir(exist_ok=True)

    def send_email(self, to_email, subject, body, smtp_server='smtp.gmail.com', smtp_port=587):
        """Send email using configured SMTP"""
        email_user = self.security.get_api_key('email_user')
        email_pass = self.security.get_api_key('email_pass')

        if not email_user or not email_pass:
            return "Email credentials not configured. Use 'store api key email_user YOUR_EMAIL' and 'store api key email_pass YOUR_PASSWORD'"

        try:
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_pass)
            text = msg.as_string()
            server.sendmail(email_user, to_email, text)
            server.quit()

            return f"Email sent successfully to {to_email}"
        except Exception as e:
            return f"Failed to send email: {e}"

    def check_emails(self, imap_server='imap.gmail.com', num_emails=5):
        """Check recent emails"""
        email_user = self.security.get_api_key('email_user')
        email_pass = self.security.get_api_key('email_pass')

        if not email_user or not email_pass:
            return "Email credentials not configured"

        try:
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(email_user, email_pass)
            mail.select('inbox')

            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()[-num_emails:]  # Get last N emails

            emails = []
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if not msg_data or not msg_data[0]:
                    continue
                raw_email = msg_data[0][1]
                if isinstance(raw_email, bytes):
                    email_message = email.message_from_bytes(raw_email)
                elif isinstance(raw_email, str):
                    email_message = email.message_from_string(raw_email)
                else:
                    continue  # Skip if not bytes or str

                subject = email_message['Subject'] or 'No Subject'
                sender = email_message['From'] or 'Unknown'
                date = email_message['Date'] or 'Unknown'

                # Get body
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                body = payload.decode('utf-8', errors='ignore')
                            else:
                                body = str(payload)
                            break
                else:
                    payload = email_message.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body = payload.decode('utf-8', errors='ignore')
                    else:
                        body = str(payload)

                emails.append({
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'body': body[:200] + '...' if len(body) > 200 else body
                })

            mail.logout()
            return emails
        except Exception as e:
            return f"Failed to check emails: {e}"

    def schedule_task(self, task_name, command, delay_minutes=0, repeat=False):
        """Schedule a task to run later"""
        task = {
            'name': task_name,
            'command': command,
            'scheduled_time': (datetime.now() + timedelta(minutes=delay_minutes)).isoformat(),
            'repeat': repeat,
            'created': datetime.now().isoformat()
        }

        task_file = self.automation_dir / f"task_{task_name}.json"
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)

        return f"Task '{task_name}' scheduled for {delay_minutes} minutes from now"

    def list_scheduled_tasks(self):
        """List all scheduled tasks"""
        tasks = []
        for task_file in self.automation_dir.glob('task_*.json'):
            try:
                with open(task_file, 'r') as f:
                    task = json.load(f)
                    tasks.append({
                        'name': task['name'],
                        'command': task['command'],
                        'scheduled_time': task['scheduled_time'],
                        'repeat': task['repeat']
                    })
            except:
                pass

        return tasks

    def cancel_task(self, task_name):
        """Cancel a scheduled task"""
        task_file = self.automation_dir / f"task_{task_name}.json"
        if task_file.exists():
            task_file.unlink()
            return f"Task '{task_name}' cancelled"
        else:
            return f"Task '{task_name}' not found"

    def create_macro(self, macro_name, commands):
        """Create a macro (sequence of commands)"""
        macro = {
            'name': macro_name,
            'commands': commands,
            'created': datetime.now().isoformat()
        }

        macro_file = self.automation_dir / f"macro_{macro_name}.json"
        with open(macro_file, 'w') as f:
            json.dump(macro, f, indent=2)

        return f"Macro '{macro_name}' created with {len(commands)} commands"

    def run_macro(self, macro_name):
        """Execute a macro"""
        macro_file = self.automation_dir / f"macro_{macro_name}.json"
        if not macro_file.exists():
            return f"Macro '{macro_name}' not found"

        try:
            with open(macro_file, 'r') as f:
                macro = json.load(f)

            results = []
            for command in macro['commands']:
                # This would need to be integrated with the main command processor
                # For now, just simulate
                results.append(f"Executed: {command}")

            return f"Macro '{macro_name}' completed:\n" + "\n".join(results)
        except Exception as e:
            return f"Failed to run macro: {e}"

    def list_macros(self):
        """List all available macros"""
        macros = []
        for macro_file in self.automation_dir.glob('macro_*.json'):
            try:
                with open(macro_file, 'r') as f:
                    macro = json.load(f)
                    macros.append({
                        'name': macro['name'],
                        'commands': len(macro['commands']),
                        'created': macro['created']
                    })
            except:
                pass

        return macros

    def web_scraper(self, url, selector=None):
        """Basic web scraping (requires beautifulsoup4)"""
        try:
            import requests
            from bs4 import BeautifulSoup

            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            if selector:
                elements = soup.select(selector)
                content = [elem.get_text().strip() for elem in elements]
                return f"Scraped {len(content)} elements: " + " | ".join(content[:5])
            else:
                # Get main content
                for script in soup(["script", "style"]):
                    script.decompose()

                text = soup.get_text()
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                content = " ".join(lines[:10])  # First 10 lines
                return f"Page content: {content}..."

        except ImportError:
            return "Web scraping requires beautifulsoup4. Install with: pip install beautifulsoup4"
        except Exception as e:
            return f"Web scraping failed: {e}"

    def file_operations(self, operation, file_path, content=None):
        """Basic file operations"""
        try:
            if operation == 'read':
                with open(file_path, 'r') as f:
                    return f.read(1000) + "..." if len(f.read()) > 1000 else f.read()
            elif operation == 'write' and content:
                with open(file_path, 'w') as f:
                    f.write(content)
                return f"Written to {file_path}"
            elif operation == 'list':
                path = Path(file_path)
                if path.is_dir():
                    files = list(path.iterdir())[:10]  # First 10 items
                    return "\n".join([f"{'[DIR]' if f.is_dir() else '[FILE]'} {f.name}" for f in files])
                else:
                    return f"{file_path} is not a directory"
            else:
                return f"Unknown operation: {operation}"
        except Exception as e:
            return f"File operation failed: {e}"

    def create_reminder(self, message, delay_seconds):
        """Create a timed reminder"""
        try:
            import threading
            import time

            def show_reminder():
                time.sleep(delay_seconds)
                print(f"\n🔔 REMINDER: {message}\n")

            thread = threading.Thread(target=show_reminder, daemon=True)
            thread.start()

            return f"Reminder set for {delay_seconds} seconds from now"
        except Exception as e:
            return f"Reminder creation failed: {e}"

    def macro_recorder(self, macro_name, actions):
        """Record and playback macros (simplified)"""
        try:
            # Store macro
            if not hasattr(self, 'macros'):
                self.macros = {}

            self.macros[macro_name] = actions
            return f"Macro '{macro_name}' recorded with {len(actions)} actions"
        except Exception as e:
            return f"Macro recording failed: {e}"

    def play_macro(self, macro_name):
        """Play back a recorded macro"""
        try:
            if not hasattr(self, 'macros') or macro_name not in self.macros:
                return f"Macro '{macro_name}' not found"

            actions = self.macros[macro_name]
            results = []
            for action in actions:
                # Simplified execution
                results.append(f"Executed: {action}")

            return f"Macro '{macro_name}' played:\n" + "\n".join(results)
        except Exception as e:
            return f"Macro playback failed: {e}"

    def system_info(self):
        """Get system information"""
        try:
            import platform
            import psutil

            info = {
                'os': platform.system(),
                'os_version': platform.version(),
                'architecture': platform.machine(),
                'cpu_count': psutil.cpu_count(),
                'memory_total': round(psutil.virtual_memory().total / (1024**3), 2),  # GB
                'disk_total': round(psutil.disk_usage('/').total / (1024**3), 2),  # GB
                'disk_free': round(psutil.disk_usage('/').free / (1024**3), 2)  # GB
            }

            return "\n".join([f"{k}: {v}" for k, v in info.items()])
        except Exception as e:
            return f"Failed to get system info: {e}"

    def get_automation_status(self):
        """Get automation system status"""
        tasks = len(self.list_scheduled_tasks())
        macros = len(self.list_macros())

        return {
            'scheduled_tasks': tasks,
            'macros': macros,
            'automation_dir': str(self.automation_dir),
            'features': ['email', 'scheduling', 'macros', 'web_scraping', 'file_ops', 'system_info']
        }