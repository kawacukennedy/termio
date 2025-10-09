class WakeWordDetectionModule:
    def __init__(self, access_key, keyword='auralis'):
        from pvporcupine import create
        self.handle = create(access_key=access_key, keywords=[keyword])

    def process_audio(self, pcm):
        return self.handle.process(pcm) >= 0