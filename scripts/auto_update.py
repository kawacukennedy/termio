#!/usr/bin/env python3
"""
Auto-update mechanism for Auralis
Checks GitHub releases and updates if newer version available
"""

import json
import urllib.request
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil

class AutoUpdater:
    def __init__(self):
        self.repo = "sst/auralis"  # Replace with actual repo
        self.current_version = self.get_current_version()

    def get_current_version(self):
        """Get current version from config"""
        try:
            with open('config.json') as f:
                config = json.load(f)
                return config['app_identity']['version']
        except:
            return "0.0.0"

    def check_for_updates(self):
        """Check GitHub for latest release"""
        try:
            url = f"https://api.github.com/repos/{self.repo}/releases/latest"
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                latest_version = data['tag_name'].lstrip('v')
                return latest_version, data['assets']
        except Exception as e:
            print(f"Failed to check for updates: {e}")
            return None, None

    def compare_versions(self, current, latest):
        """Compare version strings"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))

        return version_tuple(latest) > version_tuple(current)

    def download_update(self, assets):
        """Download and install update"""
        # Find the appropriate asset (e.g., auralis-update.tar.gz)
        for asset in assets:
            if 'update' in asset['name'] and asset['name'].endswith('.tar.gz'):
                download_url = asset['browser_download_url']
                break
        else:
            print("No update package found")
            return False

        # Download to temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "update.tar.gz"
            print(f"Downloading update from {download_url}")
            urllib.request.urlretrieve(download_url, archive_path)

            # Extract
            import tarfile
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(temp_dir)

            # Backup current installation
            backup_dir = Path('backup')
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.copytree('.', backup_dir, ignore=shutil.ignore_patterns('backup', '__pycache__', '*.pyc'))

            # Update files (simple copy for now)
            update_dir = Path(temp_dir) / "auralis"
            for item in update_dir.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(update_dir)
                    dest = Path('.') / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)

            print("Update installed successfully")
            return True

    def run(self):
        """Main update process"""
        print(f"Current version: {self.current_version}")
        print("Checking for updates...")

        latest_version, assets = self.check_for_updates()
        if not latest_version:
            return

        print(f"Latest version: {latest_version}")

        if self.compare_versions(self.current_version, latest_version):
            print("Update available!")
            if input("Install update? (y/N): ").lower() == 'y':
                if self.download_update(assets):
                    print("Please restart Auralis")
                    sys.exit(0)
                else:
                    print("Update failed")
        else:
            print("Already up to date")

if __name__ == "__main__":
    updater = AutoUpdater()
    updater.run()