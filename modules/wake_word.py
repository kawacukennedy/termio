class WakeWordDetectionModule:
    def __init__(self, access_key, keyword='auralis', sensitivity=0.5):
        from pvporcupine import create
        self.handle = create(access_key=access_key, keywords=[keyword], sensitivities=[sensitivity])

    def process_audio(self, pcm):
        return self.handle.process(pcm) >= 0