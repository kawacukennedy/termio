import subprocess
import time
import sys

class TextToSpeechModule:
    def __init__(self):
        self.voice = 'en'  # Default voice
        self.speed = 180  # Words per minute
        self.pitch = 50   # 0-99
        self.volume = 100  # 0-100
        self.waveform_enabled = True

    def set_voice(self, voice_type):
        if voice_type == 'male':
            self.voice = 'en+m3'  # Male voice
        elif voice_type == 'female':
            self.voice = 'en+f2'  # Female voice
        else:  # neutral
            self.voice = 'en'

    def set_speed(self, speed):
        # speed 0.9x to 1.2x, base 180
        self.speed = int(180 * speed)

    def set_pitch(self, pitch_offset):
        # pitch_offset -3 to +3, base 50
        self.pitch = max(0, min(99, 50 + pitch_offset * 10))

    def set_volume(self, volume):
        # 0-100%
        self.volume = volume

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
        cmd = ['espeak-ng', '-v', self.voice, '-s', str(self.speed), '-p', str(self.pitch), '-a', str(self.volume), text]
        subprocess.run(cmd, capture_output=True)

    def _display_waveform(self, text):
        # Simple ASCII waveform simulation
        words = text.split()
        for word in words:
            sys.stdout.write('|')
            sys.stdout.flush()
            time.sleep(0.1)  # Simulate speaking time
        sys.stdout.write('\n')