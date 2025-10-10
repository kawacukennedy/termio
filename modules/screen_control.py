import pyautogui
import time

class ScreenControlModule:
    def __init__(self, config):
        self.config = config
        self.capabilities = config['screen_interaction']['screen_control']['capabilities']
        pyautogui.FAILSAFE = True

    def initialize(self):
        pyautogui.PAUSE = 0.1  # Small pause between actions

    def click(self, x, y, button='left'):
        pyautogui.click(x, y, button=button)

    def move_mouse(self, x, y):
        pyautogui.moveTo(x, y)

    def drag_drop(self, start_x, start_y, end_x, end_y):
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=0.5)

    def type_text(self, text):
        pyautogui.typewrite(text)

    def press_key(self, key):
        pyautogui.press(key)

    def window_management(self, action, window_title=None):
        if action == 'close':
            pyautogui.hotkey('alt', 'f4')
        elif action == 'minimize':
            pyautogui.hotkey('alt', 'space', 'n')
        # Add more as needed

    def confirm_action(self, action_description):
        # For now, assume confirmation is given
        return True