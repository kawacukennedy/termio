import pyautogui
import platform

class ScreenControlModule:
    def __init__(self):
        pyautogui.FAILSAFE = True
        self.system = platform.system()

    def type_text(self, text):
        pyautogui.typewrite(text)

    def click_at(self, x, y):
        pyautogui.click(x, y)

    def move_to(self, x, y):
        pyautogui.moveTo(x, y)

    def scroll(self, direction, clicks=3):
        if direction == 'up':
            pyautogui.scroll(clicks)
        elif direction == 'down':
            pyautogui.scroll(-clicks)

    def press_key(self, key):
        pyautogui.press(key)

    def close_window(self):
        if self.system == 'Darwin':  # macOS
            pyautogui.hotkey('command', 'w')
        else:  # Windows/Linux
            pyautogui.hotkey('alt', 'f4')

    def open_application(self, app):
        import subprocess
        if self.system == 'Windows':
            subprocess.run(['start', app], shell=True)
        elif self.system == 'Darwin':  # macOS
            subprocess.run(['open', app])
        else:  # Linux
            subprocess.run([app])

    def run_script(self, command):
        import subprocess
        subprocess.run(command, shell=True)

    def drag_drop(self, x1, y1, x2, y2):
        pyautogui.moveTo(x1, y1)
        pyautogui.dragTo(x2, y2, duration=0.5)