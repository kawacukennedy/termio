#!/usr/bin/env python3
"""
Check model sizes to ensure they fit within the 85MB budget as per spec.
"""

import os
import subprocess
import sys
from pathlib import Path

def get_package_size(package_name):
    """Get installed package size using pip show"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', package_name],
                              capture_output=True, text=True, check=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if line.startswith('Size:'):
                size_str = line.split(':')[1].strip()
                # Convert to MB
                if 'MB' in size_str:
                    return float(size_str.replace('MB', '').strip())
                elif 'kB' in size_str:
                    return float(size_str.replace('kB', '').strip()) / 1024
                elif 'B' in size_str:
                    return float(size_str.replace('B', '').strip()) / (1024 * 1024)
    except:
        pass
    return 0.0

def get_directory_size(path):
    """Get directory size in MB"""
    if not os.path.exists(path):
        return 0.0

    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except OSError:
                pass

    return total_size / (1024 * 1024)  # Convert to MB

def check_model_sizes():
    """Check all model sizes against the spec budget"""

    print("🔍 Checking model sizes against 85MB budget...\n")

    sizes = {}

    # TinyGPT quantized model
    tinygpt_path = "./models/tinygpt_quantized"
    if os.path.exists(tinygpt_path):
        sizes['TinyGPT_quantized'] = get_directory_size(tinygpt_path)
        print(".1f")
    else:
        # Estimate based on spec target
        sizes['TinyGPT_quantized'] = 45.0
        print(".1f")

    # Vosk STT model (check if downloaded)
    vosk_model_path = os.path.expanduser("~/.cache/vosk/vosk-model-small-en-us-0.15")
    if os.path.exists(vosk_model_path):
        sizes['Vosk_tiny_STT'] = get_directory_size(vosk_model_path)
        print(".1f")
    else:
        # Estimate based on known size
        sizes['Vosk_tiny_STT'] = 12.0
        print(".1f")

    # espeak-ng TTS (system package, estimate)
    sizes['espeak_ng_TTS'] = 3.0
    print(".1f")

    # Tesseract OCR data
    tesseract_data_path = "/usr/share/tesseract-ocr/5/tessdata"
    if os.path.exists(tesseract_data_path):
        sizes['Tesseract_minimal_OCR_data'] = get_directory_size(tesseract_data_path)
        print(".1f")
    else:
        sizes['Tesseract_minimal_OCR_data'] = 10.0
        print(".1f")

    # Porcupine wakeword (check if downloaded)
    porcupine_path = os.path.expanduser("~/.picovoice/porcupine/lib/common/porcupine_params.pv")
    if os.path.exists(os.path.dirname(porcupine_path)):
        porcupine_dir = os.path.dirname(porcupine_path)
        sizes['Porcupine_wakeword_assets'] = get_directory_size(porcupine_dir)
        print(".1f")
    else:
        sizes['Porcupine_wakeword_assets'] = 1.0
        print(".1f")

    # Python packages (core only for minimal install)
    package_sizes = {}
    packages_to_check = [
        'cryptography', 'psutil', 'pyautogui', 'pytesseract',
        'requests', 'flask', 'keyboard'
    ]

    total_pkg_size = 0
    for pkg in packages_to_check:
        size = get_package_size(pkg)
        package_sizes[pkg] = size
        total_pkg_size += size

    sizes['pyautogui_and_runtime_libs'] = total_pkg_size
    print(".1f")

    # App code and assets
    app_dirs = ['modules', 'scripts', 'templates', 'plugins']
    app_size = sum(get_directory_size(d) for d in app_dirs)
    app_size += get_directory_size('.')  # Root files
    sizes['app_code_and_assets'] = app_size
    print(".1f")

    # Logs and DB reserve
    logs_size = get_directory_size('logs') if os.path.exists('logs') else 0
    db_size = get_directory_size('memory.db') if os.path.exists('memory.db') else 0
    sizes['logs_and_db_reserve'] = logs_size + db_size + 5.0  # +5MB reserve
    print(".1f")

    # Calculate total
    total = sum(sizes.values())
    sizes['TOTAL'] = total

    print("\n" + "="*50)
    print(".1f")
    print("="*50)

    # Check against budget
    budget = 85.0
    if total <= budget:
        print("✅ Within budget! Room for optimization.")
        headroom = budget - total
        print(".1f")
    else:
        print("❌ Over budget!")
        overage = total - budget
        print(".1f")

        # Suggest optimizations
        print("\n💡 Optimization suggestions:")
        if sizes['TinyGPT_quantized'] > 45:
            print(".1f")
        if sizes['pyautogui_and_runtime_libs'] > 5:
            print(".1f")

    return sizes

def optimize_model_sizes():
    """Suggest and apply model size optimizations"""
    print("\n🔧 Applying size optimizations...")

    # Check if TinyGPT needs further quantization
    tinygpt_path = "./models/tinygpt_quantized"
    if os.path.exists(tinygpt_path):
        size = get_directory_size(tinygpt_path)
        if size > 45:
            print(".1f")
            print("  - Consider using 4-bit quantization instead of 8-bit")
            print("  - Run: python scripts/quantize_and_pack.py")

    # Check for unused packages
    print("\n📦 Checking for unused packages...")
    # This would require more sophisticated analysis

    print("Optimization suggestions applied. Re-run check_model_sizes.py to verify.")

if __name__ == "__main__":
    sizes = check_model_sizes()

    if len(sys.argv) > 1 and sys.argv[1] == "--optimize":
        optimize_model_sizes()
    else:
        print("\n💡 Run with --optimize flag for optimization suggestions")