#!/bin/bash
# Auralis Installer Script
# Installs Auralis with all dependencies under 100MB limit

set -e

echo "🚀 Installing Auralis..."

# Check system requirements
if [[ "$OSTYPE" != "darwin"* ]] && [[ "$OSTYPE" != "linux-gnu" ]]; then
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

# Create virtual environment
echo "📦 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check size before models
code_size=$(du -sm . | cut -f1)
echo "📏 Code size: ${code_size}MB"

# Download models
echo "🤖 Downloading AI models..."
python3 scripts/download_models.py

# Check total size
total_size=$(du -sm . | cut -f1)
echo "📏 Total install size: ${total_size}MB"

if [ "$total_size" -gt 100 ]; then
    echo "❌ Install size exceeds 100MB limit: ${total_size}MB"
    echo "Please optimize models or reduce dependencies"
    exit 1
fi

# Make executable
chmod +x bin/auralis
chmod +x main.py

# Create desktop shortcut (optional)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🖥️  Creating macOS app..."
    # Create .app bundle
    mkdir -p "Auralis.app/Contents/MacOS"
    mkdir -p "Auralis.app/Contents/Resources"
    cp bin/auralis "Auralis.app/Contents/MacOS/"
    echo '<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>auralis</string>
    <key>CFBundleIdentifier</key>
    <string>com.auralis.ai</string>
    <key>CFBundleName</key>
    <string>Auralis</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
</dict>
</plist>' > "Auralis.app/Contents/Info.plist"
fi

# Setup complete
echo "✅ Installation complete!"
echo "🎯 Total size: ${total_size}MB (under 100MB limit)"
echo ""
echo "To run Auralis:"
echo "  ./bin/auralis"
echo ""
echo "Or use CLI commands:"
echo "  ./bin/auralis --version"
echo "  ./bin/auralis --speak 'Hello world'"
echo "  ./bin/auralis --plugin list"