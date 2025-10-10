from transformers import pipeline
import numpy as np

class STTModuleHFAPI:
    def __init__(self, config):
        self.config = config
        self.pipe = None

    def initialize(self):
        try:
            # Load Whisper tiny quantized model
            self.pipe = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")
        except Exception as e:
            print(f"HF STT initialization failed: {e}")

    def transcribe(self, audio_data):
        """Transcribe audio data using Whisper"""
        if not self.pipe:
            return ""

        try:
            # Convert audio data to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Transcribe
            result = self.pipe(audio_array)
            return result["text"].strip()
        except Exception as e:
            print(f"HF STT transcription failed: {e}")
            return ""