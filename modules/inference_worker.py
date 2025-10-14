#!/usr/bin/env python3
"""
Inference Worker as per microarchitecture spec.
Handles TinyGPT local inferencing and on-demand HF request orchestration.
"""

import time
import logging
from nlp_offline import NLPModuleOffline
from command_parser import CommandParser
from action_planner import ActionPlanner

# Import HF modules conditionally
try:
    from nlp_hf import NLPModuleHFAPI
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("Warning: HuggingFace modules not available. Online features disabled.")

class InferenceWorker:
    def __init__(self, config, queues, memory):
        self.config = config
        self.queues = queues
        self.memory = memory
        self.logger = logging.getLogger('inference_worker')

        # Models
        self.nlp_offline = NLPModuleOffline(config)
        self.nlp_online = None

        # Command parsing and action planning
        self.command_parser = CommandParser(config, self.nlp_offline, None)  # security passed later
        self.action_planner = ActionPlanner(config, None)  # security passed later

        # Current mode
        self.current_mode = 'offline'

        # Failure mode flags
        self.model_load_failed = False
        self.network_unavailable = False

    def check_network_availability(self):
        """Check if network is available for online features"""
        try:
            import requests
            requests.get('https://huggingface.co', timeout=5)
            self.network_unavailable = False
            return True
        except ImportError:
            self.logger.warning("requests module not available, network checks disabled")
            self.network_unavailable = True
            return False
        except:
            self.network_unavailable = True
            return False

    def switch_to_offline_mode(self):
        """Gracefully switch to offline mode when network fails"""
        if self.current_mode != 'offline':
            self.current_mode = 'offline'
            self.logger.info("Switched to offline mode due to network unavailability")
            # Notify UI
            self.queues['nlp->tts'].put({
                'type': 'status_update',
                'message': 'Network unavailable - switched to offline mode',
                'mode': 'offline'
            })

        # Performance limits
        self.max_concurrent_infers = 1
        self.active_infers = 0

    def run(self):
        """Main inference worker loop"""
        self.logger.info("Inference worker starting...")

        # Initialize models with graceful degradation
        try:
            self.nlp_offline.initialize()
        except Exception as e:
            self.logger.error(f"Failed to initialize offline model: {e}")
            self.model_load_failed = True
            # Continue running - will use fallback responses

        # Try to initialize online if network available and HF available
        if HF_AVAILABLE and self.check_network_availability():
            try:
                self.nlp_online = NLPModuleHFAPI(self.config, None)  # security module would be passed
                self.nlp_online.initialize()
                self.current_mode = 'online'  # Default to online if available
            except Exception as e:
                self.logger.error(f"Failed to initialize online NLP: {e}")
                self.nlp_online = None

        last_network_check = 0
        while True:
            try:
                # Periodic network check (every 60 seconds)
                current_time = time.time()
                if current_time - last_network_check > 60:
                    self.check_network_availability()
                    last_network_check = current_time

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

        # First, try command parsing
        command_result = self.command_parser.parse_command(text)

        if command_result['intent'] != 'general_conversation' and command_result['confidence'] > 0.6:
            # Execute command
            self._execute_command(command_result)
            return

        # Otherwise, generate conversational response
        # Check if we should use online mode
        use_online = self._should_use_online(text)

        if use_online and self.nlp_online:
            response = self._generate_online_response(text)
        else:
            response = self._generate_offline_response(text)

        # Update conversation context
        self._update_conversation_context(text, response)

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

    def _execute_command(self, command_result):
        """Execute parsed command using action planner"""
        intent = command_result['intent']
        slots = command_result['slots']
        action_plan = command_result['action_plan']

        self.logger.info(f"Executing command: {intent} with plan of {len(action_plan)} steps")

        # Execute action plan
        result = self.action_planner.execute_plan(action_plan)

        if result['success']:
            response = f"Command executed successfully: {intent}"
        else:
            response = f"Command failed: {result['result']}"

        # Send response
        self.queues['nlp->tts'].put({
            'type': 'response',
            'text': response,
            'timestamp': time.time(),
            'mode': 'command'
        })

    def _generate_offline_response(self, text):
        """Generate response using offline TinyGPT with latency targets"""
        if self.model_load_failed:
            return "I'm currently running in limited mode due to model loading issues. Please check the model installation."

        start_time = time.time()

        try:
            # Get context from memory if available
            context = self._get_conversation_context(text)

            response = self.nlp_offline.generate_response(text, context, max_length=150)

            # Validate response
            if not self.nlp_offline.validate_response(response):
                response = self.nlp_offline.generate_fallback_response(text)

            latency_ms = (time.time() - start_time) * 1000

            # Check latency target: 300-900ms
            if latency_ms > 900:
                self.logger.warning(f"Offline response latency {latency_ms:.0f}ms exceeds target (900ms)")
            elif latency_ms < 300:
                self.logger.info(f"Offline response latency {latency_ms:.0f}ms within target (300-900ms)")
            else:
                self.logger.info(f"Offline response generated in {latency_ms:.0f}ms")

            return response

        except Exception as e:
            self.logger.error(f"Offline generation error: {e}")
            return "I'm sorry, I encountered an error processing your request."

    def _generate_online_response(self, text):
        """Generate response using online HF API with latency targets"""
        if not self.nlp_online:
            self.logger.warning("Online mode requested but not available")
            return self._generate_offline_response(text)

        start_time = time.time()

        try:
            response = self.nlp_online.generate_response(text, max_length=200)

            latency_ms = (time.time() - start_time) * 1000

            # Check latency target: 400-2000ms
            if latency_ms > 2000:
                self.logger.warning(f"Online response latency {latency_ms:.0f}ms exceeds target (2000ms)")
            elif latency_ms < 400:
                self.logger.info(f"Online response latency {latency_ms:.0f}ms within target (400-2000ms)")
            else:
                self.logger.info(f"Online response generated in {latency_ms:.0f}ms")

            return response

        except Exception as e:
            self.logger.error(f"Online generation error: {e}")
            self.switch_to_offline_mode()
            return self._generate_offline_response(text)

    def _should_use_online(self, text):
        """Determine if we should use online mode"""
        # Check if offline mode is forced or network unavailable
        if self.current_mode == 'offline' or self.network_unavailable:
            return False

        # Check for heavy reasoning keywords
        heavy_keywords = ['explain', 'analyze', 'summarize', 'translate', 'code']

        if any(keyword in text.lower() for keyword in heavy_keywords):
            return True

        # Check text length for long context
        if len(text) > 200:
            return True

        return False

    def _get_conversation_context(self, current_query=None):
        """Get conversation context (recent or RAG-retrieved turns)"""
        if self.memory.rag_enabled and current_query:
            relevant_turns = self.memory.get_relevant_turns(current_query, 3)
        else:
            relevant_turns = self.memory.get_recent_turns(3)

        if not relevant_turns:
            return ""

        # Format context as alternating user/assistant turns
        context_parts = []
        for turn in relevant_turns:
            context_parts.append(f"User: {turn['user']}")
            context_parts.append(f"Assistant: {turn['ai']}")

        return " ".join(context_parts)

    def _update_conversation_context(self, user_input, ai_response):
        """Update conversation context with new turn"""
        self.memory.add_turn(user_input, ai_response)

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