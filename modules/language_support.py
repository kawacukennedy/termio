import os
import json
from pathlib import Path

class LanguageSupportModule:
    def __init__(self, config):
        self.config = config
        self.current_language = 'en'
        self.supported_languages = {
            'en': {'name': 'English', 'code': 'en-US'},
            'es': {'name': 'Spanish', 'code': 'es-ES'},
            'fr': {'name': 'French', 'code': 'fr-FR'},
            'de': {'name': 'German', 'code': 'de-DE'},
            'it': {'name': 'Italian', 'code': 'it-IT'},
            'pt': {'name': 'Portuguese', 'code': 'pt-BR'},
            'ja': {'name': 'Japanese', 'code': 'ja-JP'},
            'ko': {'name': 'Korean', 'code': 'ko-KR'},
            'zh': {'name': 'Chinese', 'code': 'zh-CN'},
            'ru': {'name': 'Russian', 'code': 'ru-RU'},
            'ar': {'name': 'Arabic', 'code': 'ar-SA'}
        }

        # Language-specific responses and commands
        self.translations = self._load_translations()

    def _load_translations(self):
        """Load translation files"""
        translations = {}
        translations_dir = Path('translations')

        if translations_dir.exists():
            for lang_file in translations_dir.glob('*.json'):
                lang_code = lang_file.stem
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"Failed to load translations for {lang_code}: {e}")

        # Default English translations
        translations['en'] = {
            'greeting': 'Hello! How can I help you?',
            'goodbye': 'Goodbye!',
            'wake_word': 'Auralis',
            'listening': 'Listening...',
            'processing': 'Processing...',
            'error_misheard': 'Sorry, I didn\'t catch that. Could you repeat?',
            'error_unknown': 'I\'m not sure how to help with that.',
            'error_ocr': 'Unable to read the screen content.',
            'error_denied': 'Action denied for security reasons.',
            'commands': {
                'read_screen': 'read screen',
                'summarize': 'summarize output',
                'search_screen': 'search screen for',
                'close_window': 'close window',
                'weather': 'weather',
                'news': 'news',
                'joke': 'tell me a joke',
                'quote': 'inspire me',
                'time': 'what time is it',
                'help': 'what can you do'
            }
        }

        return translations

    def set_language(self, lang_code):
        """Set the current language"""
        if lang_code in self.supported_languages:
            self.current_language = lang_code
            return f"Language set to {self.supported_languages[lang_code]['name']}"
        else:
            return f"Unsupported language: {lang_code}. Available: {', '.join(self.supported_languages.keys())}"

    def get_current_language(self):
        """Get current language info"""
        return {
            'code': self.current_language,
            'name': self.supported_languages.get(self.current_language, {}).get('name', 'Unknown'),
            'full_code': self.supported_languages.get(self.current_language, {}).get('code', 'en-US')
        }

    def translate(self, key, lang=None):
        """Translate a key to specified or current language"""
        target_lang = lang or self.current_language

        if target_lang in self.translations:
            keys = key.split('.')
            value = self.translations[target_lang]
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                pass

        # Fallback to English
        if 'en' in self.translations:
            keys = key.split('.')
            value = self.translations['en']
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                pass

        return key  # Return key if no translation found

    def get_supported_languages(self):
        """Get list of supported languages"""
        return {code: info['name'] for code, info in self.supported_languages.items()}

    def detect_language(self, text):
        """Basic language detection (simplified)"""
        # This is a very basic implementation
        # In a real system, you'd use a proper language detection library

        text_lower = text.lower()

        # Simple keyword-based detection
        language_indicators = {
            'es': ['hola', 'gracias', 'por favor', 'sí', 'no', 'qué', 'cómo'],
            'fr': ['bonjour', 'merci', 's\'il vous plaît', 'oui', 'non', 'quoi', 'comment'],
            'de': ['hallo', 'danke', 'bitte', 'ja', 'nein', 'was', 'wie'],
            'it': ['ciao', 'grazie', 'per favore', 'sì', 'no', 'che', 'come'],
            'pt': ['olá', 'obrigado', 'por favor', 'sim', 'não', 'que', 'como'],
            'ja': ['こんにちは', 'ありがとう', 'お願いします', 'はい', 'いいえ'],
            'ko': ['안녕하세요', '감사합니다', '주세요', '네', '아니요'],
            'zh': ['你好', '谢谢', '请', '是', '不是'],
            'ru': ['привет', 'спасибо', 'пожалуйста', 'да', 'нет'],
            'ar': ['مرحبا', 'شكرا', 'من فضلك', 'نعم', 'لا']
        }

        max_matches = 0
        detected_lang = 'en'

        for lang, indicators in language_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in text_lower)
            if matches > max_matches:
                max_matches = matches
                detected_lang = lang

        return detected_lang if max_matches > 0 else 'en'

    def get_language_specific_responses(self, intent, lang=None):
        """Get language-specific responses for common intents"""
        target_lang = lang or self.current_language

        # Common responses in different languages
        responses = {
            'greeting': {
                'en': ['Hello!', 'Hi there!', 'Greetings!'],
                'es': ['¡Hola!', '¡Buenos días!', '¡Saludos!'],
                'fr': ['Bonjour!', 'Salut!', 'Bienvenue!'],
                'de': ['Hallo!', 'Guten Tag!', 'Grüß Gott!'],
                'it': ['Ciao!', 'Buongiorno!', 'Salve!'],
                'pt': ['Olá!', 'Oi!', 'Bem-vindo!'],
                'ja': ['こんにちは！', 'こんにちは！', 'ようこそ！'],
                'ko': ['안녕하세요!', '안녕하세요!', '환영합니다!'],
                'zh': ['你好！', '您好！', '欢迎！'],
                'ru': ['Привет!', 'Здравствуйте!', 'Добро пожаловать!'],
                'ar': ['مرحبا!', 'أهلاً!', 'أهلاً وسهلاً!']
            },
            'confirmation': {
                'en': ['Got it!', 'Understood!', 'Confirmed!'],
                'es': ['¡Entendido!', '¡Confirmado!', '¡Claro!'],
                'fr': ['Compris!', 'Confirmé!', 'D\'accord!'],
                'de': ['Verstanden!', 'Bestätigt!', 'Klar!'],
                'it': ['Capito!', 'Confermato!', 'Certo!'],
                'pt': ['Entendido!', 'Confirmado!', 'Claro!'],
                'ja': ['わかりました！', '確認しました！', 'はい！'],
                'ko': ['알겠습니다!', '확인했습니다!', '네!'],
                'zh': ['明白了！', '确认了！', '好的！'],
                'ru': ['Понятно!', 'Подтверждено!', 'Хорошо!'],
                'ar': ['فهمت!', 'مؤكد!', 'حسناً!']
            },
            'error': {
                'en': ['I\'m sorry, I didn\'t understand.', 'Could you please repeat that?'],
                'es': ['Lo siento, no entendí.', '¿Podrías repetirlo?'],
                'fr': ['Désolé, je n\'ai pas compris.', 'Pourriez-vous répéter?'],
                'de': ['Entschuldigung, ich habe nicht verstanden.', 'Könnten Sie das wiederholen?'],
                'it': ['Mi dispiace, non ho capito.', 'Potresti ripetere?'],
                'pt': ['Desculpe, não entendi.', 'Pode repetir?'],
                'ja': ['すみません、わかりませんでした。', 'もう一度言っていただけますか？'],
                'ko': ['죄송합니다, 이해하지 못했습니다.', '다시 말씀해 주시겠어요?'],
                'zh': ['对不起，我没听懂。', '您能重复一遍吗？'],
                'ru': ['Извините, я не понял.', 'Не могли бы вы повторить?'],
                'ar': ['عذراً، لم أفهم.', 'هل يمكنك التكرار؟']
            }
        }

        if intent in responses and target_lang in responses[intent]:
            import random
            return random.choice(responses[intent][target_lang])

        # Fallback to English
        return responses.get(intent, {}).get('en', [''])[0]

    def create_translation_file(self, lang_code):
        """Create a basic translation file template"""
        if lang_code not in self.supported_languages:
            return f"Unsupported language: {lang_code}"

        translations_dir = Path('translations')
        translations_dir.mkdir(exist_ok=True)

        template = {
            "greeting": f"Hello in {self.supported_languages[lang_code]['name']}!",
            "goodbye": f"Goodbye in {self.supported_languages[lang_code]['name']}!",
            "wake_word": "Auralis",
            "listening": "Listening...",
            "processing": "Processing...",
            "error_misheard": "Sorry, I didn't catch that. Could you repeat?",
            "error_unknown": "I'm not sure how to help with that.",
            "error_ocr": "Unable to read the screen content.",
            "error_denied": "Action denied for security reasons.",
            "commands": {
                "read_screen": "read screen",
                "summarize": "summarize output",
                "search_screen": "search screen for",
                "close_window": "close window",
                "weather": "weather",
                "news": "news",
                "joke": "tell me a joke",
                "quote": "inspire me",
                "time": "what time is it",
                "help": "what can you do"
            }
        }

        file_path = translations_dir / f"{lang_code}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)

        return f"Translation template created: {file_path}"