#!/usr/bin/env python3
"""
Command and Intent Parser as per microarchitecture spec.
Hybrid rule-based + LLM intent classifier with action planner.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

class CommandParser:
    def __init__(self, config, nlp_module=None, security_module=None):
        self.config = config
        self.nlp = nlp_module
        self.security = security_module
        self.logger = logging.getLogger('command_parser')

        # Rule-based patterns for common intents
        self.intent_patterns = {
            'screen_read': [
                r'read\s+(?:the\s+)?(?:this|screen|page)',
                r'show\s+me\s+(?:the\s+)?screen',
                r'what\s+(?:do\s+you\s+)?see',
                r'summarize\s+(?:this|screen|page)'
            ],
            'screen_control': [
                r'click\s+(?:on\s+)?(.+)',
                r'press\s+(.+)',
                r'type\s+(.+)',
                r'scroll\s+(.+)',
                r'close\s+(?:window|tab)'
            ],
            'system_info': [
                r'(?:what|show)\s+(?:is\s+)?(?:my\s+)?system\s+info',
                r'tell\s+me\s+about\s+(?:my\s+)?system',
                r'system\s+status'
            ],
            'file_operations': [
                r'(?:open|show|list)\s+(?:file|folder|directory)\s+(.+)',
                r'create\s+(?:file|folder)\s+(.+)',
                r'delete\s+(.+)'
            ],
            'web_browse': [
                r'(?:open|go\s+to)\s+(?:browser|website|url)\s+(.+)',
                r'search\s+(?:for|web)\s+(.+)',
                r'google\s+(.+)'
            ],
            'automation': [
                r'create\s+macro\s+(.+)',
                r'run\s+macro\s+(.+)',
                r'schedule\s+task\s+(.+)',
                r'set\s+(?:reminder|timer)\s+(.+)'
            ],
            'settings': [
                r'change\s+(?:voice|mode|settings?)\s+(.+)',
                r'switch\s+to\s+(?:online|offline)\s+mode',
                r'enable\s+(.+)',
                r'disable\s+(.+)'
            ]
        }

        # Forbidden action patterns
        self.forbidden_patterns = [
            r'rm\s+-rf\s+/',  # Dangerous rm commands
            r'format\s+.*drive',  # Disk formatting
            r'delete\s+system',  # System deletion
            r'override\s+.*admin',  # Admin overrides
            r'hack\s+.*',  # Hacking attempts
            r'exploit\s+.*'  # Exploit attempts
        ]

        # Slot extraction patterns
        self.slot_patterns = {
            'location': r'(?:at|on|in)\s+(.+?)(?:\s|$)',
            'time': r'(?:in|at|after)\s+(\d+)\s+(?:minute|hour|second)s?',
            'url': r'https?://[^\s]+',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'filepath': r'(?:/|\./|~\s*/)[^\s]+',
            'number': r'\b\d+\b'
        }

    def parse_command(self, user_input: str) -> Dict:
        """
        Parse user input into intent, slots, and confidence.
        Returns: {"intent": str, "slots": dict, "confidence": float, "action_plan": list}
        """
        # Step 1: Safety check - reject forbidden commands
        if self._check_forbidden(user_input):
            return {
                "intent": "forbidden",
                "slots": {},
                "confidence": 1.0,
                "action_plan": [],
                "error": "Command contains forbidden operations"
            }

        # Step 2: Rule-based intent classification
        intent, rule_confidence = self._rule_based_intent(user_input)

        # Step 3: LLM-based intent confirmation/verification (if available)
        llm_intent, llm_confidence = self._llm_intent_classification(user_input)

        # Step 4: Combine results (rule-based takes priority for safety)
        final_intent = intent if rule_confidence > 0.7 else llm_intent
        final_confidence = max(rule_confidence, llm_confidence)

        # Step 5: Extract slots
        slots = self._extract_slots(user_input, final_intent)

        # Step 6: Generate action plan
        action_plan = self._generate_action_plan(final_intent, slots)

        return {
            "intent": final_intent,
            "slots": slots,
            "confidence": final_confidence,
            "action_plan": action_plan
        }

    def _check_forbidden(self, user_input: str) -> bool:
        """Check if input contains forbidden operations"""
        input_lower = user_input.lower()
        for pattern in self.forbidden_patterns:
            if re.search(pattern, input_lower):
                self.logger.warning(f"Forbidden pattern detected: {pattern}")
                return True
        return False

    def _rule_based_intent(self, user_input: str) -> Tuple[str, float]:
        """Rule-based intent classification"""
        input_lower = user_input.lower()

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, input_lower):
                    confidence = 0.8  # High confidence for rule matches
                    return intent, confidence

        return "general_conversation", 0.3

    def _llm_intent_classification(self, user_input: str) -> Tuple[str, float]:
        """LLM-based intent classification using TinyGPT"""
        if not self.nlp:
            return "general_conversation", 0.0

        try:
            # Use TinyGPT for intent classification
            prompt = f"Classify the intent of this user input. Choose from: screen_read, screen_control, system_info, file_operations, web_browse, automation, settings, general_conversation.\n\nInput: {user_input}\nIntent:"
            response = self.nlp.generate_response(prompt, max_length=20)

            # Parse response
            response_lower = response.lower().strip()
            possible_intents = ['screen_read', 'screen_control', 'system_info', 'file_operations',
                              'web_browse', 'automation', 'settings', 'general_conversation']

            for intent in possible_intents:
                if intent in response_lower:
                    return intent, 0.6  # Medium confidence for LLM

        except Exception as e:
            self.logger.error(f"LLM intent classification failed: {e}")

        return "unknown", 0.0

    def _extract_slots(self, user_input: str, intent: str) -> Dict:
        """Extract slots from user input"""
        slots = {}

        # Intent-specific slot extraction
        if intent == 'screen_control':
            # Extract click locations, keys, etc.
            click_match = re.search(r'click\s+(?:on\s+)?(.+)', user_input, re.IGNORECASE)
            if click_match:
                slots['target'] = click_match.group(1).strip()

            type_match = re.search(r'type\s+(.+)', user_input, re.IGNORECASE)
            if type_match:
                slots['text'] = type_match.group(1).strip()

        elif intent == 'web_browse':
            url_match = re.search(self.slot_patterns['url'], user_input)
            if url_match:
                slots['url'] = url_match.group(0)

            # Extract search query
            search_match = re.search(r'search\s+(?:for\s+)?(.+)', user_input, re.IGNORECASE)
            if search_match:
                slots['query'] = search_match.group(1).strip()

        elif intent == 'file_operations':
            path_match = re.search(self.slot_patterns['filepath'], user_input)
            if path_match:
                slots['path'] = path_match.group(0)

        elif intent == 'automation':
            time_match = re.search(self.slot_patterns['time'], user_input)
            if time_match:
                slots['delay_minutes'] = int(time_match.group(1))

        # General slot extraction
        for slot_name, pattern in self.slot_patterns.items():
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match and slot_name not in slots:
                slots[slot_name] = match.group(1) if match.groups() else match.group(0)

        return slots

    def _generate_action_plan(self, intent: str, slots: Dict) -> List[Dict]:
        """Generate action plan as DAG with constraints"""
        plan = []

        # Maximum 6 steps per action
        max_steps = 6

        if intent == 'screen_read':
            plan = [
                {
                    "step": 1,
                    "action": "capture_screen",
                    "params": {"region": slots.get('location', 'active_window')},
                    "requires_permission": False
                },
                {
                    "step": 2,
                    "action": "ocr_process",
                    "params": {"fast_pass": True, "structured_pass": True},
                    "requires_permission": False
                },
                {
                    "step": 3,
                    "action": "summarize_content",
                    "params": {"max_sentences": 3},
                    "requires_permission": False
                }
            ]

        elif intent == 'screen_control':
            plan = [
                {
                    "step": 1,
                    "action": "validate_target",
                    "params": {"target": slots.get('target')},
                    "requires_permission": False
                },
                {
                    "step": 2,
                    "action": "request_confirmation",
                    "params": {"action": "screen_control", "dangerous": self._is_dangerous_action(intent, slots)},
                    "requires_permission": False
                },
                {
                    "step": 3,
                    "action": "execute_control",
                    "params": slots,
                    "requires_permission": True
                }
            ]

        elif intent == 'web_browse':
            plan = [
                {
                    "step": 1,
                    "action": "validate_url",
                    "params": {"url": slots.get('url')},
                    "requires_permission": False
                },
                {
                    "step": 2,
                    "action": "open_browser",
                    "params": {"url": slots.get('url')},
                    "requires_permission": False
                }
            ]

        elif intent == 'file_operations':
            plan = [
                {
                    "step": 1,
                    "action": "validate_path",
                    "params": {"path": slots.get('path')},
                    "requires_permission": False
                },
                {
                    "step": 2,
                    "action": "check_permissions",
                    "params": {"operation": intent},
                    "requires_permission": True
                },
                {
                    "step": 3,
                    "action": "execute_file_op",
                    "params": slots,
                    "requires_permission": True
                }
            ]

        # Ensure plan doesn't exceed max steps
        if len(plan) > max_steps:
            plan = plan[:max_steps]

        return plan

    def _is_dangerous_action(self, intent: str, slots: Dict) -> bool:
        """Determine if action is dangerous and requires special confirmation"""
        dangerous_intents = ['file_operations']
        dangerous_slots = ['delete', 'remove', 'format']

        if intent in dangerous_intents:
            return True

        slot_text = ' '.join(str(v) for v in slots.values())
        return any(word in slot_text.lower() for word in dangerous_slots)

    def validate_action_plan(self, plan: List[Dict]) -> Tuple[bool, str]:
        """Validate action plan against constraints"""
        if len(plan) > 6:
            return False, "Action plan exceeds maximum steps (6)"

        destructive_steps = sum(1 for step in plan if step.get('requires_permission', False))
        if destructive_steps > 0 and not self.security:
            return False, "Destructive actions require security module"

        return True, "Plan validated"