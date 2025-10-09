import subprocess
import time
import sys
import os
import requests
import platform
try:
    import pyttsx3
    HAS_PYTTsx3 = True
except ImportError:
    HAS_PYTTsx3 = False

class TextToSpeechModule:
    def __init__(self, online_mode=False):
        self.online_mode = online_mode
        # Set defaults for offline TTS
        self.voice = 'en'  # Default voice
        self.speed = 180  # Words per minute
        self.pitch = 50   # 0-99
        self.volume = 100  # 0-100
        if self.online_mode:
            self.elevenlabs_key = os.getenv('ELEVENLABS_API_KEY')
            self.voice_id = '21m00Tcm4TlvDq8ikWAM'  # Default voice ID
            self.google_tts_available = True  # gTTS doesn't need key
        self.waveform_enabled = True

    def _play_audio(self, file_path):
        system = platform.system()
        if system == 'Darwin':  # macOS
            subprocess.run(['afplay', file_path])
        elif system == 'Linux':
            subprocess.run(['aplay', file_path])  # or mpg123 for mp3
        elif system == 'Windows':
            subprocess.run(['start', file_path], shell=True)
        else:
            pass  # No play

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
        if self.online_mode:
            self._speak_huggingface(text)
        else:
            self._speak_offline(text)

    def _speak_offline(self, text):
        if HAS_PYTTsx3:
            engine = pyttsx3.init()
            engine.setProperty('voice', self.voice)
            engine.setProperty('rate', self.speed)
            engine.setProperty('volume', self.volume)
            engine.say(text)
            engine.runAndWait()
        else:
            cmd = ['espeak-ng', '-v', self.voice, '-s', str(self.speed), '-p', str(self.pitch), '-a', str(self.volume), text]
            subprocess.run(cmd, capture_output=True)

    def _speak_huggingface(self, text):
        hf_key = os.getenv('HUGGINGFACE_API_KEY')
        if hf_key:
            try:
                headers = {'Authorization': f'Bearer {hf_key}'}
                payload = {"inputs": text}
                response = requests.post('https://api-inference.huggingface.co/models/microsoft/speecht5_tts', headers=headers, json=payload)
                if response.status_code == 200:
                    # Assuming it returns audio bytes
                    with open('/tmp/tts_hf.wav', 'wb') as f:
                        f.write(response.content)
                    self._play_audio('/tmp/tts_hf.wav')
                else:
                    self._speak_offline(text)
            except Exception as e:
                self._speak_offline(text)
        else:
            self._speak_offline(text)

    def _display_waveform(self, text):
        # Simple ASCII waveform simulation
        words = text.split()
        for word in words:
            sys.stdout.write('|')
            sys.stdout.flush()
            time.sleep(0.1)  # Simulate speaking time
        sys.stdout.write('\n')