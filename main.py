#!/usr/bin/env python3
"""
Auralis - Terminal J.A.R.V.I.S.-style Assistant
Main entry point that starts the daemon supervisor.
"""

import json
import sys
import os

# Load config
with open('config.json') as f:
    config = json.load(f)

print(f"Starting {config['app_identity']['name']} v{config['app_identity']['version']}")

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

# Import daemon supervisor
from daemon_supervisor import AuralisDaemon

# Start the daemon
if __name__ == "__main__":
    daemon = AuralisDaemon(config)
    daemon.start()