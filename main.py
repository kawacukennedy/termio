#!/usr/bin/env python3

import json
import sys
import os
import threading
import pyaudio
import struct
import curses
from datetime import datetime

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

print(f"Starting {config['app_name']} v{config['version']}")

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import modules
from memory import ConversationMemory
from logging_storage import LoggingAndStorage
from settings import Settings
from nlp import UltraLightNLPModule
from tts import TextToSpeechModule
from screen_reader import ScreenReaderModule
from screen_control import ScreenControlModule
from wake_word import WakeWordDetectionModule
from stt import SpeechToTextModule
from plugins import PluginModule
from offline_online_switch import OfflineOnlineSwitchModule

# Initialize core components
memory = ConversationMemory(enable_long_term=True)
logger = LoggingAndStorage()
settings = Settings()
plugins = PluginModule()
plugins.load_plugins()
try:
    nlp = UltraLightNLPModule()
except ImportError:
    nlp = None
tts = TextToSpeechModule()
screen_reader = ScreenReaderModule()
screen_control = ScreenControlModule()
switch = OfflineOnlineSwitchModule()

# Voice components
access_key = os.getenv('PICOVOICE_ACCESS_KEY')
if access_key:
    wake_word = WakeWordDetectionModule(access_key)
    stt = SpeechToTextModule()
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=512)
    stream.start_stream()
else:
    wake_word = None
    stt = None
    audio = None
    stream = None

def process_input(user_input):
    user_input = user_input.strip()
    if not user_input:
        return ""

    # Command parsing
    if "read screen" in user_input.lower():
        text = screen_reader.read_screen_area()
        response = f"Screen text: {text[:500]}..."
    elif user_input.lower().startswith("type "):
        text_to_type = user_input[5:]
        screen_control.type_text(text_to_type)
        response = f"Typed: {text_to_type}"
    elif "click at" in user_input.lower():
        parts = user_input.split()
        try:
            x, y = int(parts[-2]), int(parts[-1])
            screen_control.click_at(x, y)
            response = f"Clicked at {x}, {y}"
        except:
            response = "Invalid coordinates"
    elif "time" in user_input.lower():
        response = f"The time is {datetime.now().strftime('%H:%M:%S')}"
    elif user_input.lower().startswith('plugin '):
        parts = user_input.split()
        if len(parts) > 1:
            response = plugins.execute(parts[1], *parts[2:])
        else:
            response = "Usage: plugin <name> [args]"
    elif "list plugins" in user_input.lower():
        response = "Available plugins: " + ', '.join(plugins.list_plugins())
    elif "summarize screen" in user_input.lower():
        text = screen_reader.read_screen_area()
        response = screen_reader.summarize_content(text)
    elif user_input.lower().startswith("search screen for "):
        keyword = user_input[17:]
        text = screen_reader.read_screen_area()
        found = screen_reader.search_for_keyword(text, keyword)
        response = f"Keyword '{keyword}' found" if found else f"Keyword '{keyword}' not found"
    elif "clear logs" in user_input.lower():
        logger.clear_logs()
        response = "Logs cleared"
    elif user_input.lower().startswith("set voice "):
        voice = user_input[10:].strip()
        tts.set_voice(voice)
        response = f"Voice set to {voice}"
    elif user_input.lower().startswith("set speed "):
        try:
            speed = float(user_input[10:].strip())
            tts.set_speed(speed)
            response = f"Speed set to {speed}x"
        except:
            response = "Invalid speed"
    elif user_input.lower().startswith("set pitch "):
        try:
            pitch = int(user_input[10:].strip())
            tts.set_pitch(pitch)
            response = f"Pitch set to {pitch}"
        except:
            response = "Invalid pitch"
    elif user_input.lower().startswith("set profile "):
        profile = user_input[12:].strip()
        tts.set_profile(profile)
        response = f"Profile set to {profile}"
    elif "close window" in user_input.lower():
        screen_control.close_window()
        response = "Window closed"
    elif "scroll up" in user_input.lower():
        screen_control.scroll('up')
        response = "Scrolled up"
    elif "scroll down" in user_input.lower():
        screen_control.scroll('down')
        response = "Scrolled down"
    elif user_input.lower().startswith("open "):
        app = user_input[5:].strip()
        # Simple, assume command
        import subprocess
        try:
            subprocess.run([app])
            response = f"Opened {app}"
        except:
            response = f"Failed to open {app}"
    elif "toggle offline" in user_input.lower():
        if switch.get_mode() == 'offline':
            switch.switch_to_online()
        else:
            switch.switch_to_offline()
        response = f"Switched to {switch.get_mode()} mode"
    elif "pause" in user_input.lower():
        # Simple pause, maybe stop listening
        response = "Assistant paused"
    elif "quit" in user_input.lower():
        response = "Goodbye"
    else:
        # NLP response
        context = memory.get_context()
        prompt = ""
        for turn in context:
            prompt += f"User: {turn['user']}\nAI: {turn['response']}\n"
        prompt += f"User: {user_input}\nAI:"

        switch.auto_switch()  # Check mode
        if switch.get_mode() == 'offline':
            if nlp:
                try:
                    response = nlp.generate_response(prompt)
                except Exception as e:
                    response = "NLP error: " + str(e)
            else:
                response = "Offline NLP not available. " + user_input[::-1]  # Simple reverse for test
        else:
            # Try Hugging Face first (free tier)
            hf_key = os.getenv('HUGGINGFACE_API_KEY')
            if hf_key:
                try:
                    import requests
                    headers = {"Authorization": f"Bearer {hf_key}"}
                    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 100, "temperature": 0.7}}
                    response_api = requests.post("https://api-inference.huggingface.co/models/distilgpt2", headers=headers, json=payload)
                    if response_api.status_code == 200:
                        result = response_api.json()
                        if isinstance(result, list) and result:
                            generated = result[0].get("generated_text", "")
                            if generated.startswith(prompt):
                                response = generated[len(prompt):].strip()
                            else:
                                response = generated.strip()
                        else:
                            response = "HF API error: unexpected response"
                    else:
                        response = f"HF API error: {response_api.status_code} {response_api.text}"
                except Exception as e:
                    response = "HF error: " + str(e)
            else:
                # Fallback to OpenAI
                try:
                    import openai
                    openai.api_key = os.getenv('OPENAI_API_KEY')
                    client = openai.OpenAI()
                    completion = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=100,
                        temperature=0.7
                    )
                    response = completion.choices[0].message.content.strip()
                except Exception as e:
                    response = "Online error: " + str(e)

    memory.add_interaction(user_input, response)
    logger.log_interaction(user_input, response)
    return response

