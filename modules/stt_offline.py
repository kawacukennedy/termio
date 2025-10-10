from vosk import Model, KaldiRecognizer
import pyaudio
import json
import keyboard
import time

class STTModuleOffline:
    def __init__(self, config):
        self.config = config
        self.model = None
        self.recognizer = None
        self.audio = None

    def initialize(self):
        try:
            # Load Vosk tiny model (assuming it's downloaded)
            self.model = Model(lang="en-us")
            self.recognizer = KaldiRecognizer(self.model, 16000)
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            print(f"STT offline initialization failed: {e}")

    def transcribe(self, duration=5):
        if not self.recognizer or not self.audio:
            return ""

        stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        stream.start_stream()

        print("Listening...")
        data = b""
        for _ in range(0, int(16000 / 8000 * duration)):
            data += stream.read(8000, exception_on_overflow=False)

        stream.stop_stream()
        stream.close()

        if self.recognizer.AcceptWaveform(data):
            result = json.loads(self.recognizer.Result())
            return result.get("text", "")
        else:
            return ""

    def transcribe_continuous(self, callback):
        # For push-to-talk, implement continuous listening with callback
        pass

    def transcribe_push_to_talk(self, key='space'):
        """Transcribe speech when key is held down"""
        if not self.recognizer or not self.audio:
            return ""

        print("Hold SPACE to talk...")
        while True:
            keyboard.wait(key)  # Wait for key press
            print("LISTENING... (release SPACE to stop)")

            # Start recording
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()

            data = b""
            start_time = time.time()

            # Record while key is held
            while keyboard.is_pressed(key):
                chunk = stream.read(8000, exception_on_overflow=False)
                data += chunk
                # Limit recording to reasonable time
                if time.time() - start_time > 10:
                    break

            stream.stop_stream()
            stream.close()

            # Transcribe
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    return text
            else:
                partial = json.loads(self.recognizer.PartialResult())
                text = partial.get("partial", "").strip()
                if text:
                    return text

            print("No speech detected, try again...")