#!/usr/bin/env python3
"""
Inference Worker as per microarchitecture spec.
Handles TinyGPT local inferencing and on-demand HF request orchestration.
"""

import time
import logging
from nlp_offline import NLPModuleOffline
from nlp_hf import NLPModuleHFAPI

class InferenceWorker:
    def __init__(self, config, queues):
        self.config = config
        self.queues = queues
        self.logger = logging.getLogger('inference_worker')

        # Models
        self.nlp_offline = NLPModuleOffline(config)
        self.nlp_online = None

        # Current mode
        self.current_mode = 'offline'

        # Performance limits
        self.max_concurrent_infers = 1
        self.active_infers = 0

    def run(self):
        """Main inference worker loop"""
        self.logger.info("Inference worker starting...")

        # Initialize models
        self.nlp_offline.initialize()

        while True:
            try:
                # Get input from STT queue
                if not self.queues['stt->nlp'].empty():
                    message = self.queues['stt->nlp'].get(timeout=1)

                    if message['type'] == 'text_input':
                        self._process_text_input(message)
                    elif message['type'] == 'switch_mode':
                        self._switch_mode(message['mode'])
                    elif message['type'] == 'stt_result':
                        self._process_stt_result(message)
                    elif message['type'] == 'fallback_message':
                        self._process_fallback_message(message)

                time.sleep(0.01)  # Small delay to prevent busy loop

            except Exception as e:
                self.logger.error(f"Inference worker error: {e}")
                time.sleep(0.1)

    def _process_text_input(self, message):
        """Process text input and generate response"""
        text = message.get('text', '')
        source = message.get('source', 'unknown')

        self.logger.info(f"Processing input from {source}: {text[:50]}...")

        # Check if we should use online mode
        use_online = self._should_use_online(text)

        if use_online and self.nlp_online:
            response = self._generate_online_response(text)
        else:
            response = self._generate_offline_response(text)

        # Send to TTS queue
        self.queues['nlp->tts'].put({
            'type': 'response',
            'text': response,
            'timestamp': time.time(),
            'mode': 'online' if use_online else 'offline'
        })

    def _process_stt_result(self, message):
        """Process STT transcription result"""
        text = message.get('text', '')
        confidence = message.get('confidence', 0.0)

        if not text:
            # Handle STT failure
            self.queues['nlp->tts'].put({
                'type': 'error',
                'error': 'stt_fail',
                'timestamp': time.time()
            })
            return

        # Process the transcribed text
        self._process_text_input({
            'type': 'text_input',
            'text': text,
            'source': 'stt',
            'confidence': confidence
        })

    def _process_fallback_message(self, message):
        """Process fallback messages (e.g., wakeword silence)"""
        text = message.get('text', '')

        # Send directly to TTS without NLP processing
        self.queues['nlp->tts'].put({
            'type': 'response',
            'text': text,
            'timestamp': time.time(),
            'mode': 'fallback'
        })

    def _generate_offline_response(self, text):
        """Generate response using offline TinyGPT"""
        start_time = time.time()

        try:
            # Get context from memory if available
            context = self._get_conversation_context()

            response = self.nlp_offline.generate_response(text, context, max_length=150)

            # Validate response
            if not self.nlp_offline.validate_response(response):
                response = self.nlp_offline.generate_fallback_response(text)

            latency = time.time() - start_time
            self.logger.info(f"Offline response generated in {latency:.2f}s")

            return response

        except Exception as e:
            self.logger.error(f"Offline generation error: {e}")
            return "I'm sorry, I encountered an error processing your request."

    def _generate_online_response(self, text):
        """Generate response using online HF API"""
        if not self.nlp_online:
            self.logger.warning("Online mode requested but not available")
            return self._generate_offline_response(text)

        start_time = time.time()

        try:
            response = self.nlp_online.generate_response(text, max_length=200)

            latency = time.time() - start_time
            self.logger.info(f"Online response generated in {latency:.2f}s")

            return response

        except Exception as e:
            self.logger.error(f"Online generation error: {e}")
            # Fallback to offline
            return self._generate_offline_response(text)

    def _should_use_online(self, text):
        """Determine if we should use online mode"""
        # Check for heavy reasoning keywords
        heavy_keywords = ['explain', 'analyze', 'summarize', 'translate', 'code']

        if any(keyword in text.lower() for keyword in heavy_keywords):
            return True

        # Check text length for long context
        if len(text) > 200:
            return True

        return False

    def _get_conversation_context(self):
        """Get recent conversation context"""
        # This would integrate with memory module
        # For now, return empty context
        return ""

    def _switch_mode(self, new_mode):
        """Switch between offline and online modes"""
        if new_mode == 'online':
            if not self.nlp_online:
                try:
                    self.nlp_online = NLPModuleHFAPI(self.config, None)  # security module would be passed
                    self.nlp_online.initialize()
                except Exception as e:
                    self.logger.error(f"Failed to initialize online NLP: {e}")
                    return

        self.current_mode = new_mode
        self.logger.info(f"Switched to {new_mode} mode")