import re
from collections import defaultdict

class TaskOrchestrator:
    def __init__(self, security_module, screen_control, screen_reader, tts, plugins):
        self.security = security_module
        self.screen_control = screen_control
        self.screen_reader = screen_reader
        self.tts = tts
        self.plugins = plugins

    def classify_intent(self, user_input):
        # Simple regex-based intent classification
        intents = {
            'read_screen': re.search(r'read screen|scan screen', user_input, re.I),
            'summarize_screen': re.search(r'summarize screen', user_input, re.I),
            'search_screen': re.search(r'search screen for', user_input, re.I),
            'type_text': re.search(r'type ', user_input, re.I),
            'click': re.search(r'click at', user_input, re.I),
            'open_app': re.search(r'open ', user_input, re.I),
            'close_window': re.search(r'close window', user_input, re.I),
            'scroll': re.search(r'scroll', user_input, re.I),
            'plugin': re.search(r'plugin ', user_input, re.I),
            'time': re.search(r'time', user_input, re.I),
            'help': re.search(r'help', user_input, re.I),
            'quit': re.search(r'quit', user_input, re.I),
            'settings': re.search(r'set ', user_input, re.I),
            'toggle': re.search(r'toggle ', user_input, re.I),
            'clear_logs': re.search(r'clear logs', user_input, re.I),
        }
        for intent, match in intents.items():
            if match:
                return intent
        return 'chat'  # Default to NLP chat

    def plan_tasks(self, intent, user_input):
        # Simple planner: create a list of tasks with dependencies, costs, permissions
        tasks = []
        if intent == 'read_screen':
            tasks.append({
                'action': 'read_screen_area',
                'module': 'screen_reader',
                'params': {},
                'cost': 1,
                'permission': 'screen_reading'
            })
        elif intent == 'summarize_screen':
            tasks.append({
                'action': 'read_screen_area',
                'module': 'screen_reader',
                'params': {},
                'cost': 1,
                'permission': 'screen_reading'
            })
            tasks.append({
                'action': 'summarize_content',
                'module': 'screen_reader',
                'params': {'text': 'from_previous'},
                'cost': 0.5,
                'permission': 'screen_reading',
                'depends_on': 0
            })
        elif intent == 'search_screen':
            keyword = user_input.split('search screen for ')[1]
            tasks.append({
                'action': 'read_screen_area',
                'module': 'screen_reader',
                'params': {},
                'cost': 1,
                'permission': 'screen_reading'
            })
            tasks.append({
                'action': 'search_for_keyword',
                'module': 'screen_reader',
                'params': {'text': 'from_previous', 'keyword': keyword},
                'cost': 0.5,
                'permission': 'screen_reading',
                'depends_on': 0
            })
        elif intent == 'type_text':
            text = user_input[5:]
            tasks.append({
                'action': 'type_text',
                'module': 'screen_control',
                'params': {'text': text},
                'cost': 0.5,
                'permission': 'keyboard_mouse_control'
            })
        elif intent == 'click':
            parts = user_input.split()
            x, y = int(parts[-2]), int(parts[-1])
            tasks.append({
                'action': 'click_at',
                'module': 'screen_control',
                'params': {'x': x, 'y': y},
                'cost': 0.5,
                'permission': 'keyboard_mouse_control'
            })
        elif intent == 'open_app':
            app = user_input[5:]
            tasks.append({
                'action': 'open_app',
                'module': 'screen_control',
                'params': {'app': app},
                'cost': 1,
                'permission': 'keyboard_mouse_control'
            })
        elif intent == 'close_window':
            tasks.append({
                'action': 'close_window',
                'module': 'screen_control',
                'params': {},
                'cost': 0.5,
                'permission': 'keyboard_mouse_control'
            })
        elif intent == 'scroll':
            direction = 'up' if 'up' in user_input else 'down'
            tasks.append({
                'action': 'scroll',
                'module': 'screen_control',
                'params': {'direction': direction},
                'cost': 0.2,
                'permission': 'keyboard_mouse_control'
            })
        elif intent == 'plugin':
            parts = user_input.split()
            name = parts[1]
            args = parts[2:]
            tasks.append({
                'action': 'execute_plugin',
                'module': 'plugins',
                'params': {'name': name, 'args': args},
                'cost': 1,
                'permission': 'plugin_execution'
            })
        elif intent == 'time':
            tasks.append({
                'action': 'get_time',
                'module': 'system',
                'params': {},
                'cost': 0.1,
                'permission': None
            })
        elif intent == 'help':
            tasks.append({
                'action': 'show_help',
                'module': 'system',
                'params': {},
                'cost': 0.1,
                'permission': None
            })
        elif intent == 'quit':
            tasks.append({
                'action': 'quit',
                'module': 'system',
                'params': {},
                'cost': 0.1,
                'permission': None
            })
        elif intent == 'settings':
            # Parse setting
            if 'voice' in user_input:
                voice = user_input.split('set voice ')[1]
                tasks.append({
                    'action': 'set_voice',
                    'module': 'tts',
                    'params': {'voice': voice},
                    'cost': 0.2,
                    'permission': None
                })
            # Add more
        elif intent == 'toggle':
            if 'offline' in user_input:
                tasks.append({
                    'action': 'toggle_mode',
                    'module': 'switch',
                    'params': {},
                    'cost': 0.5,
                    'permission': None
                })
        elif intent == 'clear_logs':
            tasks.append({
                'action': 'clear_logs',
                'module': 'logger',
                'params': {},
                'cost': 0.5,
                'permission': None
            })
        else:
            tasks.append({
                'action': 'chat_response',
                'module': 'nlp',
                'params': {'input': user_input},
                'cost': 2,
                'permission': None
            })
        return tasks

    def execute_plan(self, tasks):
        results = []
        for task in tasks:
            if not self.check_permission(task.get('permission')):
                results.append(f"Permission denied for {task['action']}")
                continue
            result = self.execute_task(task)
            results.append(result)
        return results

    def check_permission(self, permission):
        if not permission:
            return True
        return self.security.check_permission(permission)

    def execute_task(self, task):
        module = task['module']
        action = task['action']
        params = task['params']
        if module == 'screen_reader':
            if action == 'read_screen_area':
                return self.screen_reader.read_screen_area()
            elif action == 'summarize_content':
                text = params.get('text', 'from_previous')  # Assume from previous
                return self.screen_reader.summarize_content(text)
            elif action == 'search_for_keyword':
                text = params.get('text')
                keyword = params['keyword']
                return self.screen_reader.search_for_keyword(text, keyword)
        elif module == 'screen_control':
            if action == 'type_text':
                self.screen_control.type_text(params['text'])
                return "Typed text"
            elif action == 'click_at':
                self.screen_control.click_at(params['x'], params['y'])
                return "Clicked"
            elif action == 'open_app':
                import subprocess
                try:
                    subprocess.run([params['app']])
                    return f"Opened {params['app']}"
                except:
                    return f"Failed to open {params['app']}"
            elif action == 'close_window':
                self.screen_control.close_window()
                return "Closed window"
            elif action == 'scroll':
                self.screen_control.scroll(params['direction'])
                return f"Scrolled {params['direction']}"
        elif module == 'plugins':
            return self.plugins.execute(params['name'], *params['args'])
        elif module == 'tts':
            if action == 'set_voice':
                self.tts.set_voice(params['voice'])
                return f"Voice set to {params['voice']}"
        elif module == 'system':
            if action == 'get_time':
                from datetime import datetime
                return datetime.now().strftime('%H:%M:%S')
            elif action == 'show_help':
                return "Help: Commands include read screen, type, click, etc."
            elif action == 'quit':
                return "Quitting"
        elif module == 'switch':
            # Assume switch is global
            return "Toggled mode"
        elif module == 'logger':
            # Assume logger global
            return "Logs cleared"
        elif module == 'nlp':
            # Assume natural_dialogue
            return "Chat response"
        return "Task executed"