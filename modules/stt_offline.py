from vosk import Model, KaldiRecognizer
import pyaudio
import json
import time

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Warning: keyboard module not available. Push-to-talk will not work.")

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

        try:
            stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()

            print("🎤 Listening...")
            data = b""
            for _ in range(0, int(16000 / 8000 * duration)):
                chunk = stream.read(8000, exception_on_overflow=False)
                data += chunk

            stream.stop_stream()
            stream.close()

            if len(data) == 0:
                return ""

            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip()
                confidence = result.get("confidence", 0.0)

                # Validate transcription
                if self._validate_transcription(text, confidence):
                    return text
                else:
                    return ""
            else:
                partial = json.loads(self.recognizer.PartialResult())
                partial_text = partial.get("partial", "").strip()
                if partial_text and len(partial_text.split()) > 2:  # At least 3 words
                    return partial_text
                return ""
        except Exception as e:
            print(f"STT transcription error: {e}")
            return ""



    def transcribe_continuous(self, callback):
        # For push-to-talk, implement continuous listening with callback
        pass

    def transcribe_push_to_talk(self, key='space'):
        """Enhanced push-to-talk with voice activity detection"""
        if not self.recognizer or not self.audio:
            return ""

        if not KEYBOARD_AVAILABLE:
            print("❌ Keyboard module not available. Use 'transcribe(duration=5)' instead.")
            return ""

        print(f"🎤 Hold {key.upper()} to speak...")

        silence_threshold = 500  # Adjust for your microphone
        min_speech_duration = 0.3  # Minimum speech duration
        max_recording_time = 15  # Maximum recording time

        while True:
            try:
                keyboard.wait(key)  # Wait for key press
                print("🎤 LISTENING... (release to process)")

                stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
                stream.start_stream()

                data = b""
                start_time = time.time()
                speech_started = False
                last_speech_time = start_time

                # Record with voice activity detection
                while keyboard.is_pressed(key) and (time.time() - start_time) < max_recording_time:
                    chunk = stream.read(8000, exception_on_overflow=False)
                    data += chunk

                    # Voice activity detection
                    audio_level = self._calculate_audio_level(chunk)
                    if audio_level > silence_threshold:
                        speech_started = True
                        last_speech_time = time.time()
                    elif speech_started and (time.time() - last_speech_time) > 1.5:  # 1.5s silence
                        print("🔇 Silence detected, stopping...")
                        break

                stream.stop_stream()
                stream.close()

                duration = time.time() - start_time
                if len(data) > 0 and duration > min_speech_duration:
                    text = self._process_audio_data(data)
                    if text and len(text.strip()) > 1:
                        print(f"✅ Recognized: {text}")
                        return text
                    else:
                        print("❌ No clear speech detected")
                        continue  # Try again
                elif duration < min_speech_duration:
                    print("⚠️  Recording too short, try again")
                    continue

            except KeyboardInterrupt:
                print("\n🛑 STT interrupted")
                return ""
            except Exception as e:
                print(f"❌ STT error: {e}")
                return ""

    def _calculate_audio_level(self, audio_chunk):
        """Calculate RMS audio level for voice activity detection"""
        import struct
        if len(audio_chunk) < 2:
            return 0

        # Convert to 16-bit samples
        samples = struct.unpack('<' + ('h' * (len(audio_chunk) // 2)), audio_chunk)
        if not samples:
            return 0

        # Calculate RMS
        rms = (sum(s**2 for s in samples) / len(samples)) ** 0.5
        return rms

    def _process_audio_data(self, data):
        """Process recorded audio with validation"""
        try:
            if len(data) == 0:
                return ""

            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip()
                confidence = result.get("confidence", 0.0)

                if self._validate_transcription(text, confidence):
                    return text
                else:
                    return ""
            else:
                # Fallback to partial result
                partial = json.loads(self.recognizer.PartialResult())
                partial_text = partial.get("partial", "").strip()
                if partial_text and len(partial_text.split()) >= 2:
                    return partial_text

        except Exception as e:
            print(f"Audio processing error: {e}")

        return ""

    def _validate_transcription(self, text, confidence):
        """Enhanced transcription validation"""
        if not text or len(text.strip()) < 2:
            return False

        # Confidence check
        if confidence < 0.2:  # Lower threshold for partial results
            return False

        # Check for excessive unknown words (Vosk uses [unk])
        words = text.split()
        unk_count = sum(1 for word in words if '[unk]' in word or word.startswith('['))
        if unk_count > len(words) * 0.4:  # More than 40% unknown
            return False

        # Check for gibberish (too many short words)
        short_words = sum(1 for word in words if len(word) <= 1)
        if short_words > len(words) * 0.5:
            return False

        return True

    def unload_model(self):
        """Unload the model to free memory"""
        if self.model:
            del self.model
            self.model = None
        if self.recognizer:
            del self.recognizer
            self.recognizer = None
        if self.audio:
            self.audio.terminate()
            self.audio = None
        import gc
        gc.collect()