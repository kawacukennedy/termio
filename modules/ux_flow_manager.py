import time
import threading
import sys
import os
import shutil
import psutil

class UXFlowManager:
    def __init__(self, config):
        self.config = config
        self.status_bar = {
            'mic_status': 'OFF',
            'last_action_summary': '',
            'cpu_percent': '0%',
            'mem_mb': '0MB',
            'network_status': 'offline'
        }
        self.thinking_dots = 0
        self.conversation_mode = 'push_to_talk'  # or 'continuous'
        self.voice_active = False
        self.memory_module = None
        self.scrollback = []
        self.max_scrollback = 1000
        self.waveform_active = False
        self.terminal_width = shutil.get_terminal_size().columns
        self.terminal_height = shutil.get_terminal_size().lines

    def update_status(self, key, value):
        """Update status bar element"""
        self.status_bar[key] = value
        self.refresh_hud()

    def refresh_hud(self):
        """Refresh the entire terminal HUD"""
        # Clear screen and move to top
        print("\033[2J\033[H", end="")

        # Get current terminal size
        self.terminal_width = shutil.get_terminal_size().columns
        self.terminal_height = shutil.get_terminal_size().lines

        # Render header
        self._render_header()

        # Render main window (scrollback)
        self._render_main_window()

        # Render waveform row (if active)
        if self.waveform_active:
            self._render_waveform_row()
        else:
            # Empty waveform space
            print("│" + " " * (self.terminal_width - 2) + "│")

        # Render status bar
        self._render_status_bar()

        # Render input prompt
        self._render_input_prompt()

    def _render_header(self):
        """Render header: Auralis • offline | mode/time"""
        app_name = "Auralis"
        mode = self.status_bar.get('network_status', 'offline')
        current_time = time.strftime("%H:%M")

        header_left = f"{app_name} • {mode}"
        header_right = current_time

        # Calculate padding
        total_width = self.terminal_width - 2  # Account for borders
        padding = total_width - len(header_left) - len(header_right)

        header_line = f"┌─ {header_left}{' ' * padding}{header_right} ─┐"
        print(header_line)

    def _render_main_window(self):
        """Render main window with scrollback"""
        content_height = self.terminal_height - 6  # Header + waveform + status + input + borders

        # Get recent scrollback lines
        recent_lines = self.scrollback[-content_height:] if len(self.scrollback) > content_height else self.scrollback

        # Fill with empty lines if needed
        while len(recent_lines) < content_height:
            recent_lines.insert(0, "")

        for line in recent_lines:
            # Wrap long lines
            wrapped_lines = self._wrap_text(line, self.terminal_width - 4)
            for wrapped_line in wrapped_lines:
                print(f"│ {wrapped_line:<{self.terminal_width-4}} │")

    def _render_waveform_row(self):
        """Render ASCII waveform row"""
        waveform_height = 3
        waveform_data = self._generate_waveform_data()

        for i in range(waveform_height):
            line = ""
            for j in range(self.terminal_width - 2):
                if j < len(waveform_data[i]):
                    line += waveform_data[i][j]
                else:
                    line += " "
            print(f"│{line}│")

    def _render_status_bar(self):
        """Render status bar: mic status | last action | cpu%|memMB|net"""
        mic = self.status_bar.get('mic_status', 'OFF')
        action = self.status_bar.get('last_action_summary', '')[:20]  # Truncate
        cpu = self.status_bar.get('cpu_percent', '0%')
        mem = self.status_bar.get('mem_mb', '0MB')
        net = self.status_bar.get('network_status', 'offline')

        left = f"mic:[{mic}]"
        middle = action
        right = f"{cpu}|{mem}|{net}"

        # Calculate padding
        total_width = self.terminal_width - 2
        left_width = len(left)
        right_width = len(right)
        middle_width = total_width - left_width - right_width - 4  # Account for separators

        status_line = f"├─ {left} {middle:<{middle_width}} {right} ─┤"
        print(status_line)

    def _render_input_prompt(self):
        """Render input prompt"""
        placeholder = "Type or hold SPACE to speak..."
        prompt_line = f"└─ {placeholder}{' ' * (self.terminal_width - len(placeholder) - 5)} ─┘"
        print(prompt_line)

    def _wrap_text(self, text, width):
        """Wrap text to fit width"""
        if len(text) <= width:
            return [text]

        lines = []
        while text:
            if len(text) <= width:
                lines.append(text)
                break
            # Find last space within width
            cut = text.rfind(' ', 0, width)
            if cut == -1:
                cut = width
            lines.append(text[:cut])
            text = text[cut:].lstrip()
        return lines

    def _generate_waveform_data(self):
        """Generate ASCII waveform data"""
        # Simple sine wave for demo
        import math
        width = self.terminal_width - 2
        height = 3
        waveform = [[" " for _ in range(width)] for _ in range(height)]

        for x in range(width):
            # Sine wave
            y = int((math.sin(x * 0.2 + time.time()) + 1) * (height - 1) / 2)
            if 0 <= y < height:
                waveform[y][x] = "~"

        return waveform

    def _performance_monitor(self):
        """Monitor and update performance stats"""
        while True:
            try:
                cpu_percent = f"{psutil.cpu_percent()}%"
                mem_mb = f"{int(psutil.virtual_memory().used / 1024 / 1024)}MB"
                self.update_status('cpu_percent', cpu_percent)
                self.update_status('mem_mb', mem_mb)
            except:
                pass
            time.sleep(5)

    def add_to_scrollback(self, text):
        """Add text to scrollback buffer"""
        self.scrollback.append(text)
        if len(self.scrollback) > self.max_scrollback:
            self.scrollback.pop(0)
        self.refresh_hud()

    def start_waveform(self):
        """Start waveform animation"""
        self.waveform_active = True
        self.refresh_hud()

    def stop_waveform(self):
        """Stop waveform animation"""
        self.waveform_active = False
        self.refresh_hud()

    def show_boot_sequence(self):
        """Detailed boot animation sequence as per spec"""
        # Clear screen
        print("\033[2J\033[H", end="")

        boot_frames = [
            {"time_ms": 0, "line": "[*        ] Initializing core processes..."},
            {"time_ms": 200, "line": "[**       ] Loading tiny models (quantized) — 85MB budget..."},
            {"time_ms": 400, "line": "[***      ] Activating voice pipeline (push-to-talk ready)..."},
            {"time_ms": 700, "line": "[****     ] Preparing screen reader & control modules..."},
            {"time_ms": 1000, "line": "[*****    ] Optimizing runtime & CPU budget..."},
            {"time_ms": 1400, "line": "[******   ] Finalizing security tokens & permissions..."},
            {"time_ms": 1800, "line": "[******** ] Auralis ready — Press & hold [SPACE] to talk"}
        ]

        start_time = time.time() * 1000
        for frame in boot_frames:
            # Wait for the specified time
            elapsed = time.time() * 1000 - start_time
            wait_time = (frame["time_ms"] - elapsed) / 1000
            if wait_time > 0:
                time.sleep(wait_time)

            # Clear previous line and print new frame
            print(f"\r{frame['line']}", end="", flush=True)

            # Add sound cues (simulated)
            if frame["time_ms"] == 0:
                print("\a", end="")  # Soft ping
            elif frame["time_ms"] == 1800:
                print("\a\a", end="")  # Chime

        print()  # New line after boot

    def show_idle_screen(self):
        """Show idle screen with HUD"""
        self.add_to_scrollback("Auralis ready — Press & hold [SPACE] to talk")
        # Start performance monitoring
        self.perf_thread = threading.Thread(target=self._performance_monitor, daemon=True)
        self.perf_thread.start()

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

    def start_push_to_talk_flow(self, stt_module, nlp_module, tts_module, memory_module=None):
        """Implement push-to-talk flow as per spec"""
        # Trigger: User holds SPACE
        self.update_status('mic_status', 'ON')
        self.start_waveform()

        # Capture window: 4000ms max
        start_time = time.time()
        user_input = stt_module.transcribe_push_to_talk()

        self.stop_waveform()
        self.update_status('mic_status', 'PROCESSING')

        if user_input:
            self.process_input_flow(user_input, nlp_module, tts_module, memory_module)
        else:
            self.add_to_scrollback("No speech detected")
            self.update_status('last_action_summary', 'No speech detected')

        self.update_status('mic_status', 'OFF')

    def process_input_flow(self, user_input, nlp_module, tts_module, memory_module):
        """Process input through NLP -> TTS flow"""
        self.add_to_scrollback(f"You: {user_input}")

        # NLP processing with latency target
        start_time = time.time()
        response = nlp_module.generate_contextual_response(user_input)
        nlp_time = time.time() - start_time

        # Validate response
        if not nlp_module.validate_response(response):
            response = nlp_module.generate_fallback_response(user_input)

        self.add_to_scrollback(f"Auralis: {response}")
        self.update_status('last_action_summary', f'Response ({nlp_time:.1f}s)')

        # TTS playback
        tts_module.speak(response)

        # Memory
        if memory_module:
            memory_module.add_turn(user_input, response)

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
        self.update_status('last_action_summary', 'Thinking...')
        time.sleep(0.5)  # Brief pause

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
        """Show cinematic conversation flow in scrollback"""
        self.add_to_scrollback(f"You: {user_input}")
        self.show_thinking_animation()
        self.add_to_scrollback(f"Auralis: {ai_response}")
        self.stop_thinking_animation()