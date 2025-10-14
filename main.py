#!/usr/bin/env python3
"""
Auralis - Terminal J.A.R.V.I.S.-style Assistant
Main entry point that starts the daemon supervisor or handles CLI commands.
"""

import json
import sys
import os
import argparse

# Load config
with open('config.json') as f:
    config = json.load(f)

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

def handle_cli_commands():
    """Handle CLI commands without starting daemon"""
    parser = argparse.ArgumentParser(description='Auralis CLI')
    parser.add_argument('--speak', type=str, help='Speak text using TTS')
    parser.add_argument('--plugin', choices=['install', 'list', 'remove'], help='Plugin management')
    parser.add_argument('--plugin-name', type=str, help='Plugin name for install/remove')
    parser.add_argument('--version', action='store_true', help='Show version')

    args = parser.parse_args()

    if args.version:
        print(f"{config['app_identity']['name']} v{config['app_identity']['version']}")
        return

    if args.speak:
        # Import TTS and speak
        try:
            from tts_offline import TTSModuleOffline
            tts = TTSModuleOffline(config)
            tts.initialize()
            tts.speak(args.speak)
            print(f"Spoke: {args.speak}")
        except Exception as e:
            print(f"Error speaking: {e}")
        return

    if args.plugin:
        try:
            from plugins import PluginHostModule
            plugins = PluginHostModule(config)

            if args.plugin == 'list':
                plugin_list = plugins.list_plugins()
                for p in plugin_list:
                    print(f"- {p['name']}: {p['description']}")
            elif args.plugin == 'install' and args.plugin_name:
                result = plugins.install_plugin(args.plugin_name)
                print(f"Installed plugin: {args.plugin_name}")
            elif args.plugin == 'remove' and args.plugin_name:
                result = plugins.remove_plugin(args.plugin_name)
                print(f"Removed plugin: {args.plugin_name}")
            else:
                print("Use --plugin-name with install/remove")
        except Exception as e:
            print(f"Plugin error: {e}")
        return

    # If no CLI command, start daemon
    start_daemon()

def start_daemon():
    """Start the daemon supervisor"""
    print(f"Starting {config['app_identity']['name']} v{config['app_identity']['version']}")

    # Import daemon supervisor
    from daemon_supervisor import AuralisDaemon

    # Start the daemon
    daemon = AuralisDaemon(config)
    daemon.start()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        handle_cli_commands()
    else:
        start_daemon()