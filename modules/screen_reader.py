import pytesseract
from PIL import Image
import mss

class ScreenReaderModule:
    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'

    def read_screen_area(self, x=0, y=0, width=800, height=600):
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            img = sct.grab(monitor)
            img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            text = pytesseract.image_to_string(img)
            return text

    def summarize_content(self, text):
        # Simple summary
        return text[:200] + "..." if len(text) > 200 else text

    def search_for_keyword(self, text, keyword):
        return keyword.lower() in text.lower()

    def extract_highlighted(self, text):
        # Assume no highlight, return all
        return text