from transformers import pipeline

class NLPModuleHFAPI:
    def __init__(self, config):
        self.config = config
        self.generator = None

    def initialize(self):
        try:
            # Use a small GPT model for dialogue
            self.generator = pipeline('text-generation', model='microsoft/DialoGPT-small')
        except Exception as e:
            print(f"HF NLP initialization failed: {e}")

    def generate_response(self, prompt, context=None):
        """Generate response using DialoGPT"""
        if not self.generator:
            return "Sorry, online NLP is not available."

        try:
            # Add context if available
            if context:
                full_prompt = context + " " + prompt
            else:
                full_prompt = prompt

            result = self.generator(full_prompt, max_length=100, num_return_sequences=1, truncation=True, pad_token_id=50256)
            response = result[0]['generated_text']

            # Remove the prompt from response
            if response.startswith(full_prompt):
                response = response[len(full_prompt):].strip()

            return response
        except Exception as e:
            print(f"HF NLP generation failed: {e}")
            return "Sorry, I couldn't generate a response."