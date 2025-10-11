from transformers import pipeline
import numpy as np
import pyaudio
import time

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available for HF STT")

class STTModuleHFAPI:
    def __init__(self, config):
        self.config = config
        self.pipe = None
        self.audio = None

    def initialize(self):
        if not TRANSFORMERS_AVAILABLE:
            return
        try:
            # Load Whisper tiny quantized model
            self.pipe = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            print(f"HF STT initialization failed: {e}")

    def transcribe(self, duration=5):
        """Transcribe audio for given duration using Whisper"""
        if not self.pipe or not self.audio:
            return ""

        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()

            print("🎤 Listening (HF)...")
            data = b""
            for _ in range(0, int(16000 / 8000 * duration)):
                chunk = stream.read(8000, exception_on_overflow=False)
                data += chunk

            stream.stop_stream()
            stream.close()

            if len(data) == 0:
                return ""

            # Convert to numpy array
            audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

            # Transcribe
            result = self.pipe(audio_array)
            text = result["text"].strip()
            return text
        except Exception as e:
            print(f"HF STT transcription failed: {e}")
            return ""

    def unload_model(self):
        """Unload the model"""
        if self.pipe:
            del self.pipe
            self.pipe = None
        if self.audio:
            self.audio.terminate()
            self.audio = None
        import gc
        gc.collect()