# Auralis

A terminal-based AI assistant with offline-first capabilities.

## Installation

1. Install Python 3.11+
2. Install system dependencies:
   - Tesseract OCR: `brew install tesseract` (macOS), `sudo apt install tesseract-ocr` (Linux), or download for Windows
   - espeak-ng for TTS: `brew install espeak-ng` (macOS), `sudo apt install espeak-ng` (Linux)
3. pip install -r requirements.txt
4. Download Vosk STT model: `wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && unzip vosk-model-small-en-us-0.15.zip && mv vosk-model-small-en-us-0.15 model`
5. Get Picovoice access key from https://console.picovoice.ai/ and set env var: `export PICOVOICE_ACCESS_KEY=your_key`
6. Optional: For online mode, `export OPENAI_API_KEY=your_openai_key` or `export HUGGINGFACE_API_KEY=your_hf_key` for free alternatives (Hugging Face Inference API with rate limits)

## Usage

python main.py

- Type commands in the terminal interface.
- Use F12 for push-to-talk voice input.
- Wake word "Auralis" activates voice listening (if access key set).
- Type 'quit' to exit.

## Features

- Offline-first NLP with lightweight GPT model
- Text-to-speech with espeak-ng
- Speech-to-text with Vosk
- Wake word detection with Porcupine
- Screen reading with Tesseract OCR
- Screen control with PyAutoGUI
- Conversation memory (last 3 turns)
- Compressed logging
- Terminal UI with curses
- Online fallback to OpenAI GPT or Hugging Face (free tier available)
- Commands: read screen, type text, click at coordinates, time, etc.
- Push-to-talk and continuous listening modes

## Storage

Under 100MB including models. Logs compressed in gzip.

## Alternative APIs

For online mode, instead of OpenAI, you can use free or open-source alternatives:

- **NLP**: Hugging Face Inference API (free tier: ~30 requests/minute, requires API key from huggingface.co)
- **STT**: Hugging Face Whisper via Inference API (same free tier)
- **TTS**: Hugging Face Bark or eSpeak models (same free tier)

Set `HUGGINGFACE_API_KEY` instead of `OPENAI_API_KEY`. Note rate limits and model availability.