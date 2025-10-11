try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("Warning: pyautogui not available. Screen control will not work.")

import time

class ScreenControlModule:
    def __init__(self, config):
        self.config = config
        self.capabilities = config['screen_interaction']['screen_control']['capabilities']
        if PYAUTOGUI_AVAILABLE:
            pyautogui.FAILSAFE = True

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

    def confirm_action(self, action_description):
        # For now, assume confirmation is given
        return True