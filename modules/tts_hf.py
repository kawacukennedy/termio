from transformers import pipeline
import sounddevice as sd
import numpy as np

class TTSModuleHFAPI:
    def __init__(self, config):
        self.config = config
        self.synthesizer = None

    def initialize(self):
        try:
            # Use a TTS model from HF
            self.synthesizer = pipeline("text-to-speech", model="microsoft/speecht5_tts")
        except Exception as e:
            print(f"HF TTS initialization failed: {e}")

    def speak(self, text, voice='en'):
        """Synthesize speech using HF model"""
        if not self.synthesizer:
            print(f"[TTS]: {text}")
            return

        try:
            # Generate speech
            result = self.synthesizer(text)

            # Play audio
            audio = result["audio"]
            sample_rate = result["sampling_rate"]

            # Convert to numpy array if needed
            if isinstance(audio, list):
                audio = np.array(audio)

            sd.play(audio, samplerate=sample_rate)
            sd.wait()
        except Exception as e:
            print(f"HF TTS failed: {e}")
            print(f"[TTS]: {text}")