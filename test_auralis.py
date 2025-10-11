#!/usr/bin/env python3

import subprocess
import time
import sys
import os

# Add venv to path
venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python3')
if os.path.exists(venv_python):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'venv', 'lib', 'python3.13', 'site-packages'))

import requests

def run_tests():
    print("🧪 Starting Auralis Comprehensive Tests...")

    # Start Auralis in background
    print("🚀 Starting Auralis...")
    env = os.environ.copy()
    env['PATH'] = 'venv/bin:' + env['PATH']
    process = subprocess.Popen(
        ['venv/bin/python3', 'main.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(__file__),
        env=env
    )

    # Give it time to start
    time.sleep(15)

    # Wait for startup
    time.sleep(15)

    # Test web dashboard
    print("🌐 Testing Web Dashboard...")
    try:
        response = requests.get('http://localhost:5000/api/status', timeout=5)
        if response.status_code == 200:
            print("✅ Web dashboard status API working")
        else:
            print(f"❌ Web dashboard status API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Web dashboard test failed: {e}")

    # Test plugins API
    try:
        response = requests.get('http://localhost:5000/api/plugins', timeout=5)
        if response.status_code == 200:
            print("✅ Plugins API working")
        else:
            print(f"❌ Plugins API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Plugins API test failed: {e}")

    # Send test commands
    test_commands = [
        "set api key huggingface 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",
        "switch to online",
        "what is the capital of France",
        "tell me a joke",
        "switch to offline",
        "what is 2+2",
        "list voice profiles",
        "create backup test_backup",
        "list backups",
        "system info",
        "quit"
    ]

    print("💬 Testing Interactive Commands...")
    for cmd in test_commands:
        try:
            print(f"📝 Sending: {cmd}")
            process.stdin.write(cmd + '\n')
            process.stdin.flush()
            time.sleep(2)  # Wait for response
        except Exception as e:
            print(f"❌ Command '{cmd}' failed: {e}")
            break

    # Wait a bit more
    time.sleep(5)

    # Terminate process
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()

    print("✅ Tests completed!")

if __name__ == "__main__":
    run_tests()