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

        # Screen control
        self.screen_control_available = False
        try:
            import pyautogui
            self.screen_control_available = True
        except ImportError:
            self.logger.warning("pyautogui not available, screen control disabled")

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
        """Execute screen control action"""
        if not self.screen_control_available:
            return "Screen control not available"

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

        except Exception as e:
            self.logger.error(f"Screen action error: {e}")
            return f"Screen action failed: {e}"

    def execute_shell_command(self, command, sandboxed=True):
        """Execute shell command in sandboxed mode"""
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
                return f"Command failed: {result.stderr.strip()}"

        except subprocess.TimeoutExpired:
            return "Command timed out"
        except Exception as e:
            return f"Command execution error: {e}"

    def confirm_destructive_action(self, action_description):
        """Get user confirmation for destructive actions"""
        # This would show a confirmation dialog
        # For now, always deny for safety
        self.logger.warning(f"Destructive action blocked: {action_description}")
        return False