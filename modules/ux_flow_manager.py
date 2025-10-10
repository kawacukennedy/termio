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
        """Cinematic boot sequence with enhanced visuals"""
        print("🚀 Initializing Auralis...\n")

        boot_frames = self.config['terminal_ui_ux']['boot_sequence']

        for i, frame in enumerate(boot_frames):
            print(frame)

            # Add visual effects
            if i == 0:
                self.show_pulse_animation(2)
            elif i == len(boot_frames) - 1:
                print("✨ Ready!")
                self.show_success_animation()

            time.sleep(0.8)

        print("\n" + "="*50)

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

    def update_performance_status(self, performance_module):
        """Update status bar with real-time performance metrics"""
        perf_display = performance_module.format_status_display()
        self.update_status('performance', perf_display)

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

    def show_pulse_animation(self, duration=2):
        """Show a pulsing animation"""
        start_time = time.time()
        while time.time() - start_time < duration:
            for intensity in [".", "o", "O", "o", "."]:
                print(f"\r{intensity}", end="", flush=True)
                time.sleep(0.1)
        print("\r ", end="\r")  # Clear

    def show_success_animation(self):
        """Show success animation"""
        success_chars = ["✓", "✔", "✅"]
        for char in success_chars:
            print(f"\r{char}", end="", flush=True)
            time.sleep(0.2)
        print()

    def show_error_message(self, error_type):
        messages = {
            "misheard_voice": "Sorry, I didn't catch that. Could you repeat?",
            "unknown_command": "I'm not sure how to help with that.",
            "ocr_failure": "Unable to read the screen content.",
            "action_denied": "Action denied for security reasons."
        }
        error_msg = messages.get(error_type, "An error occurred.")
        print(f"❌ {error_msg}")

    def show_conversation_flow(self, user_input, ai_response):
        """Show cinematic conversation flow"""
        print(f"\n👤 {user_input}")
        self.show_thinking_animation()
        self.stop_thinking_animation()
        print(f"🤖 {ai_response}")
        print("-" * 40)