from nlp import UltraLightNLPModule

class NaturalDialogueEngine:
    def __init__(self):
        self.nlp = UltraLightNLPModule()

    def respond(self, prompt):
        return self.nlp.generate_response(prompt)

    def supports_natural_speech(self):
        return True