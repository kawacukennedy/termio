try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("Warning: pyautogui not available. Screen control will not work.")

import time
import hashlib
import json
import logging

class ScreenControlModule:
    def __init__(self, config):
        self.config = config
        self.capabilities = config['screen_interaction']['screen_control']['capabilities']
        self.logger = logging.getLogger('screen_control')
        self.security = None  # Will be set by caller

        if PYAUTOGUI_AVAILABLE:
            pyautogui.FAILSAFE = True

        # Audit logging
        self.audit_log = []

    def initialize(self):
        if PYAUTOGUI_AVAILABLE:
            pyautogui.PAUSE = 0.1  # Small pause between actions

    def click(self, x, y, button='left'):
        if not PYAUTOGUI_AVAILABLE:
            return False
        pyautogui.click(x, y, button=button)
        return True

    def move_mouse(self, x, y):
        if not PYAUTOGUI_AVAILABLE:
            return False
        pyautogui.moveTo(x, y)
        return True

    def drag_drop(self, start_x, start_y, end_x, end_y):
        if not PYAUTOGUI_AVAILABLE:
            return False
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=0.5)
        return True

    def type_text(self, text):
        if not PYAUTOGUI_AVAILABLE:
            return False
        pyautogui.typewrite(text)
        return True

    def press_key(self, key):
        if not PYAUTOGUI_AVAILABLE:
            return False
        pyautogui.press(key)
        return True

    def window_management(self, action, window_title=None):
        if not PYAUTOGUI_AVAILABLE:
            return False
        if action == 'close':
            pyautogui.hotkey('alt', 'f4')
        elif action == 'minimize':
            pyautogui.hotkey('alt', 'space', 'n')
        # Add more as needed
        return True

    def execute_with_confirmation(self, action_func, action_name, params=None, dangerous=False):
        """Execute action with spec-compliant confirmation flow"""
        params = params or {}

        # Before execution: display short overlay + voice 'Confirm? Y/N' + 5s timeout
        confirmed = self._get_user_confirmation(f"Execute {action_name}?", dangerous=dangerous)

        if not confirmed:
            return False, "Action cancelled by user"

        # Execute action
        try:
            result = action_func(**params)

            # Audit logging
            self._audit_action(action_name, params, success=True)

            return True, "Action executed successfully"

        except Exception as e:
            self._audit_action(action_name, params, success=False, error=str(e))
            return False, f"Action failed: {e}"

    def _get_user_confirmation(self, prompt, dangerous=False):
        """Get user confirmation as per spec"""
        print(f"\n🖱️  {prompt}")

        if dangerous:
            # Dangerous actions require typed confirmation
            print("This is a dangerous action. Type 'CONFIRM' to proceed:")
            response = input("> ").strip()
            return response.upper() == 'CONFIRM'
        else:
            # Non-dangerous: Y/N with 5s timeout
            print("Press Y to confirm, N to cancel (5s timeout):")
            import threading

            confirmed = [False]
            cancelled = [False]

            def wait_for_input():
                try:
                    response = input("> ").strip().lower()
                    if response in ['y', 'yes']:
                        confirmed[0] = True
                    else:
                        cancelled[0] = True
                except:
                    cancelled[0] = True

            input_thread = threading.Thread(target=wait_for_input, daemon=True)
            input_thread.start()

            # Wait up to 5 seconds
            input_thread.join(timeout=5)

            if confirmed[0]:
                return True
            elif cancelled[0]:
                return False
            else:
                print("Timeout - action cancelled")
                return False

    def _audit_action(self, action_name, params, success=True, error=None):
        """Audit logging with action hash and undo metadata"""
        action_data = {
            'timestamp': time.time(),
            'action': action_name,
            'params': params,
            'success': success,
            'error': error
        }

        # Create action hash
        action_str = json.dumps(action_data, sort_keys=True)
        action_hash = hashlib.sha256(action_str.encode()).hexdigest()
        action_data['hash'] = action_hash

        # Store undo metadata (simplified)
        action_data['undo_metadata'] = self._generate_undo_metadata(action_name, params)

        # Log to audit log
        self.audit_log.append(action_data)

        # Keep only last 100 actions
        if len(self.audit_log) > 100:
            self.audit_log.pop(0)

        self.logger.info(f"Action audited: {action_name} (hash: {action_hash[:8]})")

    def _generate_undo_metadata(self, action_name, params):
        """Generate undo metadata for actions"""
        # Simplified undo metadata
        if action_name == 'click':
            return {'type': 'mouse_move', 'x': params.get('x'), 'y': params.get('y')}
        elif action_name == 'type_text':
            return {'type': 'delete_text', 'length': len(params.get('text', ''))}
        else:
            return {'type': 'unknown'}

    def get_audit_log(self, limit=10):
        """Get recent audit log entries"""
        return self.audit_log[-limit:]

    def undo_last_action(self):
        """Undo the last action using stored metadata"""
        if not self.audit_log:
            return False, "No actions to undo"

        last_action = self.audit_log[-1]
        undo_meta = last_action.get('undo_metadata', {})

        if undo_meta['type'] == 'mouse_move':
            self.move_mouse(undo_meta['x'], undo_meta['y'])
            return True, "Mouse position restored"
        elif undo_meta['type'] == 'delete_text':
            # Simulate backspace presses
            for _ in range(undo_meta['length']):
                pyautogui.press('backspace')
            return True, "Text deleted"

        return False, "Cannot undo this action"

    # Enhanced action methods with confirmation
    def click_with_confirm(self, x, y, button='left'):
        """Click with confirmation"""
        return self.execute_with_confirmation(
            self.click, 'click', {'x': x, 'y': y, 'button': button}
        )

    def type_text_with_confirm(self, text):
        """Type text with confirmation"""
        return self.execute_with_confirmation(
            self.type_text, 'type_text', {'text': text}
        )

    def window_close_with_confirm(self):
        """Close window with confirmation (dangerous action)"""
        return self.execute_with_confirmation(
            lambda: self.window_management('close'), 'close_window', dangerous=True
        )