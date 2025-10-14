#!/usr/bin/env python3
"""
UI Worker as per microarchitecture spec.
Handles terminal HUD rendering, waveform animation, status bar.
"""

import time
import logging
from ux_flow_manager import UXFlowManager

class UIWorker:
    def __init__(self, config, queues):
        self.config = config
        self.queues = queues
        self.logger = logging.getLogger('ui_worker')

        self.ux = UXFlowManager(config)
        self.running = True

        # Failure mode flags
        self.display_failed = False
        self.keyboard_monitor_failed = False
        self.tts_failed = False
        self.ui_interaction_failed = False

    def run(self):
        """Main UI worker loop"""
        self.logger.info("UI worker starting...")

        try:
            # Show boot sequence
            self.ux.show_boot_sequence()

            # Show idle screen
            self.ux.show_idle_screen()
        except Exception as e:
            self.logger.error(f"UI initialization failed: {e}")
            self.display_failed = True
            # Continue running in headless mode
            self.logger.info("Running in headless mode due to display failure")

        # TTS state
        self.tts_active = False
        self.tts_interrupt = False

        # Start interrupt monitoring
        try:
            self._start_interrupt_monitor()
        except Exception as e:
            self.logger.error(f"Interrupt monitoring failed: {e}")
            self.keyboard_monitor_failed = True

        consecutive_failures = 0
        max_consecutive_failures = 5

        while self.running:
            try:
                # Check for audio events
                if not self.queues['audio->stt'].empty():
                    message = self.queues['audio->stt'].get(timeout=1)

                    if message['type'] == 'ptt_start':
                        self._handle_ptt_start()
                    elif message['type'] == 'ptt_end':
                        self._handle_ptt_end()
                    elif message['type'] == 'wakeword_detected':
                        self._handle_wakeword_detected()
                    elif message['type'] == 'interrupt_tts':
                        self._interrupt_tts()
                    elif message['type'] == 'status_update':
                        self._handle_status_update(message)

                # Check for TTS responses to display
                if not self.queues['nlp->tts'].empty():
                    message = self.queues['nlp->tts'].get(timeout=1)

                    if message['type'] == 'response':
                        self._display_response(message)
                    elif message['type'] == 'error':
                        self._handle_error(message)
                    elif message['type'] == 'status_update':
                        self._handle_status_update(message)

                consecutive_failures = 0  # Reset on successful iteration
                time.sleep(0.01)

            except Exception as e:
                self.logger.error(f"UI worker error: {e}")
                consecutive_failures += 1

                if consecutive_failures >= max_consecutive_failures:
                    self.logger.error("UI worker failed repeatedly, entering degraded mode")
                    self.ui_interaction_failed = True
                    # Continue running but with minimal functionality
                    time.sleep(1)  # Slow down error loop
                else:
                    time.sleep(0.1)

    def _handle_ptt_start(self):
        """Handle PTT start with spec-compliant UI feedback"""
        # 0-20ms: status_bar.mic set ON; small click sound
        self.ux.update_status('mic_status', 'ON')
        print('\a', end='', flush=True)  # Small click sound

        # 20-60ms: waveform activates; label 'LISTENING...'
        time.sleep(0.02)  # Wait 20ms
        self.ux.start_waveform()
        self.ux.update_status('last_action_summary', 'LISTENING...')

    def _handle_ptt_end(self):
        """Handle PTT end with transcribing feedback"""
        # Stop waveform
        self.ux.stop_waveform()

        # Show 'TRANSCRIBING...' with spinner
        self.ux.update_status('mic_status', 'PROCESSING')
        self.ux.update_status('last_action_summary', 'TRANSCRIBING...')

        # Start spinner animation
        self._show_transcribing_spinner()

    def _show_transcribing_spinner(self):
        """Show 3-dot spinner animation at 250ms cadence"""
        import threading
        def spinner():
            dots = ['.', '..', '...']
            idx = 0
            while self.ux.status_bar.get('mic_status') == 'PROCESSING':
                self.ux.update_status('last_action_summary', f'TRANSCRIBING{dots[idx]}')
                idx = (idx + 1) % len(dots)
                time.sleep(0.25)  # 250ms cadence

        thread = threading.Thread(target=spinner, daemon=True)
        thread.start()

    def _display_response(self, message):
        """Display AI response in the UI with TTS playback"""
        response_text = message.get('text', '')
        mode = message.get('mode', 'offline')

        # Update status
        self.ux.update_status('mic_status', 'OFF')
        self.ux.update_status('network_status', mode)
        self.ux.update_status('last_action_summary', f'Response ({mode})')

        # Add to scrollback
        self.ux.add_to_scrollback(f"Auralis: {response_text}")

        # TTS playback behavior
        self._play_tts_response(response_text)

    def _play_tts_response(self, text):
        """Play TTS response with preview and interrupt handling"""
        if self.display_failed:
            # Skip UI updates in headless mode
            pass
        else:
            # Before play: display preview text (first 2 lines)
            lines = text.split('\n')[:2]
            preview = '\n'.join(lines)
            try:
                self.ux.add_to_scrollback(f"[Speaking] {preview}...")
            except Exception as e:
                self.logger.error(f"UI update failed: {e}")

        # Start TTS playback
        self.tts_active = True
        self.tts_interrupt = False

        try:
            # Import TTS module (would be from tts_offline or tts_hf)
            # For now, simulate TTS playback
            import threading

            def tts_playback():
                try:
                    self.logger.info(f"TTS: {text}")

                    # Simulate TTS timing (rough estimate: 150 words per minute)
                    words = len(text.split())
                    duration_sec = max(1, words / 2.5)  # ~150 wpm

                    start_time = time.time()
                    while time.time() - start_time < duration_sec and not self.tts_interrupt:
                        # Could implement text highlighting here
                        time.sleep(0.1)

                    if self.tts_interrupt:
                        self.logger.info("TTS interrupted")
                    else:
                        self.logger.info("TTS completed")

                except Exception as e:
                    self.logger.error(f"TTS playback error: {e}")
                    self.tts_failed = True
                finally:
                    self.tts_active = False

            # Start TTS in background
            tts_thread = threading.Thread(target=tts_playback, daemon=True)
            tts_thread.start()

        except Exception as e:
            self.logger.error(f"TTS initialization error: {e}")
            self.tts_active = False
            self.tts_failed = True

    def _interrupt_tts(self):
        """Interrupt TTS playback with fadeout"""
        if self.tts_active:
            self.tts_interrupt = True
            # Fadeout would happen in actual TTS implementation
            time.sleep(0.05)  # 50-100ms fadeout
            self.tts_active = False
            self.ux.update_status('last_action_summary', 'TTS interrupted')

    def _start_interrupt_monitor(self):
        """Monitor for TTS interrupt commands"""
        import threading

        def monitor_interrupts():
            try:
                import keyboard

                # Monitor for SPACE or 'stop' word
                def on_space_press():
                    if self.tts_active:
                        self.queues['audio->stt'].put({
                            'type': 'interrupt_tts',
                            'timestamp': time.time()
                        })

                keyboard.on_press_key('space', lambda _: on_space_press())

                # For 'stop' word detection, we'd need STT integration
                # For now, just keyboard interrupt

                keyboard.wait()  # Keep thread alive

            except ImportError:
                self.logger.warning("keyboard module not available, TTS interrupt disabled")
            except OSError as e:
                if "administrator" in str(e).lower():
                    self.logger.warning("Keyboard monitoring requires accessibility permissions on macOS. TTS interrupt disabled.")
                    self.keyboard_monitor_failed = True
                else:
                    self.logger.error(f"Keyboard monitoring error: {e}")
                    self.keyboard_monitor_failed = True
            except Exception as e:
                self.logger.error(f"Interrupt monitoring failed: {e}")
                self.keyboard_monitor_failed = True

        thread = threading.Thread(target=monitor_interrupts, daemon=True)
        thread.start()

    def _handle_error(self, message):
        """Handle errors with spec-compliant messages"""
        error_type = message.get('error', 'unknown')

        if error_type == 'stt_fail':
            # Display 'Speech unclear. Repeat?' and offer 'retry' key
            self.ux.add_to_scrollback("Speech unclear. Repeat?")
            self.ux.update_status('last_action_summary', 'Speech unclear - Press R to retry')

            # Wait for retry key
            import threading
            def wait_for_retry():
                try:
                    import keyboard
                    keyboard.wait('r')  # Wait for 'r' key
                    # Retry - this would trigger PTT again
                    self.logger.info("Retry requested")
                except ImportError:
                    pass

        thread = threading.Thread(target=wait_for_retry, daemon=True)
        thread.start()

        self.ux.update_status('mic_status', 'OFF')

    def _handle_wakeword_detected(self):
        """Handle wakeword detection UI feedback"""
        if self.display_failed:
            return

        try:
            # Status 'LISTENING (wakeword)' - already set by audio worker
            self.ux.update_status('last_action_summary', 'LISTENING (wakeword)')
            self.ux.start_waveform()
        except Exception as e:
            self.logger.error(f"Wakeword UI update failed: {e}")
            self.ui_interaction_failed = True

    def _handle_status_update(self, message):
        """Handle status update messages from other workers"""
        if self.display_failed:
            return

        try:
            status_type = message.get('message', '')
            mode = message.get('mode', '')

            if 'offline' in status_type.lower():
                self.ux.update_status('network_status', 'OFFLINE')
            elif 'network unavailable' in status_type.lower():
                self.ux.update_status('network_status', 'OFFLINE')
            elif 'text input mode' in status_type.lower():
                self.ux.update_status('mic_status', 'TEXT_ONLY')

            self.ux.update_status('last_action_summary', status_type)
        except Exception as e:
            self.logger.error(f"Status update failed: {e}")
            self.ui_interaction_failed = True