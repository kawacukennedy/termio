import time
import random

TRANSFORMERS_AVAILABLE = False
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warning: transformers not available. Using simple NLP fallback.")

class NLPModuleOffline:
    def __init__(self, config):
        self.config = config
        self.generator = None
        self.last_used = 0
        self.conversation_state = {
            'context': [],
            'intent': None,
            'entities': {},
            'topic': None,
            'sentiment': 'neutral'
        }
        self.intent_patterns = {
            'greeting': ['hello', 'hi', 'hey', 'good morning', 'good afternoon'],
            'question': ['what', 'how', 'why', 'when', 'where', 'who', 'which'],
            'command': ['do', 'make', 'create', 'run', 'execute', 'open', 'close'],
            'information': ['tell me', 'explain', 'describe', 'show me'],
            'goodbye': ['bye', 'goodbye', 'see you', 'farewell']
        }

    def _load_model(self):
        """Lazy load the model"""
        if self.generator is None:
            if TRANSFORMERS_AVAILABLE:
                print("Loading NLP model...")
                self.generator = pipeline('text-generation', model='distilgpt2')
            else:
                print("Using simple NLP fallback...")
                self.generator = None  # Will use fallback in generate_response
        self.last_used = time.time()

    def generate_response(self, prompt, context=None, max_length=100, creative=False):
        self._load_model()

        # Build full prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\nUser: {prompt}\nAI:"

        if self.generator is not None:
            # Use transformers
            # Adjust generation parameters for creativity
            if creative:
                temperature = 0.8
                do_sample = True
                num_return_sequences = 1
            else:
                temperature = 0.7
                do_sample = True
                num_return_sequences = 1

            # Generate response
            result = self.generator(
                full_prompt,
                max_length=len(full_prompt.split()) + max_length,
                num_return_sequences=num_return_sequences,
                truncation=True,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=50256
            )

            response = result[0]['generated_text']

            # Clean up response
            if full_prompt in response:
                response = response.replace(full_prompt, '').strip()
        else:
            # Simple fallback responses
            response = self._generate_fallback_response(prompt, context, creative)

        # Update conversation state
        self._update_conversation_state(prompt, response)

        return response

    def _generate_fallback_response(self, prompt, context=None, creative=False):
        """Generate simple fallback responses based on intent"""
        intent = self._detect_intent(prompt.lower())

        # Basic response templates
        responses = {
            'greeting': [
                "Hello! How can I help you today?",
                "Hi there! What can I do for you?",
                "Greetings! How may I assist you?"
            ],
            'question': [
                "That's an interesting question. I'm still learning, but I'll do my best to help.",
                "Good question! Let me think about that.",
                "I'm here to help with that question."
            ],
            'command': [
                "I understand you want me to do something. Please be more specific.",
                "I'd be happy to help with that task.",
                "Let me assist you with that command."
            ],
            'information': [
                "I'd be glad to provide information about that.",
                "Let me share some information on that topic.",
                "Here's what I know about that."
            ],
            'goodbye': [
                "Goodbye! Have a great day!",
                "Farewell! Come back anytime.",
                "See you later!"
            ],
            'general': [
                "I'm here to help. What would you like to know?",
                "How can I assist you today?",
                "What can I do for you?"
            ]
        }

        # Get responses for intent
        intent_responses = responses.get(intent, responses['general'])

        # Add some creativity if requested
        if creative and len(intent_responses) > 1:
            # Add some variation
            creative_additions = [
                " That's fascinating!",
                " I'm excited to help with that.",
                " Let's explore this together.",
                " This sounds interesting!"
            ]
            base_response = random.choice(intent_responses)
            addition = random.choice(creative_additions) if random.random() > 0.5 else ""
            return base_response + addition

        return random.choice(intent_responses)

    def _update_conversation_state(self, user_input, ai_response):
        """Update conversation context and state"""
        # Add to context
        self.conversation_state['context'].append({
            'user': user_input,
            'ai': ai_response,
            'timestamp': time.time()
        })

        # Keep only last 5 exchanges
        if len(self.conversation_state['context']) > 5:
            self.conversation_state['context'] = self.conversation_state['context'][-5:]

        # Detect intent
        self.conversation_state['intent'] = self._detect_intent(user_input)

        # Extract entities
        self.conversation_state['entities'] = self._extract_entities(user_input)

        # Detect topic
        self.conversation_state['topic'] = self._detect_topic(user_input)

        # Simple sentiment analysis
        self.conversation_state['sentiment'] = self._analyze_sentiment(user_input)

    def _detect_intent(self, text):
        """Simple intent detection"""
        text_lower = text.lower()
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return intent
        return 'general'

    def _extract_entities(self, text):
        """Simple entity extraction"""
        entities = {}
        words = text.split()

        # Simple name detection (capitalized words)
        names = [word for word in words if word[0].isupper()]
        if names:
            entities['names'] = names

        # Time expressions
        time_words = ['today', 'tomorrow', 'yesterday', 'morning', 'afternoon', 'evening']
        times = [word for word in words if word.lower() in time_words]
        if times:
            entities['time'] = times

        # Numbers
        numbers = [word for word in words if word.isdigit()]
        if numbers:
            entities['numbers'] = numbers

        return entities

    def _detect_topic(self, text):
        """Simple topic detection"""
        text_lower = text.lower()
        topics = {
            'weather': ['weather', 'rain', 'sunny', 'temperature'],
            'time': ['time', 'clock', 'schedule'],
            'food': ['food', 'eat', 'drink', 'recipe'],
            'tech': ['computer', 'software', 'program', 'code'],
            'help': ['help', 'assist', 'support']
        }

        for topic, keywords in topics.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic

        return 'general'

    def _analyze_sentiment(self, text):
        """Simple sentiment analysis"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'like', 'happy']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'sad', 'angry', 'disappointed']

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def get_conversation_context(self):
        """Get current conversation context"""
        return self.conversation_state

    def generate_contextual_response(self, user_input):
        """Generate response with full context awareness"""
        context = self.get_conversation_context()

        # Build enhanced prompt
        prompt_parts = []

        # Add topic context
        if context['topic'] != 'general':
            prompt_parts.append(f"Topic: {context['topic']}")

        # Add intent context
        if context['intent'] != 'general':
            prompt_parts.append(f"Intent: {context['intent']}")

        # Add sentiment context
        prompt_parts.append(f"Mood: {context['sentiment']}")

        # Add recent conversation
        if context['context']:
            recent = context['context'][-2:]  # Last 2 exchanges
            for exchange in recent:
                prompt_parts.append(f"Previous: User said '{exchange['user'][:50]}...' AI responded '{exchange['ai'][:50]}...'")

        # Add current input
        prompt_parts.append(f"Current: {user_input}")

        enhanced_prompt = "\n".join(prompt_parts)

        return self.generate_response(enhanced_prompt, max_length=150)

    def get_intent_and_entities(self, text):
        """Get intent and entities for command processing"""
        intent = self._detect_intent(text)
        entities = self._extract_entities(text)
        return intent, entities

    def validate_response(self, response):
        """Basic response validation"""
        if not response or len(response.strip()) < 5:
            return False
        if response.count('?') > 3:  # Too many questions
            return False
        return True

    def generate_fallback_response(self, user_input):
        """Generate fallback response when main generation fails"""
        intent = self.conversation_state.get('intent', 'general')

        fallbacks = {
            'greeting': "Hello! How can I help you today?",
            'question': "That's an interesting question. Let me think about that.",
            'command': "I understand you want me to do something. Could you be more specific?",
            'information': "I'd be happy to provide information. What would you like to know?",
            'goodbye': "Goodbye! Have a great day!",
            'general': "I heard you. Can you tell me more?"
        }

        return fallbacks.get(intent, "I'm here to help. What can I do for you?")

    def generate_creative_task(self, user_input):
        """Generate creative task suggestions based on user input"""
        self._load_model()

        creative_prompts = [
            f"Based on '{user_input}', suggest 3 creative ways to:",
            f"How could we make '{user_input}' more interesting?",
            f"What creative tasks relate to '{user_input}'?"
        ]

        suggestions = []
        for prompt in creative_prompts[:1]:  # Just use first for now
            result = self.generator(
                prompt,
                max_length=len(prompt.split()) + 50,
                num_return_sequences=1,
                truncation=True,
                temperature=0.9,
                do_sample=True,
                pad_token_id=50256
            )
            suggestion = result[0]['generated_text'].replace(prompt, '').strip()
            suggestions.append(suggestion)

        return suggestions[0] if suggestions else "I have some creative ideas!"

    def unload_if_inactive(self):
        """Unload model if inactive for 5 minutes"""
        if self.generator and time.time() - self.last_used > 300:
            self.generator = None
            print("Unloaded NLP model")

    def unload_model(self):
        """Force unload the model"""
        if self.generator:
            self.generator = None
            print("Unloaded NLP model")