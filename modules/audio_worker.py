#!/usr/bin/env python3
"""
Audio I/O Worker as per microarchitecture spec.
Handles audio capture, wakeword detection, push-to-talk capture, chunking for STT.
"""

import time
import threading
import pyaudio
import numpy as np
import logging

class AudioWorker:
    def __init__(self, config, queues):
        self.config = config
        self.queues = queues
        self.logger = logging.getLogger('audio_worker')

        # Audio settings
        self.chunk_size = 1024
        self.sample_rate = 16000
        self.channels = 1
        self.format = pyaudio.paInt16

        # Wakeword detection
        self.wakeword_enabled = config.get('wakeword', {}).get('enabled', False)
        self.wakeword_phrase = config.get('wakeword', {}).get('phrase', 'Auralis')

        # Push-to-talk
        self.ptt_active = False
        self.ptt_key = config.get('push_to_talk', {}).get('key', 'space')

        # Audio stream
        self.audio = None
        self.stream = None

    def run(self):
        """Main worker loop"""
        self.logger.info("Audio worker starting...")

        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )

            # Start wakeword detection if enabled
            if self.wakeword_enabled:
                threading.Thread(target=self._wakeword_loop, daemon=True).start()

            # Start push-to-talk monitoring
            threading.Thread(target=self._ptt_monitor_loop, daemon=True).start()

            # Main audio capture loop
            self._audio_capture_loop()

        except Exception as e:
            self.logger.error(f"Audio worker error: {e}")
        finally:
            self._cleanup()

    def _audio_capture_loop(self):
        """Main audio capture and processing loop with spec chunking"""
        chunk_duration_ms = 1200  # 1200ms chunks as per spec
        overlap_ms = 200  # 200ms overlap
        samples_per_chunk = int(self.sample_rate * chunk_duration_ms / 1000)
        samples_overlap = int(self.sample_rate * overlap_ms / 1000)

        buffer = np.array([], dtype=np.int16)

        while True:
            try:
                # Read audio data
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)

                # Accumulate in buffer
                buffer = np.concatenate([buffer, audio_chunk])

                # Process chunks when we have enough data
                while len(buffer) >= samples_per_chunk:
                    # Extract chunk with overlap
                    chunk = buffer[:samples_per_chunk]

                    # Send to STT queue if PTT active or wakeword detected
                    if self.ptt_active or hasattr(self, 'wakeword_active') and self.wakeword_active:
                        source = 'ptt' if self.ptt_active else 'wakeword'
                        self.queues['audio->stt'].put({
                            'type': 'audio_chunk',
                            'data': chunk.tobytes(),
                            'timestamp': time.time(),
                            'source': source,
                            'chunk_duration_ms': chunk_duration_ms
                        })

                    # Remove processed samples, keeping overlap
                    buffer = buffer[samples_per_chunk - samples_overlap:]

            except Exception as e:
                self.logger.error(f"Audio capture error: {e}")
                time.sleep(0.1)

    def _wakeword_loop(self):
        """Wakeword detection loop"""
        self.logger.info("Wakeword detection enabled")

        while True:
            try:
                # Simple wakeword detection (placeholder - integrate with Porcupine)
                # For now, just listen for silence breaks
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)

                # Check for wakeword (simplified)
                if self._detect_wakeword(audio_chunk):
                    self.logger.info("Wakeword detected!")
                    self.queues['audio->stt'].put({
                        'type': 'wakeword_detected',
                        'timestamp': time.time()
                    })

                    # Start capture window (4 seconds)
                    self._capture_after_wakeword()

            except Exception as e:
                self.logger.error(f"Wakeword detection error: {e}")
                time.sleep(0.1)

    def _detect_wakeword(self, audio_chunk):
        """Simple wakeword detection (placeholder)"""
        # Calculate RMS amplitude
        rms = np.sqrt(np.mean(audio_chunk**2))

        # Threshold for "wakeword" (just loud enough sound)
        threshold = 500  # Adjust based on microphone

        return rms > threshold

    def _capture_after_wakeword(self):
        """Capture audio after wakeword detection"""
        start_time = time.time()
        capture_duration = 4.0  # 4 seconds as per spec

        while time.time() - start_time < capture_duration:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_chunk = np.frombuffer(data, dtype=np.int16)

                self.queues['audio->stt'].put({
                    'type': 'audio_chunk',
                    'data': audio_chunk.tobytes(),
                    'timestamp': time.time(),
                    'source': 'wakeword'
                })

                time.sleep(0.01)  # Small delay

            except Exception as e:
                self.logger.error(f"Wakeword capture error: {e}")
                break

    def _ptt_monitor_loop(self):
        """Monitor for push-to-talk key presses with spec-compliant timing"""
        try:
            import keyboard

            def on_ptt_press():
                start_time = time.time()
                self.ptt_active = True
                self.logger.info("Push-to-talk activated")

                # UI feedback: 0-20ms status_bar.mic set ON; small click sound
                self.queues['audio->stt'].put({
                    'type': 'ptt_start',
                    'timestamp': start_time
                })

            def on_ptt_release():
                end_time = time.time()
                self.ptt_active = False
                self.logger.info("Push-to-talk deactivated")

                # Signal end of PTT capture
                self.queues['audio->stt'].put({
                    'type': 'ptt_end',
                    'timestamp': end_time
                })

            keyboard.on_press_key(self.ptt_key, lambda _: on_ptt_press())
            keyboard.on_release_key(self.ptt_key, lambda _: on_ptt_release())

            # Keep thread alive
            keyboard.wait()

        except ImportError:
            self.logger.warning("keyboard module not available, PTT disabled")

    def _cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()