import pytesseract
import pyautogui
from PIL import Image
import time
import cv2
import numpy as np

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

    def summarize(self, text, max_sentences=3):
        """Advanced summarization using extractive methods"""
        if not text:
            return ""

        sentences = [s.strip() for s in text.split('.') if s.strip()]

        if len(sentences) <= max_sentences:
            return text

        # Simple scoring based on length and position
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            # Score based on position (prefer first/last) and length
            position_score = 1.0 if i == 0 or i == len(sentences)-1 else 0.5
            length_score = min(len(sentence.split()) / 20, 1.0)  # Prefer 10-20 word sentences
            total_score = position_score * length_score
            scored_sentences.append((total_score, sentence))

        # Sort by score and take top sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        selected_sentences = [s[1] for s in scored_sentences[:max_sentences]]

        # Return in original order
        result_sentences = []
        for sentence in sentences:
            if sentence in selected_sentences:
                result_sentences.append(sentence)
                selected_sentences.remove(sentence)

        return '. '.join(result_sentences) + '.'

    def highlight_keywords_simple(self, text, keywords):
        # Simple keyword highlighting in text
        for keyword in keywords:
            text = text.replace(keyword, f"**{keyword}**")
        return text

    def search_text(self, text, query):
        return query.lower() in text.lower()

    def capture_region(self, x, y, width, height):
        return self.read_screen(region=(x, y, width, height))

    def recognize_tables(self, image=None):
        """Extract tables from screen or image"""
        if image is None:
            image = pyautogui.screenshot()

        # Convert PIL to OpenCV
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Convert to grayscale
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)

        # Detect tables using contours
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        tables = []
        for contour in contours:
            # Approximate the contour
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            if len(approx) == 4:  # Rectangle
                x, y, w, h = cv2.boundingRect(contour)
                if w > 100 and h > 50:  # Minimum size
                    table_region = image.crop((x, y, x+w, y+h))
                    table_text = pytesseract.image_to_string(table_region)

                    # Parse table (basic CSV-like parsing)
                    lines = [line.strip() for line in table_text.split('\n') if line.strip()]
                    if lines:
                        tables.append({
                            'position': (x, y, w, h),
                            'content': lines
                        })

        return tables

    def highlight_keywords(self, text, keywords, case_sensitive=False):
        """Enhanced keyword highlighting with context"""
        if not case_sensitive:
            text_lower = text.lower()
            keywords_lower = [k.lower() for k in keywords]
        else:
            text_lower = text
            keywords_lower = keywords

        highlighted = text
        for i, keyword in enumerate(keywords):
            if case_sensitive:
                highlighted = highlighted.replace(keyword, f"**{keyword}**")
            else:
                # Case-insensitive replacement
                import re
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                highlighted = pattern.sub(f"**{keyword}**", highlighted)

        return highlighted

    def convert_to_speech(self, text):
        """Convert text to speech (delegate to TTS module)"""
        # This would be called from main app
        return text  # Placeholder

    def get_screen_resolution(self):
        """Get current screen resolution"""
        screen_width, screen_height = pyautogui.size()
        return screen_width, screen_height

    def capture_window(self, window_title=None):
        """Capture specific window content"""
        # This would require additional libraries like pygetwindow
        # For now, return full screen
        return self.read_screen()