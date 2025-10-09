FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    espeak-ng \
    libespeak-ng1 \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy files
COPY . .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Download Vosk model (example, adjust path)
RUN wget -O vosk-model.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && \
    unzip vosk-model.zip && \
    mv vosk-model-small-en-us-0.15 model && \
    rm vosk-model.zip

# Expose if needed, but terminal app
CMD ["python", "main.py"]