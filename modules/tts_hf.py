import requests
import io
import pygame
import time

class TTSModuleHFAPI:
    def __init__(self, config, security_module=None):
        self.config = config
        self.security = security_module
        self.api_url = "https://api-inference.huggingface.co/models/espnet/kan-bayashi_ljspeech_vits"
        self.headers = {}
        self.current_profile = 'neutral'
        self.profiles = {
            'formal': {'voice': 'en+m3'},
            'casual': {'voice': 'en+m2'},
            'energetic': {'voice': 'en+f2'}
        }

    def initialize(self):
        token = self.security.get_api_key("huggingface") if self.security else None
        if token:
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            print("Warning: No HuggingFace token configured for TTS")

    def speak(self, text, voice=None, speed=None, pitch=None, volume=None, interruptible=True):
        """Synthesize speech using HF Inference API"""
        try:
            payload = {"inputs": text}

            response = requests.post(self.api_url, headers=self.headers, json=payload)
            if response.status_code == 200:
                audio_bytes = response.content
                # Play audio using pygame
                pygame.mixer.init()
                audio_stream = io.BytesIO(audio_bytes)
                pygame.mixer.music.load(audio_stream)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                pygame.mixer.quit()
            else:
                print(f"HF TTS API error: {response.status_code} - {response.text}")
                print(f"[TTS]: {text}")
        except Exception as e:
            print(f"HF TTS failed: {e}")
            print(f"[TTS]: {text}")

    def set_voice_profile(self, profile_name):
        """Set voice profile"""
        if profile_name in self.profiles:
            self.current_profile = profile_name
            return f"Voice profile set to {profile_name}"
        else:
            return f"Unknown profile: {profile_name}"

    def get_voice_profiles(self):
        """Get available voice profiles"""
        return list(self.profiles.keys())

    def customize_voice(self, voice=None, speed=None, pitch=None, volume=None):
        """Customize voice parameters"""
        if voice:
            self.profiles[self.current_profile]['voice'] = voice
        # HF TTS may not support all customizations
        return f"Voice customized (limited support in HF TTS)"

    def stop(self):
        """Stop current speech"""
        try:
            pygame.mixer.music.stop()
        except:
            pass

    def unload_model(self):
        """Unload resources"""
        self.stop()