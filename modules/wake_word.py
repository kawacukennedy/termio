import pvporcupine
import pyaudio
import struct

class WakeWordDetectionModule:
    def __init__(self, config):
        self.config = config
        self.porcupine = None
        self.audio_stream = None
        self.is_listening = False

    def initialize(self):
        # Initialize Porcupine with 'Auralis' keyword
        try:
            self.porcupine = pvporcupine.create(
                keywords=['auralis'],
                sensitivities=[0.5]  # medium sensitivity
            )
            self.audio_stream = pyaudio.PyAudio().open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            self.is_listening = True
        except Exception as e:
            print(f"Wakeword initialization failed: {e}")
            self.is_listening = False

    def detect(self):
        if not self.is_listening or not self.audio_stream:
            return False

        try:
            pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            keyword_index = self.porcupine.process(pcm)
            return keyword_index >= 0
        except Exception as e:
            print(f"Wakeword detection error: {e}")
            return False

    def stop(self):
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.porcupine:
            self.porcupine.delete()
        self.is_listening = False