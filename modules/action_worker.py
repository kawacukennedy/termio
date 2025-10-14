#!/usr/bin/env python3
"""
Action Executor Worker as per microarchitecture spec.
Handles screen control via accessibility APIs, pyautogui actions, sandboxed shell execution.
"""

import time
import logging
import subprocess
import shlex

class ActionWorker:
    def __init__(self, config, queues):
        self.config = config
        self.queues = queues
        self.logger = logging.getLogger('action_worker')
        self.security = None  # Will be set by daemon

        # Screen control
        self.screen_control_available = False
        try:
            import pyautogui
            self.screen_control_available = True
        except ImportError:
            self.logger.warning("pyautogui not available, screen control disabled")

        # Failure mode flags
        self.screen_control_failed = False
        self.shell_execution_failed = False
        self.permission_denied_count = 0
        self.action_timeout_count = 0

    def run(self):
        """Main action worker loop"""
        self.logger.info("Action worker starting...")

        while True:
            try:
                # Check for action requests (this would come from NLP parsing)
                # For now, just sleep
                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Action worker error: {e}")
                time.sleep(0.1)

    def execute_screen_action(self, action, params=None):
        """Execute screen control action with permission checks and failure handling"""
        if not self.screen_control_available:
            self.screen_control_failed = True
            return "Screen control not available"

        # Check permissions
        if self.security:
            allowed, reason = self.security.check_action_permission('screen_control', {'action': action, 'params': params})
            if not allowed:
                self.permission_denied_count += 1
                self.logger.warning(f"Screen action permission denied: {reason}")
                return f"Permission denied: {reason}"

        max_retries = 3
        for attempt in range(max_retries):
            try:
                import pyautogui
                pyautogui.FAILSAFE = True

                if action == 'click':
                    x, y = params.get('x', 0), params.get('y', 0)
                    pyautogui.click(x, y)
                    return "Click executed"

                elif action == 'type':
                    text = params.get('text', '')
                    pyautogui.typewrite(text)
                    return "Text typed"

                elif action == 'scroll':
                    x, y, clicks = params.get('x', 0), params.get('y', 0), params.get('clicks', 1)
                    pyautogui.scroll(clicks, x, y)
                    return "Scroll executed"

                else:
                    return f"Unknown screen action: {action}"

            except pyautogui.FailSafeException:
                self.logger.warning("PyAutoGUI failsafe triggered")
                return "Action cancelled by user (failsafe)"

            except Exception as e:
                self.logger.error(f"Screen action error (attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    self.screen_control_failed = True
                    return f"Screen action failed after {max_retries} attempts: {e}"
                time.sleep(0.5)  # Brief delay before retry

    def execute_shell_command(self, command, sandboxed=True):
        """Execute shell command in sandboxed mode with permission checks and failure handling"""
        # Check permissions for shell execution
        if self.security:
            allowed, reason = self.security.check_action_permission('run_command', {'command': command, 'sandboxed': sandboxed})
            if not allowed:
                self.permission_denied_count += 1
                self.logger.warning(f"Shell command permission denied: {reason}")
                return f"Permission denied: {reason}"

        if sandboxed:
            # Basic sandboxing - restrict to safe commands
            safe_commands = ['ls', 'pwd', 'echo', 'cat', 'head', 'tail', 'grep']

            # Parse command
            try:
                cmd_parts = shlex.split(command)
                if cmd_parts[0] not in safe_commands:
                    return f"Command '{cmd_parts[0]}' not allowed in sandboxed mode"
            except:
                return "Invalid command format"

        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Execute with timeout
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    error_msg = f"Command failed: {result.stderr.strip()}"
                    if attempt == max_retries - 1:
                        self.shell_execution_failed = True
                    return error_msg

            except subprocess.TimeoutExpired:
                self.action_timeout_count += 1
                if attempt == max_retries - 1:
                    self.shell_execution_failed = True
                return "Command timed out"
            except Exception as e:
                self.logger.error(f"Command execution error (attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    self.shell_execution_failed = True
                    return f"Command execution error: {e}"
                time.sleep(0.5)  # Brief delay before retry

    def confirm_destructive_action(self, action_description):
        """Get user confirmation for destructive actions"""
        # This would show a confirmation dialog
        # For now, always deny for safety
        self.logger.warning(f"Destructive action blocked: {action_description}")
        return False

    def get_health_status(self):
        """Get current health status of action worker"""
        status = {
            'screen_control': not self.screen_control_failed,
            'shell_execution': not self.shell_execution_failed,
            'permissions_issues': self.permission_denied_count,
            'timeouts': self.action_timeout_count
        }
        return status

    def reset_failure_flags(self):
        """Reset failure flags (called after successful operations)"""
        self.screen_control_failed = False
        self.shell_execution_failed = False