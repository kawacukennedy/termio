import time
import threading
import sys
import os

class UXFlowManager:
    def __init__(self, config):
        self.config = config
        self.status_bar = {}
        self.thinking_dots = 0

    def show_boot_sequence(self):
        for frame in self.config['terminal_ui_ux']['boot_sequence']:
            print(frame)
            time.sleep(0.5)

    def show_idle_screen(self):
        hint = self.config['terminal_ui_ux']['idle_screen']['hint_text']
        print(f"\n{hint}")
        # Start pulse animation in background thread
        self.idle_thread = threading.Thread(target=self._pulse_animation, daemon=True)
        self.idle_thread.start()

    def _pulse_animation(self):
        while True:
            print(".", end="", flush=True)
            time.sleep(2)
            print("\b \b", end="", flush=True)
            time.sleep(2)

    def show_status_bar(self):
        elements = self.config['terminal_ui_ux']['visual_feedback']['status_bar_elements']
        status = []
        for elem in elements:
            if elem in self.status_bar:
                status.append(f"{elem}: {self.status_bar[elem]}")
        print(" | ".join(status))

    def update_status(self, key, value):
        self.status_bar[key] = value
        self.show_status_bar()

    def show_ascii_waveform(self, amplitude=5, duration=2):
        """Show animated ASCII waveform for duration seconds"""
        import time
        start_time = time.time()
        while time.time() - start_time < duration:
            # Generate waveform
            waveform = ""
            for i in range(amplitude):
                waveform += "~" * (amplitude - i) + " " * i + "\n"
            print(waveform, end="", flush=True)
            time.sleep(0.1)
            # Clear
            print("\033[F" * amplitude, end="")  # Move cursor up
        # Clear final waveform
        print(" " * (amplitude * amplitude))

    def show_thinking_animation(self):
        dots = "." * ((self.thinking_dots % 3) + 1)
        print(f"Thinking{dots}", end="\r", flush=True)
        self.thinking_dots += 1

    def stop_thinking_animation(self):
        print(" " * 20, end="\r", flush=True)
        self.thinking_dots = 0

    def show_error_message(self, error_type):
        messages = {
            "misheard_voice": "Sorry, I didn't catch that. Could you repeat?",
            "unknown_command": "I'm not sure how to help with that.",
            "ocr_failure": "Unable to read the screen content.",
            "action_denied": "Action denied for security reasons."
        }
        print(messages.get(error_type, "An error occurred."))