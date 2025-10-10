#!/usr/bin/env python3

import json
import sys
import os
import time
import threading
import random

with open('config.json') as f:
    config = json.load(f)

print(f"Starting {config['app_identity']['name']} v{config['app_identity']['version']}")

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import modules
from ux_flow_manager import UXFlowManager
from wake_word import WakeWordDetectionModule
from stt_offline import STTModuleOffline
from stt_hf import STTModuleHFAPI
from nlp_offline import NLPModuleOffline
from nlp_hf import NLPModuleHFAPI
from tts_offline import TTSModuleOffline
from tts_hf import TTSModuleHFAPI
from screen_reader import ScreenReaderModule
from screen_control import ScreenControlModule
from memory import ConversationMemoryModule
from logging import LoggingModule
from settings import SettingsModule
from security import SecurityModule
from performance import PerformanceOptimizerModule
from plugins import PluginHostModule

# Initialize modules
ux = UXFlowManager(config)
wakeword = WakeWordDetectionModule(config)
stt_offline = STTModuleOffline(config)
stt_online = STTModuleHFAPI(config)
nlp_offline = NLPModuleOffline(config)
nlp_online = NLPModuleHFAPI(config)
tts_offline = TTSModuleOffline(config)
tts_online = TTSModuleHFAPI(config)
screen_reader = ScreenReaderModule(config)
screen_control = ScreenControlModule(config)
memory = ConversationMemoryModule(config)
logging_mod = LoggingModule(config)
settings = SettingsModule(config)
security = SecurityModule(config, settings)
performance = PerformanceOptimizerModule(config)
plugins = PluginHostModule(config)

# Current mode
current_mode = 'offline'
stt = stt_offline
nlp = nlp_offline
tts = tts_offline

# Initialize modules
wakeword.initialize()
stt_offline.initialize()
stt_online.initialize()
nlp_online.initialize()
tts_online.initialize()
screen_reader.initialize()
screen_control.initialize()
plugins.load_plugins()

# Boot
ux.show_boot_sequence()
ux.update_status('mode_indicator', 'offline')
ux.update_status('network_status', 'offline')
print("Auralis ready")

# Idle
ux.show_idle_screen()

# Conversation loop
def voice_loop():
    while True:
        if wakeword.detect():
            ux.update_status('mic_status', 'listening')
            ux.show_ascii_waveform()
            print("Wakeword detected! Listening...")

            # Transcribe speech
            user_input = stt.transcribe(duration=5)
            ux.update_status('mic_status', 'processing')

            if user_input:
                process_input(user_input)
            else:
                ux.show_error_message('misheard_voice')

            ux.update_status('mic_status', 'idle')

            # Performance optimization
            performance.update_activity()
            performance.unload_inactive_models(nlp_offline, stt_offline, tts_offline)
        time.sleep(0.1)

def push_to_talk_loop():
    while True:
        try:
            user_input = stt.transcribe_push_to_talk()
            if user_input:
                ux.update_status('mic_status', 'processing')
                process_input(user_input)
                ux.update_status('mic_status', 'idle')
        except KeyboardInterrupt:
            break

def switch_mode(new_mode):
    global current_mode, stt, nlp, tts
    if new_mode == current_mode:
        return f"Already in {new_mode} mode."

    if new_mode == 'online':
        stt = stt_online
        nlp = nlp_online
        tts = tts_online
        ux.update_status('network_status', 'online')
    elif new_mode == 'offline':
        stt = stt_offline
        nlp = nlp_offline
        tts = tts_offline
        ux.update_status('network_status', 'offline')

    current_mode = new_mode
    return f"Switched to {new_mode} mode."

