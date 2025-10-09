# Auralis

Auralis is a terminal-based AI assistant providing full offline-first natural voice and text conversation, real-time screen reading and control, push-to-talk voice interaction, optional online enhancements, minimal CPU/GPU usage, and storage under 100MB.

## Installation

1. Install Python 3.11+
2. Install system dependencies:
    - Tesseract OCR: `brew install tesseract` (macOS), `sudo apt install tesseract-ocr` (Linux), or download for Windows
    - espeak-ng for TTS: `brew install espeak-ng` (macOS), `sudo apt install espeak-ng` (Linux)
3. pip install -r requirements.txt
4. Download Vosk STT model: `wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && unzip vosk-model-small-en-us-0.15.zip && mv vosk-model-small-en-us-0.15 model`
5. Get Picovoice access key from https://console.picovoice.ai/ and set env var: `export PICOVOICE_ACCESS_KEY=your_key`
6. Optional: For online mode, `export OPENAI_API_KEY=your_openai_key`, `export HUGGINGFACE_API_KEY=your_hf_key` for free alternatives, or `export GOOGLE_API_KEY` for Google STT/TTS

## Usage

python main.py

- Type commands in the terminal interface.
- Use configurable hotkey (default F12) for push-to-talk voice input.
- Wake word "Auralis" activates voice listening (if access key set).
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
- Wake word detection with Porcupine ultra-light (~1MB)
- Push-to-talk and continuous listening modes
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
- "Auralis, what time is it?"
- "Auralis, type 'Hello' in terminal"
- "Auralis, read this section"
- "Auralis, summarize output"
- "Auralis, close this window"
- "Auralis, search screen for 'error'"
- "Auralis, open browser and go to 'example.com'"
- "Auralis, tell me a joke"
- "Auralis, explain this output to me"

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

## Alternative APIs

For online mode, free alternatives available:

- **NLP**: Hugging Face Inference API (free tier: ~30 requests/minute)
- **STT**: Google STT API or Hugging Face Whisper
- **TTS**: ElevenLabs or Google TTS

Set appropriate API keys. Note rate limits.