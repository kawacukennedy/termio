import time
import threading
import sys
import os

class UXFlowManager:
    def __init__(self, config):
        self.config = config
        self.status_bar = {}
        self.thinking_dots = 0
        self.conversation_mode = 'push_to_talk'  # or 'continuous'
        self.voice_active = False
        self.memory_module = None

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

    def start_voice_conversation(self, stt_module, nlp_module, tts_module, wake_word_module=None, memory_module=None):
        """Start voice conversation loop"""
        print("🎤 Voice conversation started. Say 'exit' or 'quit' to stop.")

        self.memory_module = memory_module
        self.voice_active = True
        self.update_status('mode', 'VOICE')

        try:
            while self.voice_active:
                # Wake word detection if available
                if wake_word_module and self.conversation_mode == 'continuous':
                    if wake_word_module.detect_wake_word():
                        print("🎯 Wake word detected!")
                    else:
                        continue

                # Get speech input
                if self.conversation_mode == 'push_to_talk':
                    user_input = stt_module.transcribe_push_to_talk()
                else:
                    user_input = stt_module.transcribe(duration=3)

                if not user_input:
                    continue

                print(f"You: {user_input}")

                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'stop', 'goodbye']:
                    response = "Goodbye! Have a great day."
                    tts_module.speak(response)
                    if self.memory_module:
                        self.memory_module.add_turn(user_input, response)
                    break

                # Show thinking animation
                self.show_thinking_animation()

                # Generate response
                intent, entities = nlp_module.get_intent_and_entities(user_input)

                if intent == 'command':
                    # Handle commands
                    response = self.process_voice_command(user_input, entities)
                else:
                    # Generate conversational response
                    response = nlp_module.generate_contextual_response(user_input)

                # Validate response
                if not nlp_module.validate_response(response):
                    response = nlp_module.generate_fallback_response(user_input)

                print(f"Auralis: {response}")

                # Speak response
                tts_module.speak(response)

                # Store in memory
                if self.memory_module:
                    self.memory_module.add_turn(user_input, response)

        except KeyboardInterrupt:
            print("\n🛑 Voice conversation interrupted")
        except Exception as e:
            print(f"❌ Voice conversation error: {e}")
        finally:
            self.voice_active = False
            self.update_status('mode', 'IDLE')

    def process_voice_command(self, command, entities):
        """Process voice commands"""
        command_lower = command.lower()

        # Basic command handling
        if 'time' in command_lower:
            from datetime import datetime
            current_time = datetime.now().strftime("%I:%M %p")
            return f"The current time is {current_time}"

        elif 'date' in command_lower:
            from datetime import datetime
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            return f"Today is {current_date}"

        elif 'weather' in command_lower:
            # Would integrate with external API
            return "I'd need to check the weather service for current conditions."

        elif 'reminder' in command_lower or 'remind' in command_lower:
            # Would integrate with automation
            return "I'll help you set a reminder."

        elif 'joke' in command_lower:
            # Would integrate with external API
            return "Why don't scientists trust atoms? Because they make up everything!"

        else:
            return "I'm not sure how to handle that command. Can you try rephrasing?"

    def show_thinking_animation(self):
        """Show thinking animation during processing"""
        import time
        dots = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        for _ in range(10):  # ~1 second
            for dot in dots:
                print(f"\r🤔 Thinking {dot}", end="", flush=True)
                time.sleep(0.05)
        print("\r" + " " * 20 + "\r", end="", flush=True)  # Clear line

    def toggle_conversation_mode(self):
        """Toggle between push-to-talk and continuous mode"""
        if self.conversation_mode == 'push_to_talk':
            self.conversation_mode = 'continuous'
            mode_text = 'continuous'
        else:
            self.conversation_mode = 'push_to_talk'
            mode_text = 'push-to-talk'

        self.update_status('voice_mode', mode_text)
        return f"Voice mode switched to {mode_text}"

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