def process_voice(text):
    if text:
        response = process_input(text)
        tts.speak(response)
        # In curses, would update, but for now print
        print(f"Voice input: {text}")
        print(f"Response: {response}")

def wake_thread():
    if not stream:
        return
    while True:
        data = stream.read(512)
        pcm = struct.unpack_from("h" * 512, data)
        if wake_word.process_audio(pcm):
            listen_thread()

def listen_thread():
    if not stream or not stt:
        return
    frames = []
    for _ in range(50):  # ~5 seconds
        data = stream.read(8000)
        frames.append(data)
        text = stt.transcribe(data)
        if text:
            process_voice(text)
            break

def push_to_talk():
    from pynput import keyboard
    def on_press(key):
        if key == keyboard.Key.f12:
            listen_thread()
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

def main_curses(stdscr):
    curses.curs_set(1)
    stdscr.clear()
    stdscr.addstr(0, 0, "Auralis - Terminal AI Assistant")
    stdscr.addstr(1, 0, "Type commands or use F12 for push-to-talk. Type 'quit' to exit.")
    y = 3
    while True:
        stdscr.addstr(y, 0, "> ")
        curses.echo()
        user_input = stdscr.getstr(y, 2).decode()
        curses.noecho()
        if user_input.lower() == 'quit':
            break
        response = process_input(user_input)
        y += 1
        stdscr.addstr(y, 0, f"AI: {response}")
        y += 1
        if y > curses.LINES - 2:
            y = 3
            stdscr.clear()
            stdscr.addstr(0, 0, "Auralis - Terminal AI Assistant")
            stdscr.addstr(1, 0, "Type commands or use F12 for push-to-talk. Type 'quit' to exit.")
        stdscr.refresh()
        tts.speak(response)

if __name__ == "__main__":
    if wake_word:
        threading.Thread(target=wake_thread, daemon=True).start()
    push_to_talk()
    curses.wrapper(main_curses)