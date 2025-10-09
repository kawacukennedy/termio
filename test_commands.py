#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Mock or skip imports that fail
try:
    from memory import ConversationMemory
    memory = ConversationMemory(enable_long_term=False)  # Disable for test
except:
    memory = None

try:
    from logging_storage import LoggingAndStorage
    logger = LoggingAndStorage()
except:
    logger = None

try:
    from settings import Settings
    settings = Settings()
except:
    settings = None

try:
    from offline_online_switch import OfflineOnlineSwitchModule
    switch = OfflineOnlineSwitchModule()
except:
    switch = None

try:
    import nlp
    nlp_module = nlp.UltraLightNLPModule()
except:
    nlp_module = None

try:
    import tts
    tts_module = tts.TextToSpeechModule()
except:
    tts_module = None

try:
    from screen_reader import ScreenReaderModule
    screen_reader = ScreenReaderModule()
except:
    screen_reader = None

try:
    from screen_control import ScreenControlModule
    screen_control = ScreenControlModule()
except:
    screen_control = None

try:
    from plugins import PluginModule
    plugins = PluginModule()
    plugins.load_plugins()
except:
    plugins = None

def process_input(user_input):
    user_input = user_input.strip()
    if not user_input:
        return ""

    # Command parsing
    if "read screen" in user_input.lower():
        if screen_reader:
            text = screen_reader.read_screen_area()
            response = f"Screen text: {text[:500]}..."
        else:
            response = "Screen reader not available"
    elif user_input.lower().startswith("type "):
        if screen_control:
            text_to_type = user_input[5:]
            screen_control.type_text(text_to_type)
            response = f"Typed: {text_to_type}"
        else:
            response = "Screen control not available"
    elif "click at" in user_input.lower():
        parts = user_input.split()
        try:
            x, y = int(parts[-2]), int(parts[-1])
            if screen_control:
                screen_control.click_at(x, y)
                response = f"Clicked at {x}, {y}"
            else:
                response = "Screen control not available"
        except:
            response = "Invalid coordinates"
    elif "time" in user_input.lower():
        from datetime import datetime
        response = f"The time is {datetime.now().strftime('%H:%M:%S')}"
    elif user_input.lower().startswith('plugin '):
        if plugins:
            parts = user_input.split()
            if len(parts) > 1:
                response = plugins.execute(parts[1], *parts[2:])
            else:
                response = "Usage: plugin <name> [args]"
        else:
            response = "Plugins not available"
    elif "list plugins" in user_input.lower():
        if plugins:
            response = "Available plugins: " + ', '.join(plugins.list_plugins())
        else:
            response = "Plugins not available"
    elif "summarize screen" in user_input.lower():
        if screen_reader:
            text = screen_reader.read_screen_area()
            response = screen_reader.summarize_content(text)
        else:
            response = "Screen reader not available"
    elif user_input.lower().startswith("search screen for "):
        if screen_reader:
            keyword = user_input[17:]
            text = screen_reader.read_screen_area()
            found = screen_reader.search_for_keyword(text, keyword)
            response = f"Keyword '{keyword}' found" if found else f"Keyword '{keyword}' not found"
        else:
            response = "Screen reader not available"
    elif "clear logs" in user_input.lower():
        if logger:
            logger.clear_logs()
            response = "Logs cleared"
        else:
            response = "Logger not available"
    elif user_input.lower().startswith("set voice "):
        if tts_module:
            voice = user_input[10:].strip()
            tts_module.set_voice(voice)
            response = f"Voice set to {voice}"
        else:
            response = "TTS not available"
    elif user_input.lower().startswith("set speed "):
        if tts_module:
            try:
                speed = float(user_input[10:].strip())
                tts_module.set_speed(speed)
                response = f"Speed set to {speed}x"
            except:
                response = "Invalid speed"
        else:
            response = "TTS not available"
    elif user_input.lower().startswith("set pitch "):
        if tts_module:
            try:
                pitch = int(user_input[10:].strip())
                tts_module.set_pitch(pitch)
                response = f"Pitch set to {pitch}"
            except:
                response = "Invalid pitch"
        else:
            response = "TTS not available"
    elif user_input.lower().startswith("set profile "):
        if tts_module:
            profile = user_input[12:].strip()
            tts_module.set_profile(profile)
            response = f"Profile set to {profile}"
        else:
            response = "TTS not available"
    elif "close window" in user_input.lower():
        if screen_control:
            screen_control.close_window()
            response = "Window closed"
        else:
            response = "Screen control not available"
    elif "scroll up" in user_input.lower():
        if screen_control:
            screen_control.scroll('up')
            response = "Scrolled up"
        else:
            response = "Screen control not available"
    elif "scroll down" in user_input.lower():
        if screen_control:
            screen_control.scroll('down')
            response = "Scrolled down"
        else:
            response = "Screen control not available"
    elif user_input.lower().startswith("open "):
        app = user_input[5:].strip()
        import subprocess
        try:
            subprocess.run([app])
            response = f"Opened {app}"
        except:
            response = f"Failed to open {app}"
    elif "toggle offline" in user_input.lower():
        if switch:
            if switch.get_mode() == 'offline':
                switch.switch_to_online()
            else:
                switch.switch_to_offline()
            response = f"Switched to {switch.get_mode()} mode"
        else:
            response = "Switch not available"
    elif "pause" in user_input.lower():
        response = "Assistant paused"
    elif "quit" in user_input.lower():
        response = "Goodbye"
    else:
        # NLP response
        if memory:
            context = memory.get_context()
            prompt = ""
            for turn in context:
                prompt += f"User: {turn['user']}\nAI: {turn['response']}\n"
            prompt += f"User: {user_input}\nAI:"
        else:
            prompt = f"User: {user_input}\nAI:"

        if switch and switch.get_mode() == 'offline':
            if nlp_module:
                try:
                    response = nlp_module.generate_response(prompt)
                except Exception as e:
                    response = "NLP error: " + str(e)
            else:
                response = "Offline NLP not available. Echo: " + user_input
        else:
            if os.getenv('OPENAI_API_KEY'):
                try:
                    import openai
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
            else:
                response = "Online mode but no API key. Echo: " + user_input

    if memory:
        memory.add_interaction(user_input, response)
    if logger:
        logger.log_interaction(user_input, response)
    return response

if __name__ == "__main__":
    # Test example commands
    test_commands = [
        "what time is it?",
        "type Hello World",
        "read screen",
        "summarize screen",
        "search screen for error",
        "close window",
        "scroll down",
        "open calculator",
        "set voice male",
        "set speed 1.1",
        "set profile casual",
        "toggle offline",
        "list plugins",
        "plugin calculator 2 + 3",
        "clear logs",
        "Explain basic math",
        "Tell a joke",
        "quit"
    ]

    for cmd in test_commands:
        print(f"Input: {cmd}")
        response = process_input(cmd)
        print(f"Response: {response}")
        print("-" * 50)