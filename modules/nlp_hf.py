import requests
import time

class NLPModuleHFAPI:
    def __init__(self, config, security_module=None):
        self.config = config
        self.security = security_module
        self.api_url = "https://api-inference.huggingface.co/models/gpt2"
        self.headers = {}
        self.last_used = 0

    def initialize(self):
        token = self.security.get_api_key("huggingface") if self.security else None
        if token:
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            print("Warning: No HuggingFace token configured for NLP")

    def generate_response(self, prompt, context=None, max_length=100, creative=False):
        """Generate response using HF Inference API"""
        try:
            # Add context if available
            if context:
                full_prompt = context + " " + prompt
            else:
                full_prompt = prompt

            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "max_length": len(full_prompt.split()) + max_length,
                    "temperature": 0.9 if creative else 0.7,
                    "do_sample": creative,
                    "pad_token_id": 50256
                }
            }

            response = requests.post(self.api_url, headers=self.headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and result:
                    generated_text = result[0].get("generated_text", "")
                    # Remove the prompt from response
                    if generated_text.startswith(full_prompt):
                        response_text = generated_text[len(full_prompt):].strip()
                    else:
                        response_text = generated_text.strip()
                    self.last_used = time.time()
                    return response_text
                else:
                    return "Sorry, I couldn't generate a response."
            else:
                print(f"HF NLP API error: {response.status_code} - {response.text}")
                return "Sorry, online NLP is not available."
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
        """Unload resources"""
        pass