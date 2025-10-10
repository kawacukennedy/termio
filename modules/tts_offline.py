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

    def speak(self, text, voice='neutral', speed=1.0, pitch=0, volume=80):
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
            espeak_voice = voice_map.get(voice, 'en')

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