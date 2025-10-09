import json

class SpeechToTextModule:
    def __init__(self, model_path='model'):
        from vosk import Model, KaldiRecognizer
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, 16000)

    def transcribe(self, data):
        if self.rec.AcceptWaveform(data):
            result = json.loads(self.rec.Result())
            return result.get('text', '')
        return None