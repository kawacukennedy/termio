try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class UltraLightNLPModule:
    def __init__(self, model_name="microsoft/DialoGPT-small"):
        if HAS_TRANSFORMERS:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            self.model.eval()
            # Disable gradients for inference
            for param in self.model.parameters():
                param.requires_grad = False
        else:
            self.tokenizer = None
            self.model = None

    def generate_response(self, prompt, max_length=100):
        if not HAS_TRANSFORMERS:
            # Extract user input from prompt
            lines = prompt.strip().split('\n')
            for line in reversed(lines):
                if line.startswith("User: "):
                    return "NLP not available. Echo: " + line[6:]
            return "NLP not available. Echo: " + prompt
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_length=inputs["input_ids"].shape[1] + max_length,
                num_return_sequences=1,
                no_repeat_ngram_size=2,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the AI part after the prompt
        if prompt in response:
            response = response[len(prompt):].strip()
        return response