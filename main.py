#!/usr/bin/env python3
# Auralis - Terminal AI Assistant

import json
import sys
import os
import threading
import struct
import curses
from datetime import datetime

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    sd = None

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
tts = TextToSpeechModule(online_mode=True)
screen_reader = ScreenReaderModule(tts_module=tts)
screen_control = ScreenControlModule()
switch = OfflineOnlineSwitchModule()
natural_dialogue = NaturalDialogueEngine(switch)
optimizer = PerformanceOptimizerModule()
security = SecurityAndPrivacyModule()

# Voice components
hotkey = settings.get('voice_interface.push_to_talk.hotkey', 'f12')
if HAS_SOUNDDEVICE:
    stt = SpeechToTextModule(switch_module=switch)
else:
    stt = None

def process_input(user_input):
    user_input = user_input.strip()
    if not user_input:
        return ""

    try:
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
                except ValueError:
                    response = "Invalid coordinates. Use: click at <x> <y>"
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
            plugin_list = plugins.list_plugins()
            if plugin_list:
                response = "Available plugins: " + ', '.join(plugin_list)
            else:
                response = "No plugins available"
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
            except ValueError:
                response = "Invalid speed. Use a number between 0.9 and 1.2"
        elif user_input.lower().startswith("set pitch "):
            try:
                pitch = int(user_input[10:].strip())
                tts.set_pitch(pitch)
                response = f"Pitch set to {pitch}"
            except ValueError:
                response = "Invalid pitch. Use an integer offset"
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
                import subprocess
                try:
                    subprocess.run([app])
                    response = f"Opened {app}"
                except FileNotFoundError:
                    response = f"Application '{app}' not found"
                except Exception as e:
                    response = f"Failed to open {app}: {e}"
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
        elif "interrupt" in user_input.lower():
            # Interrupt current TTS if possible
            response = "Interruption requested"
        elif "help" in user_input.lower():
            response = "Available commands: read screen, type <text>, click at <x> <y>, time, plugin <name>, list plugins, summarize screen, search screen for <keyword>, convert screen to speech, highlight keywords <kw>, recognize tables, clear logs, set voice <type>, set speed <0.9-1.2>, set pitch <offset>, set profile <formal/casual/energetic>, close window, scroll up/down, open <app>, toggle offline, pause, interrupt, quit"
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
    except Exception as e:
        response = f"An error occurred: {str(e)}. Try 'help' for commands."

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
    if not HAS_SOUNDDEVICE or not stt:
        return
    import queue
    q = queue.Queue()
    def audio_callback(indata, frames, time, status):
        q.put(indata.copy())
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=16000, blocksize=8000):
        while True:
            data = q.get()
            pcm = data.flatten().astype('int16').tobytes()
            text = stt.transcribe(pcm)
            if text and 'auralis' in text.lower():
                listen_thread()

