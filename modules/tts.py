import os
import subprocess
import requests
from io import BytesIO
import pygame  # For playing audio online
import tempfile
import os
import shutil

class TextToSpeechModule:
    def __init__(self, online_mode=False):
        self.online_mode = online_mode
        self.voice = "male_default"
        self.speed = 1.0
        self.pitch = 0
        self.volume = 100
        self.profile = "casual"
        self.switch = None  # Will be set if needed

    def set_voice(self, voice):
        if voice in ["male_default", "female_default", "neutral"]:
            self.voice = voice

    def set_speed(self, speed):
        if 0.9 <= speed <= 1.2:
            self.speed = speed

    def set_pitch(self, pitch):
        if -3 <= pitch <= 3:
            self.pitch = pitch

    def set_volume(self, volume):
        if 0 <= volume <= 100:
            self.volume = volume

    def set_profile(self, profile):
        if profile in ["formal", "casual", "energetic"]:
            self.profile = profile
            # Adjust settings based on profile
            if profile == "formal":
                self.speed = 0.9
                self.pitch = 1
            elif profile == "casual":
                self.speed = 1.0
                self.pitch = 0
            elif profile == "energetic":
                self.speed = 1.1
                self.pitch = -1

    def speak(self, text):
        if self.switch and self.switch.get_mode() == 'online':
            self._speak_online(text)
        else:
            self._speak_offline(text)

    def _speak_offline(self, text):
        # Use espeak-ng
        voice_map = {
            "male_default": "en+m1",
            "female_default": "en+f1",
            "neutral": "en"
        }
        voice = voice_map.get(self.voice, "en")
        speed = int(150 * self.speed)  # espeak-ng speed
        pitch = 50 + self.pitch * 10  # Adjust pitch
        espeak_cmd = self._find_espeak()
        if espeak_cmd:
            cmd = [espeak_cmd, "-v", voice, "-s", str(speed), "-p", str(pitch), "-a", str(self.volume), text]
            try:
                subprocess.run(cmd, check=True)
                return
            except subprocess.CalledProcessError:
                pass
        print("espeak-ng not available, using fallback")
        # Fallback to pyttsx3 if available
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', int(200 * self.speed))
            engine.setProperty('volume', self.volume / 100)
            voices = engine.getProperty('voices')
            if self.voice == "female_default" and len(voices) > 1:
                engine.setProperty('voice', voices[1].id)
            engine.say(text)
            engine.runAndWait()
        except ImportError:
            print("No TTS engine available")

    def _find_espeak(self):
        possible_paths = ['/usr/local/bin/espeak-ng', '/opt/homebrew/bin/espeak-ng', shutil.which('espeak-ng')]
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        return None

    def _speak_online(self, text):
        # Use Hugging Face TTS via Inference API
        hf_key = os.getenv('HUGGINGFACE_API_KEY')
        if hf_key:
            try:
                headers = {"Authorization": f"Bearer {hf_key}"}
                payload = {"inputs": text}
                response = requests.post("https://api-inference.huggingface.co/models/facebook/mms-tts-eng", headers=headers, json=payload)
                if response.status_code == 200:
                    audio_data = response.content
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                        f.write(audio_data)
                        # Play the file
                        if os.name == 'nt':  # Windows
                            os.startfile(f.name)
                        else:  # macOS/Linux
                            subprocess.run(['aplay', f.name])  # Assuming aplay is installed
                        os.unlink(f.name)
                else:
                    print(f"HF TTS error: {response.status_code}")
                    self._speak_offline(text)  # Fallback
            except Exception as e:
                print(f"HF TTS error: {e}")
                self._speak_offline(text)  # Fallback
        else:
            print("Hugging Face API key not set for TTS")
            self._speak_offline(text)  # Fallback