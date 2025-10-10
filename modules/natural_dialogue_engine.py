from nlp import UltraLightNLPModule
import os
import requests

class NaturalDialogueEngine:
    def __init__(self, switch_module, memory_module):
        self.nlp = UltraLightNLPModule()
        self.switch = switch_module
        self.memory = memory_module

    def respond(self, prompt):
        # Safety check
        forbidden = ["bypass system security", "create malware", "assist in illegal violence", "hack", "exploit"]
        if any(word in prompt.lower() for word in forbidden):
            return "I'm sorry, but I cannot assist with that request as it violates safety guidelines."

        self.switch.auto_switch()
        hf_key = os.getenv('HUGGINGFACE_API_KEY')
        context = self.memory.get_context()  # Get last 3 turns
        conversation_history = ""
        for turn in context[-3:]:  # Last 3 turns
            conversation_history += f"User: {turn['user']}\nAssistant: {turn['response']}\n"
        conversation_history += f"User: {prompt}\nAssistant:"

        if self.switch.get_mode() == 'online' and hf_key:
            # Use Hugging Face Inference API with system prompt and history
            try:
                system_prompt = "You are Auralis, an AI assistant inspired by JARVIS from Iron Man. Respond politely, concisely, with a touch of wit when fitting. Prioritize user safety and helpfulness. Engage in natural conversation, ask follow-up questions if appropriate. Keep responses under 100 words."
                full_prompt = f"{system_prompt}\n{conversation_history}"
                headers = {"Authorization": f"Bearer {hf_key}"}
                payload = {"inputs": full_prompt, "parameters": {"max_new_tokens": 100, "temperature": 0.7, "do_sample": True}}
                response_api = requests.post("https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill", headers=headers, json=payload, timeout=15)
                if response_api.status_code == 200:
                    result = response_api.json()
                    if isinstance(result, list) and result:
                        generated = result[0].get("generated_text", "")
                        # Extract the new response
                        if conversation_history in generated:
                            response = generated.replace(conversation_history, "").strip()
                        else:
                            response = generated.strip()
                        # Clean up
                        if response.startswith("Assistant:"):
                            response = response[10:].strip()
                        # Safety filter on response
                        if any(word in response.lower() for word in forbidden):
                            return "I apologize, but I cannot provide that information."
                        return response[:200]  # Limit length
                    else:
                        return "I'm sorry, I couldn't generate a response right now."
                else:
                    return "Cloud service unavailable, switching to offline mode."
            except Exception as e:
                return "Connection issue, using offline mode."
        else:
            # Offline or no key
            return self.nlp.generate_response(prompt)

    def supports_natural_speech(self):
        return True