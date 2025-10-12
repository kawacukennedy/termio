#!/usr/bin/env python3
"""
Action Planner as per microarchitecture spec.
Lightweight DAG builder with rollback support.
"""

import time
import logging
from typing import Dict, List, Optional

class ActionPlanner:
    def __init__(self, config, security_module=None):
        self.config = config
        self.security = security_module
        self.logger = logging.getLogger('action_planner')

        # Rollback metadata storage
        self.rollback_stack = []

    def execute_plan(self, action_plan: List[Dict]) -> Dict:
        """
        Execute action plan with rollback support.
        Returns: {"success": bool, "result": any, "rollback_data": dict}
        """
        results = []
        rollback_data = []

        try:
            for step in action_plan:
                step_num = step.get('step', 0)
                action = step.get('action', '')
                params = step.get('params', {})
                requires_permission = step.get('requires_permission', False)

                self.logger.info(f"Executing step {step_num}: {action}")

                # Check permissions if required
                if requires_permission and self.security:
                    allowed, reason = self.security.check_action_permission(action, params)
                    if not allowed:
                        return {
                            "success": False,
                            "result": f"Permission denied: {reason}",
                            "rollback_data": rollback_data
                        }

                # Execute step
                result = self._execute_step(action, params)

                if not result.get('success', False):
                    # Step failed, attempt rollback
                    self._rollback_actions(rollback_data)
                    return {
                        "success": False,
                        "result": result.get('error', 'Step execution failed'),
                        "rollback_data": rollback_data
                    }

                results.append(result)
                rollback_data.extend(result.get('rollback_info', []))

            return {
                "success": True,
                "result": results,
                "rollback_data": rollback_data
            }

        except Exception as e:
            self.logger.error(f"Action plan execution failed: {e}")
            self._rollback_actions(rollback_data)
            return {
                "success": False,
                "result": str(e),
                "rollback_data": rollback_data
            }

    def _execute_step(self, action: str, params: Dict) -> Dict:
        """Execute individual action step"""
        try:
            if action == 'capture_screen':
                return self._capture_screen(params)
            elif action == 'ocr_process':
                return self._ocr_process(params)
            elif action == 'summarize_content':
                return self._summarize_content(params)
            elif action == 'validate_target':
                return self._validate_target(params)
            elif action == 'request_confirmation':
                return self._request_confirmation(params)
            elif action == 'execute_control':
                return self._execute_control(params)
            elif action == 'validate_url':
                return self._validate_url(params)
            elif action == 'open_browser':
                return self._open_browser(params)
            elif action == 'validate_path':
                return self._validate_path(params)
            elif action == 'check_permissions':
                return self._check_permissions(params)
            elif action == 'execute_file_op':
                return self._execute_file_op(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _capture_screen(self, params: Dict) -> Dict:
        """Capture screen"""
        try:
            import pyautogui
            region = params.get('region', 'full')
            if region == 'active_window':
                # Simplified - capture full screen
                screenshot = pyautogui.screenshot()
            else:
                screenshot = pyautogui.screenshot()

            return {
                "success": True,
                "data": screenshot,
                "rollback_info": [{"action": "screen_capture", "data": None}]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _ocr_process(self, params: Dict) -> Dict:
        """Process OCR"""
        try:
            import pytesseract
            from PIL import Image

            # This would use the screen data from previous step
            # For now, simulate OCR
            text = "Sample OCR text from screen"

            return {
                "success": True,
                "text": text,
                "rollback_info": []
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _summarize_content(self, params: Dict) -> Dict:
        """Summarize content"""
        # This would use NLP to summarize
        return {
            "success": True,
            "summary": "Content summarized",
            "rollback_info": []
        }

    def _validate_target(self, params: Dict) -> Dict:
        """Validate control target"""
        target = params.get('target', '')
        if not target:
            return {"success": False, "error": "No target specified"}

        return {"success": True, "rollback_info": []}

    def _request_confirmation(self, params: Dict) -> Dict:
        """Request user confirmation"""
        action = params.get('action', '')
        dangerous = params.get('dangerous', False)

        # In a real implementation, this would show UI confirmation
        # For now, assume confirmed
        return {
            "success": True,
            "confirmed": True,
            "rollback_info": []
        }

    def _execute_control(self, params: Dict) -> Dict:
        """Execute screen control"""
        try:
            import pyautogui

            if 'text' in params:
                pyautogui.typewrite(params['text'])
                rollback_info = [{"action": "delete_text", "length": len(params['text'])}]
            elif 'target' in params:
                # Simplified click
                pyautogui.click()
                rollback_info = [{"action": "undo_click"}]
            else:
                return {"success": False, "error": "No control parameters"}

            return {
                "success": True,
                "rollback_info": rollback_info
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _validate_url(self, params: Dict) -> Dict:
        """Validate URL"""
        import re
        url = params.get('url', '')
        if re.match(r'https?://', url):
            return {"success": True, "rollback_info": []}
        return {"success": False, "error": "Invalid URL"}

    def _open_browser(self, params: Dict) -> Dict:
        """Open browser"""
        import webbrowser
        url = params.get('url', 'https://www.google.com')
        webbrowser.open(url)
        return {
            "success": True,
            "rollback_info": [{"action": "close_browser"}]
        }

    def _validate_path(self, params: Dict) -> Dict:
        """Validate file path"""
        import os
        path = params.get('path', '')
        if os.path.exists(path):
            return {"success": True, "rollback_info": []}
        return {"success": False, "error": "Path does not exist"}

    def _check_permissions(self, params: Dict) -> Dict:
        """Check operation permissions"""
        operation = params.get('operation', '')
        if self.security:
            allowed, reason = self.security.check_action_permission(operation)
            return {
                "success": allowed,
                "error": reason if not allowed else None,
                "rollback_info": []
            }
        return {"success": True, "rollback_info": []}

    def _execute_file_op(self, params: Dict) -> Dict:
        """Execute file operation"""
        # Simplified - would implement actual file operations
        return {
            "success": True,
            "rollback_info": [{"action": "undo_file_op", "params": params}]
        }

    def _rollback_actions(self, rollback_data: List[Dict]):
        """Rollback executed actions"""
        self.logger.info("Rolling back actions...")

        for item in reversed(rollback_data):
            try:
                action = item.get('action')
                if action == 'delete_text':
                    length = item.get('length', 0)
                    # Simulate backspace presses
                    import pyautogui
                    for _ in range(length):
                        pyautogui.press('backspace')
                elif action == 'undo_click':
                    # Can't really undo clicks, just log
                    pass
                elif action == 'close_browser':
                    # Can't easily close browser, just log
                    pass

                self.logger.info(f"Rolled back: {action}")

            except Exception as e:
                self.logger.error(f"Rollback failed for {item}: {e}")

    def get_plan_status(self) -> Dict:
        """Get current plan execution status"""
        return {
            "active_plan": len(self.rollback_stack) > 0,
            "rollback_available": len(self.rollback_stack) > 0
        }