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
        # Use better whisper variant as per spec
        self.api_url = "https://api-inference.huggingface.co/models/openai/whisper-base"
        self.headers = {}
        self.cloud_mode_enabled = False

    def initialize(self):
        try:
            self.audio = pyaudio.PyAudio()
            token = self.security.get_api_key("huggingface") if self.security else None
            if token:
                self.headers = {"Authorization": f"Bearer {token}"}
            else:
                print("Warning: No HuggingFace token configured for STT")

            # Check if cloud mode is enabled
            self.cloud_mode_enabled = self.config.get('user_settings', {}).get('cloud_mode', False)
            if not self.cloud_mode_enabled:
                print("Cloud mode not enabled. HF STT will not be used.")
        except Exception as e:
            print(f"HF STT initialization failed: {e}")

    def transcribe(self, duration=5):
        """Transcribe audio using HF Inference API with streaming support"""
        if not self.cloud_mode_enabled:
            return ""

        if not self.audio:
            return ""

        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()

            print("🎤 Listening (HF API streaming)...")
            data = b""

            # Collect audio in chunks for streaming
            chunk_duration = 1.0  # 1 second chunks
            total_chunks = int(duration / chunk_duration)

            for chunk_idx in range(total_chunks):
                chunk_data = b""
                for _ in range(int(16000 / 8000 * chunk_duration)):
                    chunk_data += stream.read(8000, exception_on_overflow=False)

                # Process chunk immediately (streaming)
                partial_text = self._transcribe_chunk(chunk_data)
                if partial_text:
                    print(f"📝 Chunk {chunk_idx + 1}: {partial_text}")
                    data += chunk_data

            stream.stop_stream()
            stream.close()

            if len(data) == 0:
                return ""

            # Final transcription of complete audio
            return self._transcribe_chunk(data, final=True)

        except Exception as e:
            print(f"HF STT transcription failed: {e}")
            return ""

    def _transcribe_chunk(self, audio_data, final=False):
        """Transcribe a chunk of audio data"""
        try:
            # Convert to WAV format for API
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)
            wav_buffer.seek(0)

            # Send to HF API with streaming parameters
            payload = wav_buffer.getvalue()
            headers = self.headers.copy()
            headers["Content-Type"] = "application/octet-stream"

            response = requests.post(
                self.api_url,
                headers=headers,
                data=payload,
                params={"return_timestamps": "true" if final else "false"}
            )

            if response.status_code == 200:
                result = response.json()
                text = result.get("text", "").strip()
                return text
            else:
                print(f"HF STT chunk API error: {response.status_code}")
                return ""

        except Exception as e:
            print(f"HF STT chunk transcription failed: {e}")
            return ""

    def unload_model(self):
        """Unload resources"""
        if self.audio:
            self.audio.terminate()
            self.audio = None