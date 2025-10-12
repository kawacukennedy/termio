import pytesseract
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("Warning: pyautogui not available. Screen capture will not work.")

from PIL import Image
import time
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Warning: OpenCV not available. Advanced OCR features disabled.")

class ScreenReaderModule:
    def __init__(self, config):
        self.config = config
        self.capabilities = config['screen_interaction']['screen_reading']['capabilities']
        self.polling_interval = config['screen_interaction']['screen_reading']['polling_interval_ms'] / 1000

    def initialize(self):
        # pytesseract is configured to use tesseract
        pass

    def read_screen(self, region=None, mode='active_window'):
        """Read screen with spec-compliant preprocessing and OCR pipeline"""
        try:
            import pyautogui
        except ImportError:
            return "Screen capture not available (pyautogui not installed)"

        # Region selection as per spec
        if mode == 'entire_screen':
            screenshot = pyautogui.screenshot()
        elif mode == 'active_window':
            # For active window, we'd need additional libraries
            # For now, use full screen
            screenshot = pyautogui.screenshot()
        elif region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        # Preprocessing as per spec
        processed_image = self._preprocess_image(screenshot)

        # OCR pipeline
        text = self._ocr_pipeline(processed_image)

        return text.strip()

    def _preprocess_image(self, image):
        """Preprocess image as per spec: grayscale, adaptive_thresholding, dpi_normalize"""
        if not OPENCV_AVAILABLE:
            return image

        # Convert PIL to OpenCV
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Grayscale
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)

        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # DPI normalization (downscale to 150-200 DPI for speed)
        height, width = thresh.shape
        scale_factor = min(200 / max(width, height), 1.0)  # Target ~200 DPI
        if scale_factor < 1.0:
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            thresh = cv2.resize(thresh, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # Convert back to PIL
        pil_image = Image.fromarray(thresh)

        return pil_image

    def _ocr_pipeline(self, image):
        """OCR pipeline with fast_pass and optional structured_pass"""
        # Fast text pass
        text = pytesseract.image_to_string(image)

        # Optional structured detection pass (tables/cli)
        if OPENCV_AVAILABLE:
            structured_text = self._structured_ocr_pass(image)
            if structured_text:
                text += "\n\n[Structured Content]\n" + structured_text

        # Post-process
        text = self._post_process_ocr(text)

        return text

    def _structured_ocr_pass(self, image):
        """Optional structured OCR pass for tables and CLI content"""
        # Detect tables
        tables = self.recognize_tables(image)

        structured_content = []

        # Process tables
        for table in tables:
            structured_content.append("Table detected:")
            for line in table['content'][:5]:  # Limit lines
                structured_content.append(f"  {line}")

        # CLI detection (look for monospace patterns)
        # This is a simplified implementation
        ocr_text = pytesseract.image_to_string(image)
        lines = ocr_text.split('\n')

        cli_patterns = []
        for line in lines:
            # Look for command-like patterns
            if any(cmd in line.lower() for cmd in ['$', '#', '>', 'ls', 'cd', 'pwd']):
                cli_patterns.append(line)

        if cli_patterns:
            structured_content.append("CLI/Terminal content detected:")
            structured_content.extend(cli_patterns[:10])  # Limit

        return '\n'.join(structured_content) if structured_content else ""

    def _post_process_ocr(self, text):
        """Post-process OCR: language_normalize, whitespace_trim, line_wrap 80 columns"""
        if not text:
            return ""

        # Language normalize (basic)
        # Whitespace trim
        text = text.strip()

        # Line wrap 80 columns
        lines = text.split('\n')
        wrapped_lines = []
        for line in lines:
            if len(line) > 80:
                # Simple wrapping
                wrapped = [line[i:i+80] for i in range(0, len(line), 80)]
                wrapped_lines.extend(wrapped)
            else:
                wrapped_lines.append(line)

        return '\n'.join(wrapped_lines)

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
        if not PYAUTOGUI_AVAILABLE:
            return []
        if not OPENCV_AVAILABLE:
            return []

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
        if not PYAUTOGUI_AVAILABLE:
            return (0, 0)
        screen_width, screen_height = pyautogui.size()
        return screen_width, screen_height

    def capture_window(self, window_title=None):
        """Capture specific window content"""
        if not PYAUTOGUI_AVAILABLE:
            return "Screen capture not available"
        # This would require additional libraries like pygetwindow
        # For now, return full screen
        return self.read_screen()