def listen_thread():
    if not HAS_SOUNDDEVICE or not stt:
        return
    duration = 5  # seconds
    fs = 16000
    print("Listening...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    data = recording.flatten().tobytes()
    # Simple waveform
    pcm = struct.unpack_from("h" * len(recording) // 2, data)
    max_val = max(abs(x) for x in pcm) if pcm else 0
    bars = int(max_val / 1000)
    print('|' * bars)
    text = stt.transcribe(data)
    if text:
        process_voice(text)

def push_to_talk(hotkey='f12'):
    if not HAS_SOUNDDEVICE:
        return
    from pynput import keyboard
    key_obj = getattr(keyboard.Key, hotkey.lower(), keyboard.Key.f12)
    def on_press(key):
        if key == key_obj:
            listen_thread()
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

def main_curses(stdscr):
    curses.curs_set(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Light theme
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Dark theme
    theme = 1  # 1 light, 2 dark
    stdscr.bkgd(curses.color_pair(theme))
    stdscr.clear()
    stdscr.addstr(0, 0, "Auralis - Terminal AI Assistant", curses.color_pair(theme))
    stdscr.addstr(1, 0, f"Type commands or use {hotkey.upper()} for voice input. Type 'quit' to exit.", curses.color_pair(theme))
    history = []
    show_history = True
    activity_indicator = False
    commands = ["read screen", "type", "click at", "time", "plugin", "list plugins", "summarize screen", "search screen for", "convert screen to speech", "highlight keywords", "recognize tables", "clear logs", "set voice", "set speed", "set pitch", "set profile", "close window", "scroll up", "scroll down", "open", "toggle offline", "pause", "interrupt", "quit", "toggle history", "toggle theme"]
    y = 3
    while True:
        stdscr.addstr(y, 0, "> ", curses.color_pair(theme))
        curses.echo()
        user_input = stdscr.getstr(y, 2).decode()
        curses.noecho()
        # Inline suggestions
        if user_input:
            suggestions = [cmd for cmd in commands if cmd.startswith(user_input.lower())]
            if suggestions and len(suggestions) <= 3:
                stdscr.addstr(y+1, 0, f"Suggestions: {', '.join(suggestions[:3])}", curses.color_pair(theme))
                stdscr.refresh()
                curses.napms(1000)  # Show for 1s
                stdscr.addstr(y+1, 0, " " * 50, curses.color_pair(theme))  # Clear
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'toggle history':
            show_history = not show_history
            response = f"History display {'enabled' if show_history else 'disabled'}"
        elif user_input.lower() == 'toggle theme':
            theme = 2 if theme == 1 else 1
            stdscr.bkgd(curses.color_pair(theme))
            stdscr.clear()
            stdscr.addstr(0, 0, "Auralis - Terminal AI Assistant", curses.color_pair(theme))
            stdscr.addstr(1, 0, f"Type commands or use {hotkey.upper()} for voice input. Type 'quit' to exit.", curses.color_pair(theme))
            response = f"Theme switched to {'dark' if theme == 2 else 'light'}"
            y = 3
        else:
            activity_indicator = True
            stdscr.addstr(y+1, 0, "Processing...", curses.color_pair(theme))
            stdscr.refresh()
            response = process_input(user_input)
            activity_indicator = False
            activity_indicator = True
            stdscr.addstr(y+1, 0, "Processing...", curses.color_pair(theme))
            stdscr.refresh()
            response = process_input(user_input)
            activity_indicator = False
        y += 1
        stdscr.addstr(y, 0, f"AI: {response}", curses.color_pair(theme))
        # Contextual hints
        if "screen" in user_input.lower():
            hint = "Try: summarize screen, search screen for <keyword>"
        elif "voice" in user_input.lower() or "tts" in user_input.lower():
            hint = "Try: set voice male/female/neutral, set speed 1.0"
        else:
            hint = ""
        if hint:
            y += 1
            stdscr.addstr(y, 0, f"Hint: {hint}", curses.color_pair(theme))
        history.append(f"User: {user_input}")
        history.append(f"AI: {response}")
        if len(history) > 10:  # Keep last 5 exchanges
            history = history[-10:]
        y += 1
        if show_history and y < curses.LINES - 5:
            for i, line in enumerate(history[-4:]):  # Show last 4 lines
                stdscr.addstr(y + i, 0, line, curses.color_pair(theme))
            y += 4
        if y > curses.LINES - 2:
            y = 3
            stdscr.clear()
            stdscr.addstr(0, 0, "Auralis - Terminal AI Assistant", curses.color_pair(theme))
            stdscr.addstr(1, 0, f"Type commands or use {hotkey.upper()} for voice input. Type 'quit' to exit.", curses.color_pair(theme))
        stdscr.refresh()
        optimizer.update_activity()
        tts.speak(response)
        optimizer.optimize()  # Sleep if idle

def simple_cli_text():
    print("Auralis - Text Conversation Mode")
    while True:
        user_input = input("> ")
        if user_input.lower() == 'quit':
            break
        response = process_input(user_input)
        print(f"AI: {response}")

def simple_cli_voice():
    print("Auralis - Voice Conversation Mode")
    print("Hello Sir!")
    tts.speak("Hello Sir!")
    if not HAS_SOUNDDEVICE:
        print("Voice not available.")
        return
    threading.Thread(target=wake_thread, daemon=True).start()
    print("Say 'Auralis' to start a conversation.")
    while True:
        # Keep running
        pass

def simple_cli():
    print("Auralis - Simple CLI Mode (Curses not available)")
    print("Choose mode: 1 for Text-only, 2 for Voice-enabled")
    choice = input("Enter 1 or 2: ").strip()
    voice_enabled = choice == '2'
    if voice_enabled and not HAS_SOUNDDEVICE:
        print("Voice not available, falling back to text-only.")
        voice_enabled = False
    if voice_enabled:
        threading.Thread(target=wake_thread, daemon=True).start()
        print("Voice mode enabled. Say 'Auralis' to wake, then speak.")
    while True:
        user_input = input("> ")
        if user_input.lower() == 'quit':
            break
        response = process_input(user_input)
        print(f"AI: {response}")

def main():
    try:
        curses.wrapper(main_curses)
    except:
        simple_cli()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == 'text':
            simple_cli_text()
        elif mode == 'voice':
            simple_cli_voice()
        else:
            print("Usage: python main.py [text|voice]")
            main()
    else:
        main()