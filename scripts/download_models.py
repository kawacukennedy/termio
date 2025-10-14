#!/usr/bin/env python3
"""
Download required model files for Auralis
"""

import os
import urllib.request
import zipfile
import tarfile
import shutil
from pathlib import Path

class ModelDownloader:
    def __init__(self):
        self.models_dir = Path('models')
        self.models_dir.mkdir(exist_ok=True)

    def download_file(self, url, filename):
        """Download file with progress"""
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filename)

    def extract_archive(self, archive_path, extract_to):
        """Extract zip or tar.gz"""
        if archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.endswith('.tar.gz'):
            with tarfile.open(archive_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_to)

    def download_tinygpt(self):
        """Download TinyGPT model (~50MB)"""
        # Placeholder URL - replace with actual TinyGPT download
        url = "https://example.com/tinygpt_model.tar.gz"
        archive = self.models_dir / "tinygpt.tar.gz"

        try:
            self.download_file(url, archive)
            self.extract_archive(archive, self.models_dir / "tinygpt")
            archive.unlink()  # Remove archive
            print("TinyGPT model downloaded successfully")
        except Exception as e:
            print(f"Failed to download TinyGPT: {e}")
            print("Note: TinyGPT model must be downloaded separately")

    def download_vosk_stt(self):
        """Download Vosk STT model (~20MB)"""
        # Placeholder for Vosk tiny model
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        archive = self.models_dir / "vosk_stt.zip"

        try:
            self.download_file(url, archive)
            self.extract_archive(archive, self.models_dir / "vosk_stt")
            archive.unlink()
            print("Vosk STT model downloaded successfully")
        except Exception as e:
            print(f"Failed to download Vosk STT: {e}")

    def download_tesseract_data(self):
        """Download Tesseract OCR data (~20MB)"""
        # Tesseract data is usually installed separately
        print("Tesseract data should be installed via system package manager")
        print("On macOS: brew install tesseract")
        print("On Ubuntu: apt install tesseract-ocr")

    def check_total_size(self):
        """Check total models directory size"""
        total_size = sum(f.stat().st_size for f in self.models_dir.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(".1f")
        if size_mb > 100:
            print("WARNING: Total size exceeds 100MB limit!")
        return size_mb

    def run(self):
        """Download all models"""
        print("Starting model downloads for Auralis...")

        self.download_tinygpt()
        self.download_vosk_stt()
        self.download_tesseract_data()

        size = self.check_total_size()
        if size <= 100:
            print("✅ All models downloaded successfully. Total size within 100MB limit.")
        else:
            print("❌ Total size exceeds 100MB. Please optimize models.")

if __name__ == "__main__":
    downloader = ModelDownloader()
    downloader.run()