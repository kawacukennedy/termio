import pyttsx3
import time
import sys

class TextToSpeechModule:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)  # Default speed
        self.engine.setProperty('volume', 0.9)  # Default volume
        self.voices = self.engine.getProperty('voices')
        self.current_voice = 0  # Index for voice
        self.set_voice('male')  # Default
        self.waveform_enabled = True

    def set_voice(self, voice_type):
        if voice_type == 'male':
            for i, voice in enumerate(self.voices):
                if 'male' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    self.current_voice = i
                    break
        elif voice_type == 'female':
            for i, voice in enumerate(self.voices):
                if 'female' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    self.current_voice = i
                    break
        else:  # neutral or default
            self.engine.setProperty('voice', self.voices[0].id)
            self.current_voice = 0

    def set_speed(self, speed):
        # speed 0.9x to 1.2x
        rate = int(180 * speed)
        self.engine.setProperty('rate', rate)

    def set_pitch(self, pitch_offset):
        # pitch -3 to +3 semitones, but pyttsx3 doesn't directly support pitch, approximate with rate
        # For simplicity, adjust rate slightly
        current_rate = self.engine.getProperty('rate')
        new_rate = current_rate + (pitch_offset * 10)
        self.engine.setProperty('rate', max(100, min(300, new_rate)))

    def set_volume(self, volume):
        # 0-100%
        self.engine.setProperty('volume', volume / 100.0)

    def set_profile(self, profile):
        if profile == 'formal':
            self.set_speed(0.9)
            self.set_pitch(-1)
        elif profile == 'casual':
            self.set_speed(1.1)
            self.set_pitch(0)
        elif profile == 'energetic':
            self.set_speed(1.2)
            self.set_pitch(1)

    def speak(self, text):
        if self.waveform_enabled:
            self._display_waveform(text)
        self.engine.say(text)
        self.engine.runAndWait()

    def _display_waveform(self, text):
        # Simple ASCII waveform simulation
        words = text.split()
        for word in words:
            sys.stdout.write('|')
            sys.stdout.flush()
            time.sleep(0.1)  # Simulate speaking time
        sys.stdout.write('\n')