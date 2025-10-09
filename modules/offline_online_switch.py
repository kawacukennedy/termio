import os

class OfflineOnlineSwitchModule:
    def __init__(self):
        self.mode = "offline"  # default offline-first

    def switch_to_online(self):
        if os.getenv('OPENAI_API_KEY'):
            self.mode = "online"
        else:
            self.mode = "offline"

    def switch_to_offline(self):
        self.mode = "offline"

    def get_mode(self):
        return self.mode

    def auto_switch(self):
        # If internet available and key set, online; else offline
        if os.getenv('OPENAI_API_KEY'):
            self.mode = "online"
        else:
            self.mode = "offline"