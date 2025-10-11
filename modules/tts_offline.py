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
            'neutral': {'voice': 'en+m1', 'speed': 1.0, 'pitch': 0, 'volume': 80},
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

    def _preprocess_text(self, text):
        """Preprocess text for better TTS"""
        import re

        # Expand abbreviations
        abbreviations = {
            'Dr.': 'Doctor',
            'Mr.': 'Mister',
            'Mrs.': 'Misses',
            'Ms.': 'Miss',
            'vs.': 'versus',
            'etc.': 'et cetera',
            'i.e.': 'that is',
            'e.g.': 'for example',
            'approx.': 'approximately',
            'min.': 'minimum',
            'max.': 'maximum'
        }

        for abbr, full in abbreviations.items():
            text = re.sub(r'\b' + re.escape(abbr) + r'\b', full, text, flags=re.IGNORECASE)

        # Handle numbers (simple cases)
        text = re.sub(r'\b(\d{1,2})\b', lambda m: self._number_to_words(int(m.group(1))), text)

        # Clean up punctuation
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces
        text = re.sub(r'([.!?])\1+', r'\1', text)  # Multiple punctuation

        return text.strip()

    def _number_to_words(self, num):
        """Convert small numbers to words"""
        words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty']
        return words[num] if 0 <= num < len(words) else str(num)

    def stop_speaking(self):
        """Stop current speech"""
        if self.current_process and self.is_speaking:
            try:
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                self.current_process = None
                self.is_speaking = False
                return True
            except:
                pass
        return False

    def speak(self, text, voice=None, speed=None, pitch=None, volume=None, interruptible=True):
        """Enhanced speech synthesis with preprocessing"""
        if not text or not text.strip():
            return

        # Stop any current speech if interruptible
        if interruptible and self.is_speaking:
            self.stop_speaking()

        # Preprocess text for better speech
        processed_text = self._preprocess_text(text)

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
            # Build espeak command with enhanced options
            cmd = [
                'espeak-ng',
                '-v', voice,
                '-s', str(int(175 * speed)),  # Speed in words per minute
                '-p', str(50 + pitch * 10),   # Pitch (0-100, default 50)
                '-a', str(volume),            # Amplitude/volume
                '-g', '2',                    # Word gap
                '-m'                          # Interpret SSML markup
            ]

            # Add text (processed)
            cmd.append(processed_text)

            # Execute in background
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            self.is_speaking = True

            # Monitor process in background
            def monitor_speech():
                if self.current_process:
                    self.current_process.wait()
                self.is_speaking = False
                self.current_process = None

            threading.Thread(target=monitor_speech, daemon=True).start()

        except FileNotFoundError:
            print("espeak-ng not found. Install with: sudo apt install espeak-ng")
        except Exception as e:
            print(f"TTS error: {e}")
            self.is_speaking = False
            # Fallback to print
            print(f"[TTS]: {text}")

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

    def unload_model(self):
        """Unload TTS resources"""
        self.stop()  # Stop any current speech
        # espeak-ng doesn't load large models, so just clean up