# Auralis

Auralis is a terminal-based AI assistant providing full offline-first natural voice and text conversation, real-time screen reading and control, push-to-talk voice interaction, optional online enhancements, minimal CPU/GPU usage, and storage under 100MB.

## Installation

1. Install Python 3.11+
2. Install system dependencies:
    - Tesseract OCR: `brew install tesseract` (macOS), `sudo apt install tesseract-ocr` (Linux), or download for Windows
    - espeak-ng for TTS: `brew install espeak-ng` (macOS), `sudo apt install espeak-ng` (Linux)
3. pip install -r requirements.txt
4. Download Vosk STT model: `wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && unzip vosk-model-small-en-us-0.15.zip && mv vosk-model-small-en-us-0.15 model`
 5. Optional: For online mode, get Hugging Face API token from https://huggingface.co/settings/tokens and set `export HUGGINGFACE_API_KEY=your_token`

## Usage

python main.py text  # for text conversation
python main.py voice  # for voice conversation

- Type commands in the terminal interface.
- Use configurable hotkey (default F12) for voice input.
- Type 'quit' to exit.

## Features

### Offline Mode (Default)
- Fully functional AI conversation without internet
- Lightweight NLP with MicroGPT/TinyGPT (~50MB)
- STT with Vosk ultra-light (~20MB), CPU-only
- TTS with espeak-ng (~5MB), CPU-only
- Screen reading with Tesseract minimal (~20MB)
- Screen control with PyAutoGUI lightweight (~5MB)
- Conversation memory: last 3 interactions in RAM
- Push-to-talk voice input
- Natural spoken dialogue support

### Online Mode (Optional)
- Advanced reasoning with OpenAI GPT-3.5/4
- High-accuracy STT with Google or Whisper API
- Human-like TTS with ElevenLabs or Google TTS
- Long-term memory and complex tasks
- Auto-switch to offline if no internet

### Screen Interaction
- Read text from terminal/GUI apps
- Summarize content
- Highlight keywords
- Convert screen text to speech
- Search for specific text
- Recognize tables and prompts
- Mouse/keyboard control with confirmations for destructive actions

### Terminal UI
- Minimal ASCII interface
- Optional waveform visualization for voice input
- Toggleable chat history
- Dark/light ASCII themes
- Command suggestions and hints
- Real-time activity indicators

### Extensibility
- Plugin system for custom commands (<1MB each)
- Examples: calculator, weather, music control

### Security & Privacy
- 100% local processing in offline mode
- Encrypted long-term memory
- User controls for permissions and data clearing

## Example Commands

### Voice
- Press F12, then say "what time is it?"
- Press F12, then say "type 'Hello' in terminal"
- Press F12, then say "read this section"
- Press F12, then say "summarize output"
- Press F12, then say "close this window"
- Press F12, then say "search screen for 'error'"
- Press F12, then say "open browser and go to 'example.com'"
- Press F12, then say "tell me a joke"
- Press F12, then say "explain this output to me"

### Text
- "Explain basic math"
- "Tell a joke"
- "Translate 'Hola' to English"
- "Summarize last terminal output"
- "Open browser"
- "Define 'quantum computing'"
- "Provide a summary of this document"

## Storage & Performance

- Total storage: <100MB including models
- Minimum RAM: 2GB, CPU: dual-core 1.5GHz
- Logs compressed in gzip, rotatable
- Lazy-loading modules, idle sleep, low CPU usage
- Sub-100ms wake word response

## Configuration

Edit `config.json` to customize settings like hotkeys, voices, sensitivities, etc.

## Online APIs

For online mode, use Hugging Face Inference API (free tier: ~30 requests/minute for NLP, STT, TTS).

Set `HUGGINGFACE_API_KEY`. Note rate limits.