import time

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available for HF NLP")

class NLPModuleHFAPI:
    def __init__(self, config):
        self.config = config
        self.generator = None
        self.last_used = 0

    def initialize(self):
        if not TRANSFORMERS_AVAILABLE:
            return
        try:
            # Use a small GPT model for dialogue
            self.generator = pipeline('text-generation', model='microsoft/DialoGPT-small')
        except Exception as e:
            print(f"HF NLP initialization failed: {e}")

    def generate_response(self, prompt, context=None, max_length=100, creative=False):
        """Generate response using DialoGPT"""
        if not self.generator:
            return "Sorry, online NLP is not available."

        try:
            # Add context if available
            if context:
                full_prompt = context + " " + prompt
            else:
                full_prompt = prompt

            temperature = 0.9 if creative else 0.7
            result = self.generator(
                full_prompt,
                max_length=len(full_prompt.split()) + max_length,
                num_return_sequences=1,
                truncation=True,
                pad_token_id=50256,
                temperature=temperature,
                do_sample=creative
            )
            response = result[0]['generated_text']

            # Remove the prompt from response
            if response.startswith(full_prompt):
                response = response[len(full_prompt):].strip()

            self.last_used = time.time()
            return response
        except Exception as e:
            print(f"HF NLP generation failed: {e}")
            return "Sorry, I couldn't generate a response."

    def generate_contextual_response(self, user_input):
        """Generate contextual response"""
        return self.generate_response(user_input)

    def get_intent_and_entities(self, text):
        """Simple intent detection for HF"""
        # Basic implementation
        text_lower = text.lower()
        if any(word in text_lower for word in ['hello', 'hi', 'hey']):
            return 'greeting', {}
        elif any(word in text_lower for word in ['what', 'how', 'why']):
            return 'question', {}
        else:
            return 'general', {}

    def validate_response(self, response):
        """Validate response"""
        return len(response.strip()) > 5

    def generate_fallback_response(self, user_input):
        """Fallback response"""
        return "I'm here to help. What can I do for you?"

    def generate_creative_task(self, user_input):
        """Generate creative task"""
        prompt = f"Suggest creative ways to: {user_input}"
        return self.generate_response(prompt, creative=True)

    def unload_model(self):
        """Unload the model"""
        if self.generator:
            del self.generator
            self.generator = None
        import gc
        gc.collect()