from nlp import UltraLightNLPModule
import os
import requests

class NaturalDialogueEngine:
    def __init__(self, switch_module):
        self.nlp = UltraLightNLPModule()
        self.switch = switch_module

    def respond(self, prompt):
        self.switch.auto_switch()
        if self.switch.get_mode() == 'offline':
            return self.nlp.generate_response(prompt)
        else:
            # Use Hugging Face Inference API
            hf_key = os.getenv('HUGGINGFACE_API_KEY')
            if hf_key:
                try:
                    headers = {"Authorization": f"Bearer {hf_key}"}
                    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 100, "temperature": 0.7}}
                    response_api = requests.post("https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium", headers=headers, json=payload)
                    if response_api.status_code == 200:
                        result = response_api.json()
                        if isinstance(result, list) and result:
                            generated = result[0].get("generated_text", "")
                            if generated.startswith(prompt):
                                return generated[len(prompt):].strip()
                            else:
                                return generated.strip()
                        else:
                            return "HF API error: unexpected response"
                    else:
                        return f"HF API error: {response_api.status_code}"
                except Exception as e:
                    return "HF error: " + str(e)
            else:
                return "Hugging Face API key not set"
            # Try GPT-4 if available
            try:
                import openai
                openai.api_key = os.getenv('OPENAI_API_KEY')
                client = openai.OpenAI()
                completion = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.7
                )
                return completion.choices[0].message.content.strip()
            except Exception as e:
                return "GPT-4 error: " + str(e)

    def supports_natural_speech(self):
        return True