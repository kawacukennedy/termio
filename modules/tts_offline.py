import subprocess
import os
import signal
import threading

class TTSModuleOffline:
    def __init__(self, config):
        self.config = config
        self.voice_settings = config['voice_interface']['voice_response']
        self.current_process = None
        self.is_speaking = False
        self.current_profile = 'neutral'

        # Voice profiles
        self.profiles = {
            'formal': {'voice': 'en+m3', 'speed': 0.9, 'pitch': -1, 'volume': 85},
            'casual': {'voice': 'en+m2', 'speed': 1.0, 'pitch': 0, 'volume': 90},
            'energetic': {'voice': 'en+f2', 'speed': 1.1, 'pitch': 2, 'volume': 95}
        }



    def set_voice_profile(self, profile_name):
        """Set voice profile"""
        if profile_name in self.profiles:
            self.current_profile = profile_name
            return f"Voice profile set to {profile_name}"
        else:
            return f"Unknown profile: {profile_name}. Available: {', '.join(self.profiles.keys())}"

    def get_voice_profiles(self):
        """Get available voice profiles"""
        return list(self.profiles.keys())

    def customize_voice(self, voice=None, speed=None, pitch=None, volume=None):
        """Customize voice parameters"""
        if voice:
            self.profiles[self.current_profile]['voice'] = voice
        if speed:
            self.profiles[self.current_profile]['speed'] = max(0.5, min(2.0, speed))
        if pitch:
            self.profiles[self.current_profile]['pitch'] = max(-3, min(3, pitch))
        if volume:
            self.profiles[self.current_profile]['volume'] = max(0, min(100, volume))

        return f"Voice customized: {self.profiles[self.current_profile]}"

    def speak(self, text, voice=None, speed=None, pitch=None, volume=None):
        # Use profile settings or overrides
        profile = self.profiles.get(self.current_profile, self.profiles['neutral'])

        voice = voice or profile['voice']
        speed = speed if speed is not None else profile['speed']
        pitch = pitch if pitch is not None else profile['pitch']
        volume = volume if volume is not None else profile['volume']

        # Stop any current speech
        self.stop()

        # Use espeak-ng for TTS
        try:
            # Map voice to espeak voice
            voice_map = {
                'male': 'en+m1',
                'female': 'en+f1',
                'neutral': 'en'
            }
            espeak_voice = voice_map.get(voice, voice)  # Allow custom voices

            # Adjust speed (80-450 wpm, default 175)
            speed_wpm = int(175 * speed)
            speed_wpm = max(80, min(450, speed_wpm))

            # Adjust pitch (-3 to +3, map to -10% to +10%)
            pitch_percent = pitch * 10

            # Volume 0-100
            volume = max(0, min(100, volume))

            cmd = [
                'espeak-ng',
                '-v', espeak_voice,
                '-s', str(speed_wpm),
                '-p', str(50 + pitch_percent),  # pitch 0-100
                '-a', str(volume),
                text
            ]

            self.is_speaking = True
            self.current_process = subprocess.Popen(cmd)
            self.current_process.wait()
            self.is_speaking = False
        except Exception as e:
            print(f"TTS error: {e}")
            # Fallback to print
            print(f"[TTS]: {text}")
            self.is_speaking = False

    def stop(self):
        """Stop current speech"""
        if self.current_process and self.is_speaking:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=0.1)
            except:
                try:
                    self.current_process.kill()
                except:
                    pass
            self.is_speaking = False
            self.current_process = None