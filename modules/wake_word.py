class WakeWordDetectionModule:
    def __init__(self, access_key, keyword='auralis', sensitivity=0.5):
        try:
            from pvporcupine import create
            self.handle = create(access_key=access_key, keywords=[keyword], sensitivities=[sensitivity])
        except ImportError:
            self.handle = None  # Fallback

    def process_audio(self, pcm):
        return self.handle.process(pcm) >= 0