def process_input(user_input):
    print(f"You: {user_input}")

    # Check for commands
    if user_input.lower() in ['quit', 'exit', 'goodbye']:
        return 'quit'
    elif user_input.lower() == 'switch to online':
        response = switch_mode('online')
    elif user_input.lower() == 'switch to offline':
        response = switch_mode('offline')
    elif 'read screen' in user_input.lower():
        screen_text = screen_reader.read_screen()
        response = f"Screen content: {screen_text[:200]}..."
    elif 'summarize output' in user_input.lower():
        # Assume last screen read
        response = "Summary: [implement summarization]"
    elif 'search screen for' in user_input.lower():
        query = user_input.lower().replace('search screen for', '').strip()
        screen_text = screen_reader.read_screen()
        found = screen_reader.search_text(screen_text, query)
        response = f"Found '{query}' on screen: {found}"
    elif 'close window' in user_input.lower():
        screen_control.window_management('close')
        response = "Window closed."
    elif 'open browser' in user_input.lower():
        # Basic browser opening
        import webbrowser
        url = user_input.lower().replace('open browser and go to', '').strip()
        if url:
            webbrowser.open(url)
            response = f"Opened browser to {url}"
        else:
            webbrowser.open('https://www.google.com')
            response = "Opened browser to Google"
    elif 'tell me a joke' in user_input.lower():
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the computer go to the doctor? It had a virus!",
            "What do you call a fake noodle? An impasta!",
            "Why don't eggs tell jokes? They'd crack each other up!"
        ]
        response = random.choice(jokes)
    elif user_input.lower().startswith('plugin '):
        # Handle plugin commands
        parts = user_input.lower().split(' ', 2)
        if len(parts) >= 3:
            plugin_name, command = parts[1], parts[2]
            response = plugins.execute_plugin(plugin_name, command)
        else:
            response = "Usage: plugin <name> <command>"
    elif 'be creative' in user_input.lower() or 'creative' in user_input.lower():
        # Generate creative response
        creative_idea = nlp.generate_creative_task(user_input)
        response = f"Here's a creative idea: {creative_idea}"
    elif user_input.lower().startswith('set voice to '):
        profile = user_input.lower().replace('set voice to ', '').strip()
        response = tts.set_voice_profile(profile)
    elif user_input.lower() == 'list voice profiles':
        profiles = tts.get_voice_profiles()
        response = f"Available voice profiles: {', '.join(profiles)}"
    elif user_input.lower().startswith('customize voice '):
        # Parse customization command
        parts = user_input.lower().replace('customize voice ', '').split()
        params = {}
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                try:
                    if key in ['speed', 'pitch', 'volume']:
                        params[key] = float(value)
                    elif key == 'voice':
                        params[key] = value
                except ValueError:
                    pass
        if params:
            response = tts.customize_voice(**params)
        else:
            response = "Usage: customize voice speed=1.0 pitch=0 volume=80 voice=male"
    elif user_input.lower().startswith('store api key '):
        # Format: store api key service_name your_api_key_here
        parts = user_input.split(' ', 4)
        if len(parts) >= 5:
            service = parts[3]
            api_key = parts[4]
            response = security.store_api_key(service, api_key)
        else:
            response = "Usage: store api key <service> <key>"
    elif user_input.lower().startswith('get api key '):
        service = user_input.replace('get api key ', '').strip()
        api_key = security.get_api_key(service)
        if api_key:
            response = f"API key for {service}: {api_key[:8]}..."  # Show only first 8 chars
        else:
            response = f"No API key stored for {service}"
    else:
        # Generate response
        ux.show_thinking_animation()
        # Get context from memory
        recent_turns = memory.get_recent_turns(2)
        context = " ".join([f"User: {t['user']} AI: {t['ai']}" for t in recent_turns])
        response = nlp.generate_response(user_input, context)
        ux.stop_thinking_animation()

    # Show cinematic conversation flow
    ux.show_conversation_flow(user_input, response)

    # Speak
    tts.speak(response)

    # Memory
    memory.add_turn(user_input, response)

    # Log with performance metrics
    perf_status = performance.get_status()
    logging_mod.log({
        'user': user_input,
        'ai': response,
        'mode': current_mode,
        'performance': perf_status,
        'timestamp': time.time()
    })

    return None

# Start voice loops in background
voice_thread = threading.Thread(target=voice_loop, daemon=True)
voice_thread.start()

push_to_talk_thread = threading.Thread(target=push_to_talk_loop, daemon=True)
push_to_talk_thread.start()

# Start performance monitoring thread
def performance_monitor():
    while True:
        ux.update_performance_status(performance)
        time.sleep(5)  # Update every 5 seconds

perf_thread = threading.Thread(target=performance_monitor, daemon=True)
perf_thread.start()

# Main loop for text input
while True:
    try:
        user_input = input("You (text): ")
        result = process_input(user_input)
        if result == 'quit':
            break
    except KeyboardInterrupt:
        break

# Cleanup
wakeword.stop()