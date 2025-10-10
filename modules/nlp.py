import os
import re
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class UltraLightNLPModule:
    def __init__(self):
        self.model_name = "distilgpt2"  # Lightweight GPT-2 variant, ~50MB
        if HAS_TRANSFORMERS:
            self.device = 0 if torch.cuda.is_available() else -1  # CPU if no GPU
        else:
            self.device = -1
        self.generator = None
        self.lazy_loaded = False

    def lazy_load_model(self):
        if not self.lazy_loaded and HAS_TRANSFORMERS:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
                self.generator = pipeline('text-generation', model=self.model, tokenizer=self.tokenizer, device=self.device)
                self.lazy_loaded = True
            except Exception as e:
                print(f"Failed to load NLP model: {e}")
                self.generator = None
        elif not HAS_TRANSFORMERS:
            self.generator = None

    def generate_response(self, prompt):
        self.lazy_load_model()
        if self.generator:
            try:
                # Generate response
                inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
                outputs = self.model.generate(inputs['input_ids'], max_length=100, num_return_sequences=1, no_repeat_ngram_size=2, temperature=0.7)
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                # Clean up response
                if response.startswith(prompt):
                    response = response[len(prompt):].strip()
                return response if response else self.fallback_response(prompt)
            except Exception as e:
                print(f"Model generation error: {e}")
                return self.fallback_response(prompt)
        else:
            return self.fallback_response(prompt)

    def fallback_response(self, prompt):
        # Improved rule-based fallback with Jarvis personality
        prompt_lower = prompt.lower()
        if "time" in prompt_lower:
            from datetime import datetime
            return f"The current time is {datetime.now().strftime('%H:%M:%S')}, sir."
        elif "joke" in prompt_lower:
            return "Why don't scientists trust atoms? Because they make up everything! Would you like another?"
        elif re.search(r'\bdefine\b', prompt_lower):
            word = re.search(r'define (\w+)', prompt_lower)
            if word:
                return f"{word.group(1)}: I'm afraid I don't have access to definitions offline. Perhaps try an online search?"
            else:
                return "Please specify a word to define, sir."
        elif re.search(r'\bcalculate\b|\bmath\b', prompt_lower):
            # Simple arithmetic
            match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', prompt_lower)
            if match:
                a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
                if op == '+':
                    result = a + b
                elif op == '-':
                    result = a - b
                elif op == '*':
                    result = a * b
                elif op == '/' and b != 0:
                    result = a / b
                else:
                    return "Division by zero is not allowed, sir."
                return f"The result is {result}."
            return "I can perform simple arithmetic. Try: calculate 2 + 2"
        elif "summarize" in prompt_lower:
            return "Summary: This appears to be a request for summarization. In offline mode, I can provide basic responses."
        elif "hello" in prompt_lower or "hi" in prompt_lower:
            return "Hello, sir. How can I assist you today?"
        elif "thank" in prompt_lower:
            return "You're welcome, sir."
        elif "help" in prompt_lower:
            return "I can help with time, calculations, jokes, and more. What do you need?"
        else:
            responses = [
                "That's quite interesting. Could you tell me more?",
                "I'm here to help. What else is on your mind?",
                "Fascinating point. How can I assist further?",
                "Understood, sir. Is there anything else I can do for you?"
            ]
            import random
            return random.choice(responses)