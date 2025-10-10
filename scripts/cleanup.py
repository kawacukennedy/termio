#!/usr/bin/env python3
"""
Cleanup script for Auralis to maintain <100MB footprint
Removes temporary files, caches, and ensures compliance with size limits
"""

import os
import shutil
from pathlib import Path
import time

class CleanupManager:
    def __init__(self, root_dir='.'):
        self.root_dir = Path(root_dir).resolve()
        self.max_size_mb = 100

    def get_directory_size(self, path):
        """Get directory size in MB"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except OSError:
                    pass
        return total_size / (1024 * 1024)

    def cleanup_temp_files(self):
        """Remove temporary and cache files"""
        cleaned_items = []

        # Remove Python cache
        for pycache in self.root_dir.rglob('__pycache__'):
            if pycache.is_dir():
                shutil.rmtree(pycache)
                cleaned_items.append(f"Removed {pycache}")

        # Remove .pyc files
        for pyc_file in self.root_dir.rglob('*.pyc'):
            pyc_file.unlink()
            cleaned_items.append(f"Removed {pyc_file}")

        # Remove .DS_Store files (macOS)
        for ds_store in self.root_dir.rglob('.DS_Store'):
            ds_store.unlink()
            cleaned_items.append(f"Removed {ds_store}")

        # Clean logs older than 7 days
        logs_dir = self.root_dir / 'logs'
        if logs_dir.exists():
            cutoff_time = time.time() - (7 * 24 * 60 * 60)  # 7 days
            for log_file in logs_dir.glob('*'):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    cleaned_items.append(f"Removed old log {log_file}")

        # Clean old backups (keep last 5)
        backups_dir = self.root_dir / 'backups'
        if backups_dir.exists():
            backup_files = sorted(backups_dir.glob('*.tar.gz'), key=lambda x: x.stat().st_mtime, reverse=True)
            if len(backup_files) > 5:
                for old_backup in backup_files[5:]:
                    old_backup.unlink()
                    cleaned_items.append(f"Removed old backup {old_backup}")

        return cleaned_items

    def check_size_compliance(self):
        """Check if directory size is within limits"""
        current_size = self.get_directory_size(self.root_dir)
        is_compliant = current_size < self.max_size_mb

        return {
            'current_size_mb': round(current_size, 2),
            'max_size_mb': self.max_size_mb,
            'is_compliant': is_compliant,
            'overage_mb': round(max(0, current_size - self.max_size_mb), 2)
        }

    def optimize_for_size(self):
        """Perform all size optimizations"""
        print("🧹 Starting Auralis cleanup and size optimization...")

        # Cleanup temp files
        cleaned = self.cleanup_temp_files()
        if cleaned:
            print(f"✅ Cleaned {len(cleaned)} items:")
            for item in cleaned[:5]:  # Show first 5
                print(f"   {item}")
            if len(cleaned) > 5:
                print(f"   ... and {len(cleaned) - 5} more")

        # Check size compliance
        size_info = self.check_size_compliance()
        print("\n📊 Size Check:")
        print(f"   Current size: {size_info['current_size_mb']} MB")
        print(f"   Size limit: {size_info['max_size_mb']} MB")

        if size_info['is_compliant']:
            print("✅ Size compliant - within limits")
        else:
            print(f"⚠️  Over limit by {size_info['overage_mb']} MB")
            print("   Consider removing large files or optimizing storage")

        # Additional recommendations
        print("\n💡 Recommendations:")
        print("   • Run cleanup regularly to maintain size")
        print("   • Store large files externally")
        print("   • Use git LFS for large assets if needed")
        print("   • Keep offline models compressed")

        return size_info

if __name__ == '__main__':
    cleanup = CleanupManager()
    cleanup.optimize_for_size()