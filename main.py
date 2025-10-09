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
from natural_dialogue_engine import NaturalDialogueEngine
from tts import TextToSpeechModule
from screen_reader import ScreenReaderModule
from screen_control import ScreenControlModule
from wake_word import WakeWordDetectionModule
from stt import SpeechToTextModule
from plugins import PluginModule
from offline_online_switch import OfflineOnlineSwitchModule
from performance_optimizer import PerformanceOptimizerModule
from security_privacy import SecurityAndPrivacyModule

# Initialize core components
memory = ConversationMemory(enable_long_term=True)
logger = LoggingAndStorage()
settings = Settings()
plugins = PluginModule()
plugins.load_plugins()
tts = TextToSpeechModule()
screen_reader = ScreenReaderModule(tts_module=tts)
screen_control = ScreenControlModule()
switch = OfflineOnlineSwitchModule()
natural_dialogue = NaturalDialogueEngine(switch)
optimizer = PerformanceOptimizerModule()
security = SecurityAndPrivacyModule()

# Voice components
access_key = os.getenv('PICOVOICE_ACCESS_KEY')
hotkey = settings.get('voice_interface.wake_word.push_to_talk_hotkey', 'f12')
sensitivity = settings.get('voice_interface.wake_word.sensitivity', 0.5)
if access_key:
    wake_word = WakeWordDetectionModule(access_key, keyword='auralis', sensitivity=sensitivity)
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
        if security.check_permission("screen_reading"):
            text = screen_reader.read_screen_area()
            response = f"Screen text: {text[:500]}..."
        else:
            response = "Screen reading permission denied"
    elif user_input.lower().startswith("type "):
        if security.check_permission("keyboard_mouse_control"):
            text_to_type = user_input[5:]
            screen_control.type_text(text_to_type)
            response = f"Typed: {text_to_type}"
        else:
            response = "Keyboard control permission denied"
    elif "click at" in user_input.lower():
        if security.check_permission("keyboard_mouse_control"):
            parts = user_input.split()
            try:
                x, y = int(parts[-2]), int(parts[-1])
                screen_control.click_at(x, y)
                response = f"Clicked at {x}, {y}"
            except:
                response = "Invalid coordinates"
        else:
            response = "Mouse control permission denied"
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
        if security.check_permission("screen_reading"):
            text = screen_reader.read_screen_area()
            response = screen_reader.summarize_content(text)
        else:
            response = "Screen reading permission denied"
    elif user_input.lower().startswith("search screen for "):
        if security.check_permission("screen_reading"):
            keyword = user_input[17:]
            text = screen_reader.read_screen_area()
            found = screen_reader.search_for_keyword(text, keyword)
            response = f"Keyword '{keyword}' found" if found else f"Keyword '{keyword}' not found"
        else:
            response = "Screen reading permission denied"
    elif "convert screen to speech" in user_input.lower():
        if security.check_permission("screen_reading"):
            text = screen_reader.read_screen_area()
            response = screen_reader.convert_to_speech(text)
        else:
            response = "Screen reading permission denied"
    elif user_input.lower().startswith("highlight keywords "):
        if security.check_permission("screen_reading"):
            keywords_str = user_input[18:]
            keywords = keywords_str.split()
            text = screen_reader.read_screen_area()
            highlighted = screen_reader.highlight_keywords(text, keywords)
            response = highlighted[:500] + "..." if len(highlighted) > 500 else highlighted
        else:
            response = "Screen reading permission denied"
    elif "recognize tables" in user_input.lower():
        if security.check_permission("screen_reading"):
            text = screen_reader.read_screen_area()
            response = screen_reader.recognize_tables(text)
        else:
            response = "Screen reading permission denied"
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
        if security.check_permission("keyboard_mouse_control"):
            screen_control.close_window()
            response = "Window closed"
        else:
            response = "Keyboard/mouse control permission denied"
    elif "scroll up" in user_input.lower():
        if security.check_permission("keyboard_mouse_control"):
            screen_control.scroll('up')
            response = "Scrolled up"
        else:
            response = "Keyboard/mouse control permission denied"
    elif "scroll down" in user_input.lower():
        if security.check_permission("keyboard_mouse_control"):
            screen_control.scroll('down')
            response = "Scrolled down"
        else:
            response = "Keyboard/mouse control permission denied"
    elif user_input.lower().startswith("open "):
        if security.check_permission("keyboard_mouse_control"):
            app = user_input[5:].strip()
            # Simple, assume command
            import subprocess
            try:
                subprocess.run([app])
                response = f"Opened {app}"
            except:
                response = f"Failed to open {app}"
        else:
            response = "Keyboard/mouse control permission denied"
    elif "toggle offline" in user_input.lower():
        if switch.get_mode() == 'offline':
            switch.switch_to_online()
        else:
            switch.switch_to_offline()
        response = f"Switched to {switch.get_mode()} mode"
    elif "pause" in user_input.lower():
        # Simple pause, maybe stop listening
        response = "Assistant paused"
    elif "help" in user_input.lower():
        response = "Available commands: read screen, type <text>, click at <x> <y>, time, plugin <name>, list plugins, summarize screen, search screen for <keyword>, convert screen to speech, highlight keywords <kw>, recognize tables, clear logs, set voice <type>, set speed <0.9-1.2>, set pitch <offset>, set profile <formal/casual/energetic>, close window, scroll up/down, open <app>, toggle offline, pause, quit"
    elif "quit" in user_input.lower():
        response = "Goodbye"
    else:
        # NLP response
        context = memory.get_context()
        prompt = ""
        for turn in context:
            prompt += f"User: {turn['user']}\nAI: {turn['response']}\n"
        prompt += f"User: {user_input}\nAI:"
        response = natural_dialogue.respond(prompt)

    optimizer.update_activity()
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

def push_to_talk(hotkey='f12'):
    from pynput import keyboard
    key_obj = getattr(keyboard.Key, hotkey.lower(), keyboard.Key.f12)
    def on_press(key):
        if key == key_obj:
            listen_thread()
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

def main_curses(stdscr):
    curses.curs_set(1)
    stdscr.clear()
    stdscr.addstr(0, 0, "Auralis - Terminal AI Assistant")
    stdscr.addstr(1, 0, f"Type commands or use {hotkey.upper()} for push-to-talk. Type 'quit' to exit.")
    history = []
    show_history = True
    y = 3
    while True:
        stdscr.addstr(y, 0, "> ")
        curses.echo()
        user_input = stdscr.getstr(y, 2).decode()
        curses.noecho()
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'toggle history':
            show_history = not show_history
            response = f"History display {'enabled' if show_history else 'disabled'}"
        else:
            response = process_input(user_input)
        y += 1
        stdscr.addstr(y, 0, f"AI: {response}")
        history.append(f"User: {user_input}")
        history.append(f"AI: {response}")
        if len(history) > 10:  # Keep last 5 exchanges
            history = history[-10:]
        y += 1
        if show_history and y < curses.LINES - 5:
            for i, line in enumerate(history[-4:]):  # Show last 4 lines
                stdscr.addstr(y + i, 0, line)
            y += 4
        if y > curses.LINES - 2:
            y = 3
            stdscr.clear()
            stdscr.addstr(0, 0, "Auralis - Terminal AI Assistant")
            stdscr.addstr(1, 0, f"Type commands or use {hotkey.upper()} for push-to-talk. Type 'quit' to exit.")
        stdscr.refresh()
        tts.speak(response)

if __name__ == "__main__":
    if wake_word:
        threading.Thread(target=wake_thread, daemon=True).start()
    push_to_talk(hotkey)
    curses.wrapper(main_curses)