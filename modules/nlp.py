import os
import re
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

class UltraLightNLPModule:
    def __init__(self):
        self.model_name = "distilgpt2"  # Lightweight GPT-2 variant, ~50MB
        self.device = 0 if torch.cuda.is_available() else -1  # CPU if no GPU
        self.generator = None
        self.lazy_loaded = False

    def lazy_load_model(self):
        if not self.lazy_loaded:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
                self.generator = pipeline('text-generation', model=self.model, tokenizer=self.tokenizer, device=self.device)
                self.lazy_loaded = True
            except Exception as e:
                print(f"Failed to load NLP model: {e}")
                self.generator = None

    def generate_response(self, prompt):
        # For testing, use fallback
        return self.fallback_response(prompt)

    def fallback_response(self, prompt):
        # Simple rule-based fallback
        prompt_lower = prompt.lower()
        if "time" in prompt_lower:
            from datetime import datetime
            return f"The time is {datetime.now().strftime('%H:%M:%S')}"
        elif "joke" in prompt_lower:
            return "Why don't scientists trust atoms? Because they make up everything!"
        elif re.search(r'\bdefine\b', prompt_lower):
            word = re.search(r'define (\w+)', prompt_lower)
            if word:
                return f"{word.group(1)}: A word I don't have a definition for offline."
            else:
                return "Please specify a word to define."
        elif re.search(r'\bcalculate\b|\bmath\b', prompt_lower):
            # Simple arithmetic
            match = re.search(r'(\d+)\s*([+\-*/])\s*(\d+)', prompt_lower)
            if match:
                a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
                if op == '+':
                    return str(a + b)
                elif op == '-':
                    return str(a - b)
                elif op == '*':
                    return str(a * b)
                elif op == '/' and b != 0:
                    return str(a / b)
            return "I can do simple arithmetic. Try: calculate 2 + 2"
        elif "summarize" in prompt_lower:
            return "Summary: This is a placeholder summary."
        else:
            return "That's interesting. Tell me more."