import requests
import pyaudio
import numpy as np
import io
import wave

class STTModuleHFAPI:
    def __init__(self, config, security_module=None):
        self.config = config
        self.security = security_module
        self.audio = None
        self.api_url = "https://api-inference.huggingface.co/models/openai/whisper-tiny"
        self.headers = {}

    def initialize(self):
        try:
            self.audio = pyaudio.PyAudio()
            token = self.security.get_api_key("huggingface") if self.security else None
            if token:
                self.headers = {"Authorization": f"Bearer {token}"}
            else:
                print("Warning: No HuggingFace token configured for STT")
        except Exception as e:
            print(f"HF STT initialization failed: {e}")

    def transcribe(self, duration=5):
        """Transcribe audio using HF Inference API"""
        if not self.audio:
            return ""

        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()

            print("🎤 Listening (HF API)...")
            data = b""
            for _ in range(0, int(16000 / 8000 * duration)):
                chunk = stream.read(8000, exception_on_overflow=False)
                data += chunk

            stream.stop_stream()
            stream.close()

            if len(data) == 0:
                return ""

            # Convert to WAV format for API
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(data)
            wav_buffer.seek(0)

            # Send to HF API
            response = requests.post(self.api_url, headers=self.headers, data=wav_buffer.getvalue())
            if response.status_code == 200:
                result = response.json()
                return result.get("text", "").strip()
            else:
                print(f"HF STT API error: {response.status_code} - {response.text}")
                return ""
        except Exception as e:
            print(f"HF STT transcription failed: {e}")
            return ""

    def unload_model(self):
        """Unload resources"""
        if self.audio:
            self.audio.terminate()
            self.audio = None