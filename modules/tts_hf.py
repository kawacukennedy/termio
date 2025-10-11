import time

try:
    from transformers import pipeline
    import sounddevice as sd
    import numpy as np
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("Warning: HF TTS dependencies not available")

class TTSModuleHFAPI:
    def __init__(self, config):
        self.config = config
        self.synthesizer = None
        self.current_profile = 'neutral'
        self.profiles = {
            'formal': {'voice': 'en+m3'},
            'casual': {'voice': 'en+m2'},
            'energetic': {'voice': 'en+f2'}
        }

    def initialize(self):
        if not DEPENDENCIES_AVAILABLE:
            return
        try:
            # Use a TTS model from HF
            self.synthesizer = pipeline("text-to-speech", model="microsoft/speecht5_tts")
        except Exception as e:
            print(f"HF TTS initialization failed: {e}")

    def speak(self, text, voice=None, speed=None, pitch=None, volume=None, interruptible=True):
        """Synthesize speech using HF model"""
        if not self.synthesizer:
            print(f"[TTS]: {text}")
            return

        try:
            # Generate speech
            result = self.synthesizer(text)

            # Play audio
            audio = result["audio"]
            sample_rate = result["sampling_rate"]

            # Convert to numpy array if needed
            if isinstance(audio, list):
                audio = np.array(audio)

            sd.play(audio, samplerate=sample_rate)
            sd.wait()
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
            sd.stop()
        except:
            pass

    def unload_model(self):
        """Unload the model"""
        self.stop()
        if self.synthesizer:
            del self.synthesizer
            self.synthesizer = None
        import gc
        gc.collect()