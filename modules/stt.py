import json
import os
import requests
import io
import wave

class HuggingFaceSTTModule:
    def __init__(self, switch_module=None):
        self.switch = switch_module

    def transcribe(self, data):
        if self.switch and self.switch.get_mode() == 'online':
            return self._transcribe_online(data)
        else:
            return self._transcribe_offline(data)

    def _transcribe_online(self, data):
        # Use Hugging Face Whisper via Inference API
        hf_key = os.getenv('HUGGINGFACE_API_KEY')
        if hf_key:
            try:
                # Create WAV in memory
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(16000)
                    wav_file.writeframes(data)
                wav_buffer.seek(0)
                headers = {'Authorization': f'Bearer {hf_key}'}
                files = {'file': ('audio.wav', wav_buffer, 'audio/wav')}
                response = requests.post('https://api-inference.huggingface.co/models/openai/whisper-base', headers=headers, files=files)
                if response.status_code == 200:
                    result = response.json()
                    return result.get('text', '')
                else:
                    return f"HF STT error: {response.status_code}"
            except Exception as e:
                return "HF STT error: " + str(e)
        else:
            return "Hugging Face API key not set for STT"
        # Fallback to offline
        return self._transcribe_offline(data)

    def _transcribe_offline(self, data):
        # Use Vosk for offline
        from vosk import Model, KaldiRecognizer
        model = Model('vosk-model-small-en-us-0.15')
        rec = KaldiRecognizer(model, 16000)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            return result.get('text', '')
        return None


class OfflineSTTModule:
    def __init__(self):
        pass

    def transcribe(self, data):
        # Use Vosk for offline
        from vosk import Model, KaldiRecognizer
        model = Model('vosk-model-small-en-us-0.15')  # Adjust path
        rec = KaldiRecognizer(model, 16000)
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            return result.get('text', '')
        return None