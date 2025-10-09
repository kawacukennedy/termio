import pytesseract
from PIL import Image
import mss
import re
import shutil
import os

class ScreenReaderModule:
    def __init__(self, tts_module=None):
        # Check if tesseract is available
        possible_paths = ['/usr/local/bin/tesseract', '/opt/homebrew/bin/tesseract', shutil.which('tesseract')]
        for path in possible_paths:
            if path and os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                self.available = True
                break
        else:
            self.available = False
        self.tts = tts_module

    def read_screen_area(self, x=0, y=0, width=800, height=600):
        if not self.available:
            return "Tesseract not installed"
        with mss.mss() as sct:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            img = sct.grab(monitor)
            img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            text = pytesseract.image_to_string(img)
            return text

    def summarize_content(self, text):
        # Simple summary: first 200 chars or first sentence
        sentences = re.split(r'[.!?]', text)
        summary = sentences[0] if sentences else text[:200]
        return summary + "..." if len(summary) < len(text) else summary

    def search_for_keyword(self, text, keyword):
        return keyword.lower() in text.lower()

    def highlight_keywords(self, text, keywords):
        # Simple highlight by surrounding with **
        for kw in keywords:
            text = re.sub(re.escape(kw), f"**{kw}**", text, flags=re.IGNORECASE)
        return text

    def convert_to_speech(self, text):
        if self.tts:
            self.tts.speak(text)
            return "Converted to speech"
        return "TTS not available"

    def extract_highlighted(self, text):
        # Assume no actual highlight, return all
        return text

    def recognize_tables(self, text):
        # Improved table recognition using regex for tabular data
        import re
        lines = text.split('\n')
        table_lines = []
        for line in lines:
            # Check for multiple separators or structured data
            if re.search(r'(\|.*\|)|(\t.*\t)|( {2,}.* {2,})', line):
                table_lines.append(line)
        return '\n'.join(table_lines) if table_lines else "No tables detected"