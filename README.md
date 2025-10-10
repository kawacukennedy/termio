# Auralis 🤖

*Auralis is a Jarvis-inspired terminal AI assistant with offline-first neural core, voice conversation, screen reading/control, HuggingFace API augmentation, and minimal footprint (<100MB).*

**Your intelligent, conversational, desktop AI companion.**

## ✨ Features

### 🎤 Voice Interface
- **Wake Word Detection**: Responds to "Auralis" using Porcupine ultra-light engine
- **Push-to-Talk**: Hold SPACE key for voice input with visual feedback
- **Offline STT**: Vosk tiny model (~20MB) for speech-to-text
- **Online STT**: HuggingFace Whisper for enhanced recognition
- **Offline TTS**: eSpeak-NG with voice profiles and customization
- **Online TTS**: HiFi-GAN/WaveNet for high-quality speech synthesis
- **Voice Profiles**: Formal, casual, energetic presets with full customization

### 🧠 AI Processing
- **Offline NLP**: Distilled GPT-2 model (~50MB) with context awareness
- **Online NLP**: DialoGPT for advanced conversational AI
- **Creative Task Generation**: AI-powered idea generation and suggestions
- **Multi-turn Conversations**: Memory-enhanced dialogue with context retention
- **Model Fine-tuning**: Custom training capabilities for NLP models

### 👁️ Screen Interaction
- **OCR Reading**: Tesseract-based screen text recognition
- **Table Detection**: Advanced table extraction from screen content
- **Screen Control**: PyAutoGUI automation with permission prompts
- **Smart Summarization**: Extractive summarization of screen content
- **Keyword Highlighting**: Context-aware text highlighting and search

### 🔒 Security & Privacy
- **Offline-First**: 100% local processing by default
- **Encrypted Storage**: Cryptography-based data encryption
- **API Key Management**: Secure storage and retrieval of API keys
- **Permission Controls**: Granular access controls for microphone/screen
- **User Controls**: Pause, clear logs, toggle modes, custom settings

### ⚡ Performance
- **Lazy Loading**: Models load only when needed
- **Resource Monitoring**: Real-time CPU, memory, GPU tracking
- **Automatic Unloading**: Inactive models freed after 5 minutes
- **Low Footprint**: <100MB total, <20% CPU typical usage
- **Background Optimization**: Continuous performance tuning

### 🔌 Extensibility
- **Plugin System**: Sandboxed Python plugins with memory limits
- **Plugin Templates**: Easy plugin creation and management
- **Command Extensions**: Custom commands via plugin interface
- **Secure Execution**: Restricted execution environment

### 🌐 External Integrations
- **Weather API**: Real-time weather information
- **News API**: Top headlines from various sources
- **Joke API**: Random jokes and humor
- **Quote API**: Inspirational and motivational quotes
- **Time API**: World time and timezone support
- **Currency API**: Exchange rate calculations
- **Wikipedia API**: Knowledge base search and summaries

### 💾 Data Management
- **Backup System**: Complete system backups with compression
- **Restore Functionality**: Selective or full system restoration
- **Conversation Export**: Chat history in JSON/text formats
- **Import Support**: Restore conversations from backups
- **Auto Cleanup**: Automatic old backup removal

### 🌍 Multi-Language Support
- **11 Languages**: English, Spanish, French, German, Italian, Portuguese, Japanese, Korean, Chinese, Russian, Arabic
- **Language Detection**: Automatic language recognition
- **Translation System**: Localized responses and commands
- **Voice Profiles**: Language-specific voice synthesis
- **Cultural Adaptation**: Region-appropriate responses

### 🎨 User Experience
- **Cinematic Boot**: Animated startup sequence with progress indicators
- **Visual Feedback**: ASCII waveforms, status bars, thinking animations
- **Conversation Flow**: Formatted dialogue with timestamps
- **Error Handling**: Graceful error messages and recovery
- **Real-time Status**: Live performance and mode indicators

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/kawacukennedy/auralis.git
cd auralis

# Install dependencies (example - adjust for your system)
pip install vosk pyaudio pvporcupine transformers torch pytesseract pyautogui cryptography psutil requests

# Make executable
chmod +x bin/auralis

# Run cleanup to optimize size (maintains <100MB footprint)
python3 scripts/cleanup.py

# Run
./bin/auralis
```

### Size Optimization
Auralis is designed to maintain a **<100MB footprint** as specified in config.json:
- **Current size**: ~85MB (after cleanup)
- **Automatic cleanup**: Run `python3 scripts/cleanup.py` or say "run cleanup"
- **Size monitoring**: Built-in compliance checking
- **Lazy loading**: Models downloaded only when needed

### Basic Usage
1. **Voice Commands**: Say "Auralis" to wake, then speak your command
2. **Push-to-Talk**: Hold SPACE key and speak
3. **Text Input**: Type commands directly
4. **Mode Switching**: Say "switch to online" for enhanced features

### Example Commands
**Voice & Conversation:**
- "Auralis, read screen" - OCR current screen
- "Auralis, summarize output" - Summarize visible content
- "Auralis, search screen for error" - Find keywords
- "Auralis, close window" - Window management
- "set voice to formal" - Change voice profile
- "be creative about [topic]" - Generate ideas

**External Services:**
- "weather New York" - Get weather information
- "news technology" - Get top news headlines
- "tell me a joke" - Random jokes
- "inspire me" - Motivational quotes
- "what time is it in Tokyo" - World time
- "currency USD to EUR" - Exchange rates
- "wikipedia artificial intelligence" - Search Wikipedia

**System Management:**
- "store api key openweather YOUR_KEY" - Secure API key storage
- "create backup my_backup" - Create system backup
- "list backups" - Show available backups
- "restore backup my_backup" - Restore from backup
- "export conversations" - Export chat history
- "set language to es" - Switch to Spanish
- "supported languages" - List available languages

**System Management:**
- "run cleanup" - Optimize app size and clean temp files
- "fine tune nlp training_data.txt" - Train custom NLP model
- "plugin myplugin execute_command" - Run plugin commands
- "training status" - Check model training capabilities

## 🏗️ Architecture

### Core Modules
- **UXFlowManager**: Terminal UI and visual effects
- **WakeWordDetectionModule**: Voice activation
- **STTModuleOffline/HFAPI**: Speech recognition
- **NLPModuleOffline/HFAPI**: Language processing
- **TTSModuleOffline/HFAPI**: Speech synthesis
- **ScreenReaderModule**: OCR and content analysis
- **ScreenControlModule**: GUI automation
- **ConversationMemoryModule**: Encrypted conversation storage
- **PluginHostModule**: Plugin management
- **SecurityModule**: Encryption and permissions
- **PerformanceOptimizerModule**: Resource management
- **ModelTrainingModule**: Custom model training
- **ExternalAPIModule**: Third-party service integration
- **BackupRestoreModule**: Data backup and restoration
- **LanguageSupportModule**: Multi-language support

### Data Flow
```
User Input → STT → NLP Processing → Memory → Response Generation → TTS Output
                     ↓
              Screen Reading/Control ← Plugin System
                     ↓
              Performance Monitoring ← Security Controls
```

## 🔧 Configuration

The `config.json` file contains all settings:
- Resource constraints (<100MB footprint)
- Model specifications and loading policies
- Voice interface parameters
- Security and privacy settings
- UI/UX customization options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is open source. See LICENSE file for details.

## 🙏 Acknowledgments

Built with love for the AI assistant community. Inspired by JARVIS from Iron Man and the vision of seamless human-AI interaction.