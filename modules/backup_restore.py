import os
import json
import shutil
import gzip
import tarfile
from datetime import datetime
from pathlib import Path

class BackupRestoreModule:
    def __init__(self, config):
        self.config = config
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)

        # Files and directories to backup
        self.backup_items = [
            'memory.db',           # Conversation memory
            'logs/',              # Conversation logs
            'plugins/',           # User plugins
            'security_key.key',   # Encryption keys
            'memory_key.key',     # Memory encryption keys
            'config.json',        # Configuration (selective)
            'fine_tuned_nlp/',    # Fine-tuned models
        ]

    def create_backup(self, name=None):
        """Create a compressed backup archive"""
        if name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name = f"auralis_backup_{timestamp}"

        backup_path = self.backup_dir / f"{name}.tar.gz"

        try:
            with tarfile.open(backup_path, 'w:gz') as tar:
                for item in self.backup_items:
                    if os.path.exists(item):
                        if os.path.isdir(item):
                            # Add directory
                            tar.add(item, arcname=os.path.basename(item))
                        else:
                            # Add file
                            tar.add(item, arcname=os.path.basename(item))

                # Add metadata
                metadata = {
                    'created_at': datetime.now().isoformat(),
                    'version': self.config['app_identity']['version'],
                    'items': self.backup_items
                }

                metadata_file = self.backup_dir / 'backup_metadata.json'
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

                tar.add(metadata_file, arcname='backup_metadata.json')
                metadata_file.unlink()  # Clean up

            return f"Backup created successfully: {backup_path}"
        except Exception as e:
            return f"Backup creation failed: {e}"

    def list_backups(self):
        """List all available backups"""
        backups = []
        for file in self.backup_dir.glob('*.tar.gz'):
            try:
                # Extract metadata without full extraction
                with tarfile.open(file, 'r:gz') as tar:
                    metadata_file = tar.extractfile('backup_metadata.json')
                    if metadata_file:
                        metadata = json.load(metadata_file)
                        backups.append({
                            'name': file.stem,
                            'path': str(file),
                            'created_at': metadata.get('created_at', 'Unknown'),
                            'version': metadata.get('version', 'Unknown'),
                            'size_mb': round(file.stat().st_size / (1024 * 1024), 2)
                        })
            except:
                # If metadata can't be read, add basic info
                backups.append({
                    'name': file.stem,
                    'path': str(file),
                    'created_at': 'Unknown',
                    'version': 'Unknown',
                    'size_mb': round(file.stat().st_size / (1024 * 1024), 2)
                })

        return backups

    def restore_backup(self, backup_name, restore_items=None):
        """Restore from a backup archive"""
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"

        if not backup_path.exists():
            return f"Backup not found: {backup_name}"

        try:
            # Create restore directory
            restore_dir = self.backup_dir / f"restore_{backup_name}"
            restore_dir.mkdir(exist_ok=True)

            # Extract backup
            with tarfile.open(backup_path, 'r:gz') as tar:
                # Read metadata first
                metadata_file = tar.extractfile('backup_metadata.json')
                if metadata_file:
                    metadata = json.load(metadata_file)
                    print(f"Restoring backup from {metadata.get('created_at', 'Unknown')}")

                # Extract files
                items_to_restore = restore_items if restore_items else self.backup_items

                for item in items_to_restore:
                    item_name = os.path.basename(item.rstrip('/'))
                    if item_name in [member.name for member in tar.getmembers()]:
                        # Create backup of current file/directory
                        if os.path.exists(item_name):
                            backup_current = f"{item_name}.backup_before_restore"
                            if os.path.isdir(item_name):
                                shutil.copytree(item_name, backup_current)
                            else:
                                shutil.copy2(item_name, backup_current)

                        # Extract
                        tar.extract(item_name, path='.')

            return f"Backup restored successfully. Current files backed up with '.backup_before_restore' suffix."
        except Exception as e:
            return f"Backup restoration failed: {e}"

    def delete_backup(self, backup_name):
        """Delete a backup archive"""
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"

        if backup_path.exists():
            backup_path.unlink()
            return f"Backup deleted: {backup_name}"
        else:
            return f"Backup not found: {backup_name}"

    def export_conversations(self, format='json'):
        """Export conversation history in various formats"""
        try:
            import sqlite3

            conn = sqlite3.connect('memory.db')
            cursor = conn.cursor()

            # Get all conversations
            cursor.execute("SELECT user, ai, timestamp FROM turns ORDER BY timestamp")
            conversations = cursor.fetchall()
            conn.close()

            if format == 'json':
                # Export as JSON
                conv_list = [
                    {
                        'user': user,
                        'ai': ai,
                        'timestamp': timestamp
                    } for user, ai, timestamp in conversations
                ]

                export_path = self.backup_dir / f"conversations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(export_path, 'w') as f:
                    json.dump(conv_list, f, indent=2)

            elif format == 'txt':
                # Export as text
                export_path = self.backup_dir / f"conversations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(export_path, 'w') as f:
                    for user, ai, timestamp in conversations:
                        dt = datetime.fromtimestamp(timestamp)
                        f.write(f"[{dt.strftime('%Y-%m-%d %H:%M:%S')}]\n")
                        f.write(f"User: {user}\n")
                        f.write(f"Auralis: {ai}\n\n")

            return f"Conversations exported to: {export_path}"
        except Exception as e:
            return f"Export failed: {e}"

    def import_conversations(self, import_path):
        """Import conversations from export file"""
        if not os.path.exists(import_path):
            return f"Import file not found: {import_path}"

        try:
            import sqlite3

            conn = sqlite3.connect('memory.db')
            cursor = conn.cursor()

            with open(import_path, 'r') as f:
                if import_path.endswith('.json'):
                    conversations = json.load(f)
                    for conv in conversations:
                        cursor.execute(
                            "INSERT INTO turns (user, ai, timestamp) VALUES (?, ?, ?)",
                            (conv['user'], conv['ai'], conv['timestamp'])
                        )
                elif import_path.endswith('.txt'):
                    # Basic text parsing (simplified)
                    content = f.read()
                    # This would need more sophisticated parsing
                    return "Text import not implemented yet"

            conn.commit()
            conn.close()

            return f"Conversations imported from: {import_path}"
        except Exception as e:
            return f"Import failed: {e}"

    def cleanup_old_backups(self, keep_days=30):
        """Delete backups older than specified days"""
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        deleted_count = 0

        for file in self.backup_dir.glob('*.tar.gz'):
            if file.stat().st_mtime < cutoff_time:
                file.unlink()
                deleted_count += 1

        return f"Cleaned up {deleted_count} old backups"