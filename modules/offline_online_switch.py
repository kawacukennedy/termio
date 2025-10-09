import os
import asyncio
import requests

class OfflineOnlineSwitchModule:
    def __init__(self):
        self.mode = "offline"  # default offline-first
        self.low_bandwidth = True  # Compress requests if possible
        self.async_enabled = True

    def switch_to_online(self):
        if self._has_internet() and os.getenv('HUGGINGFACE_API_KEY'):
            self.mode = "online"
        else:
            self.mode = "offline"

    def switch_to_offline(self):
        self.mode = "offline"

    def get_mode(self):
        return self.mode

    def auto_switch(self):
        # If internet available and key set, online; else offline
        if self._has_internet() and os.getenv('HUGGINGFACE_API_KEY'):
            self.mode = "online"
        else:
            self.mode = "offline"

    def _has_internet(self):
        try:
            requests.get('https://www.google.com', timeout=1)
            return True
        except:
            return False

    async def process_online_async(self, func, *args, **kwargs):
        if self.async_enabled and self.mode == 'online':
            return await asyncio.to_thread(func, *args, **kwargs)
        else:
            return func(*args, **kwargs)