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

    def run(self):
        """Main UI worker loop"""
        self.logger.info("UI worker starting...")

        # Show boot sequence
        self.ux.show_boot_sequence()

        # Show idle screen
        self.ux.show_idle_screen()

        while self.running:
            try:
                # Check for TTS responses to display
                if not self.queues['nlp->tts'].empty():
                    message = self.queues['nlp->tts'].get(timeout=1)

                    if message['type'] == 'response':
                        self._display_response(message)

                time.sleep(0.01)

            except Exception as e:
                self.logger.error(f"UI worker error: {e}")
                time.sleep(0.1)

    def _display_response(self, message):
        """Display AI response in the UI"""
        response_text = message.get('text', '')
        mode = message.get('mode', 'offline')

        # Update status
        self.ux.update_status('network_status', mode)
        self.ux.update_status('last_action_summary', f'Response ({mode})')

        # Add to scrollback
        self.ux.add_to_scrollback(f"Auralis: {response_text}")

        # Speak response (this would trigger TTS)
        # For now, just log
        self.logger.info(f"Response: {response_text}")