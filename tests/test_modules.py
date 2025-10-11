import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

class TestAuralisModules(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures"""
        # Mock config for all tests
        self.mock_config = {
            "app_identity": {"name": "Auralis", "version": "1.0.0"},
            "voice_interface": {
                "voice_response": {
                    "interruptible": True,
                    "voices": ["male", "female", "neutral"],
                    "speed_range": "0.9x-1.2x"
                }
            },
            "memory_management": {
                "short_term": {"max_turns": 3},
                "long_term": {"encrypted_sqlite": True}
            },
            "plugins_and_extensibility": {
                "plugin_system": {
                    "max_memory_mb": 10,
                    "permission_scopes": ["filesystem_read"]
                }
            },
            "terminal_ui_ux": {
                "visual_feedback": {
                    "status_bar_elements": ["mic_status", "mode_indicator", "cpu_usage", "network_status"]
                }
            },
            "performance_optimizations": {
                "lazy_load_modules": True,
                "idle_sleep": True,
                "memory_efficient_caching": True
            },
            "security_privacy": {
                "permissions": ["microphone", "keyboard/mouse optional"],
                "offline_privacy": "100% local",
                "user_controls": ["pause", "clear logs", "toggle offline/online"]
            }
        }

    @patch('ux_flow_manager.time')
    def test_ux_flow_manager(self, mock_time):
        """Test UX Flow Manager basic functionality"""
        from ux_flow_manager import UXFlowManager

        ux = UXFlowManager(self.mock_config)

        # Test status updates
        ux.update_status('test_key', 'test_value')
        self.assertEqual(ux.status_bar['test_key'], 'test_value')

        # Test error messages
        ux.show_error_message('misheard_voice')
        # Should not raise exception

    @patch('memory.Fernet.generate_key', return_value=b'test_key')
    @patch.dict('sys.modules', {'cryptography': MagicMock(), 'cryptography.fernet': MagicMock(), 'sqlite3': MagicMock()})
    def test_memory_module(self, mock_generate_key):
        """Test memory module basic functionality"""
        from memory import ConversationMemoryModule

        memory = ConversationMemoryModule(self.mock_config)

        # Test adding turns
        memory.add_turn("user message", "ai response")
        self.assertEqual(len(memory.short_term_memory), 1)

    def test_settings_module(self):
        """Test settings module"""
        from settings import SettingsModule

        settings = SettingsModule(self.mock_config)

        # Test getting nested settings
        result = settings.get_setting('app_identity.name')
        self.assertEqual(result, 'Auralis')

    @patch.dict('sys.modules', {'cryptography': MagicMock(), 'cryptography.fernet': MagicMock()})
    def test_security_module(self):
        """Test security module"""
        from security import SecurityModule

        security = SecurityModule(self.mock_config)

        # Test basic functionality
        self.assertIsInstance(security, SecurityModule)

    @patch.dict('sys.modules', {'psutil': MagicMock()})
    def test_performance_module(self):
        """Test performance module"""
        from performance import PerformanceOptimizerModule

        perf = PerformanceOptimizerModule(self.mock_config)

        status = perf.get_status()
        self.assertIn('cpu_percent', status)
        self.assertIn('memory_percent', status)

    def test_plugins_module(self):
        """Test plugins module"""
        from plugins import PluginHostModule

        plugins = PluginHostModule(self.mock_config)

        # Test plugin template creation
        template_path = plugins.create_plugin_template('test_plugin')
        self.assertTrue(str(template_path).endswith('test_plugin.py'))

        # Clean up
        if os.path.exists(template_path):
            os.remove(template_path)

    def test_model_training_module(self):
        """Test model training module"""
        from model_training import ModelTrainingModule

        training = ModelTrainingModule(self.mock_config)

        status = training.get_training_status()
        self.assertIn('supported_models', status)
        self.assertIn('training_config', status)

if __name__ == '__main__':
    unittest.main()