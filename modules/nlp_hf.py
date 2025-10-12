import requests
import time

class NLPModuleHFAPI:
    def __init__(self, config, security_module=None):
        self.config = config
        self.security = security_module
        # Use instruction-following model as per spec (hosted quantized 125M–1B variants)
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        self.headers = {}
        self.last_used = 0
        self.cloud_mode_enabled = False

    def initialize(self):
        token = self.security.get_api_key("huggingface") if self.security else None
        if token:
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            print("Warning: No HuggingFace token configured for NLP")

        # Check if cloud mode is enabled
        self.cloud_mode_enabled = self.config.get('user_settings', {}).get('cloud_mode', False)
        if not self.cloud_mode_enabled:
            print("Cloud mode not enabled. HF NLP will not be used.")

    def generate_response(self, prompt, context=None, max_length=100, creative=False):
        """Generate response using HF Inference API with security checks"""
        if not self.cloud_mode_enabled:
            return "Cloud mode not enabled for NLP"

        try:
            # Add context if available
            if context:
                full_prompt = context + " " + prompt
            else:
                full_prompt = prompt

            # Redact/filter payload before upload as per spec
            redacted_prompt = self._redact_sensitive_data(full_prompt)

            payload = {
                "inputs": redacted_prompt,
                "parameters": {
                    "max_length": len(redacted_prompt.split()) + max_length,
                    "temperature": 0.9 if creative else 0.7,
                    "do_sample": creative,
                    "pad_token_id": 50256,
                    "use_cache": True,
                    "wait_for_model": False
                },
                "options": {"use_cache": True, "wait_for_model": False}
            }

            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and result:
                    generated_text = result[0].get("generated_text", "")
                    # Remove the prompt from response
                    if generated_text.startswith(redacted_prompt):
                        response_text = generated_text[len(redacted_prompt):].strip()
                    else:
                        response_text = generated_text.strip()
                    self.last_used = time.time()
                    return response_text
                else:
                    return "Sorry, I couldn't generate a response."
            else:
                print(f"HF NLP API error: {response.status_code} - {response.text}")
                return "Sorry, online NLP is not available."
        except requests.exceptions.Timeout:
            return "Online NLP request timed out."
        except Exception as e:
            print(f"HF NLP generation failed: {e}")
            return "Sorry, I couldn't generate a response."

    def _redact_sensitive_data(self, text):
        """Redact sensitive data before sending to HF API"""
        import re

        # Remove potential PII patterns
        redacted = text

        # Email addresses
        redacted = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', redacted)

        # Phone numbers (basic pattern)
        redacted = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', redacted)

        # IP addresses
        redacted = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', redacted)

        # API keys (long alphanumeric strings)
        redacted = re.sub(r'\b[A-Za-z0-9]{32,}\b', '[API_KEY]', redacted)

        return redacted

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