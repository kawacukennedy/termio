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

    def generate_response(self, prompt):
        self._load_model()
        # Generate response
        result = self.generator(prompt, max_length=50, num_return_sequences=1, truncation=True)
        return result[0]['generated_text'].replace(prompt, '').strip()

    def unload_if_inactive(self):
        """Unload model if inactive for 5 minutes"""
        if self.generator and time.time() - self.last_used > 300:
            self.generator = None
            print("Unloaded NLP model")