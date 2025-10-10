import pytesseract
import pyautogui
from PIL import Image
import time

class ScreenReaderModule:
    def __init__(self, config):
        self.config = config
        self.capabilities = config['screen_interaction']['screen_reading']['capabilities']
        self.polling_interval = config['screen_interaction']['screen_reading']['polling_interval_ms'] / 1000

    def initialize(self):
        # pytesseract is configured to use tesseract
        pass

    def read_screen(self, region=None):
        # Capture screen or region
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        # OCR
        text = pytesseract.image_to_string(screenshot)
        return text.strip()

    def summarize(self, text):
        # Basic summarization - return first few sentences
        sentences = text.split('.')
        return '.'.join(sentences[:3]) + '.'

    def highlight_keywords(self, text, keywords):
        # Simple keyword highlighting in text
        for keyword in keywords:
            text = text.replace(keyword, f"**{keyword}**")
        return text

    def search_text(self, text, query):
        return query.lower() in text.lower()

    def capture_region(self, x, y, width, height):
        return self.read_screen(region=(x, y, width, height))