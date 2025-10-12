import requests
import io
import pygame
import time

class TTSModuleHFAPI:
    def __init__(self, config, security_module=None):
        self.config = config
        self.security = security_module
        # Use HiFi-GAN / lightweight vocoders as per spec
        self.api_url = "https://api-inference.huggingface.co/models/facebook/mms-tts-eng"
        self.headers = {}
        self.current_profile = 'neutral'
        self.cloud_mode_enabled = False
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

        # Check if cloud mode is enabled
        self.cloud_mode_enabled = self.config.get('user_settings', {}).get('cloud_mode', False)
        if not self.cloud_mode_enabled:
            print("Cloud mode not enabled. HF TTS will not be used.")

    def speak(self, text, voice=None, speed=None, pitch=None, volume=None, interruptible=True):
        """Synthesize speech using HF Inference API with streaming and security"""
        if not self.cloud_mode_enabled:
            print(f"[TTS]: {text}")
            return

        try:
            # Redact sensitive data from text
            redacted_text = self._redact_sensitive_data(text)

            payload = {
                "inputs": redacted_text,
                "options": {"use_cache": True, "wait_for_model": False}
            }

            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            if response.status_code == 200:
                audio_bytes = response.content

                # Play audio using pygame with streaming support
                try:
                    pygame.mixer.init(frequency=22050)  # Common sample rate for TTS
                    audio_stream = io.BytesIO(audio_bytes)
                    pygame.mixer.music.load(audio_stream)
                    pygame.mixer.music.play()

                    # Wait for playback to complete or interruption
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                        if interruptible and self._check_interrupt():
                            pygame.mixer.music.stop()
                            break

                    pygame.mixer.quit()
                except Exception as audio_error:
                    print(f"Audio playback failed: {audio_error}")
                    print(f"[TTS]: {text}")
            else:
                print(f"HF TTS API error: {response.status_code} - {response.text}")
                print(f"[TTS]: {text}")
        except requests.exceptions.Timeout:
            print("HF TTS request timed out")
            print(f"[TTS]: {text}")
        except Exception as e:
            print(f"HF TTS failed: {e}")
            print(f"[TTS]: {text}")

    def _redact_sensitive_data(self, text):
        """Redact sensitive data before TTS"""
        import re

        # Similar redaction as NLP
        redacted = text
        redacted = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email address]', redacted)
        redacted = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[phone number]', redacted)
        redacted = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP address]', redacted)

        return redacted

    def _check_interrupt(self):
        """Check for TTS interruption (SPACE key or 'stop' command)"""
        # This would be integrated with the UI interrupt system
        # For now, return False
        return False

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