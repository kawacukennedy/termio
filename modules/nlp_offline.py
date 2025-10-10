from transformers import pipeline
import time

class NLPModuleOffline:
    def __init__(self, config):
        self.config = config
        self.generator = None
        self.last_used = 0

    def _load_model(self):
        """Lazy load the model"""
        if self.generator is None:
            print("Loading NLP model...")
            self.generator = pipeline('text-generation', model='distilgpt2')
        self.last_used = time.time()

    def generate_response(self, prompt, context=None, max_length=100, creative=False):
        self._load_model()

        # Build full prompt with context
        full_prompt = prompt
        if context:
            full_prompt = f"{context}\nUser: {prompt}\nAI:"

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

        # Remove any remaining prompt artifacts
        response = response.split('\nUser:')[0].split('\nAI:')[0].strip()

        return response

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