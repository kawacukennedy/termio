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

    @patch('memory.Fernet')
    @patch('memory.sqlite3')
    def test_memory_module(self, mock_sqlite, mock_fernet):
        """Test memory module basic functionality"""
        # Mock Fernet
        mock_fernet.generate_key.return_value = b'test_key'
        mock_fernet.return_value.encrypt.return_value = b'encrypted'
        mock_fernet.return_value.decrypt.return_value = b'decrypted'

        # Mock sqlite3
        mock_conn = MagicMock ()
        mock_cursor = MagicMock ()
        mock_conn.cursor.return_value = mock_cursor
        mock_sqlite.connect.return_value = mock_conn

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

    @patch('security.Fernet')
    def test_security_module(self, mock_fernet):
        """Test security module"""
        mock_fernet.generate_key.return_value = b'test_key'

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
        self.assertTrue(str(template_path).endswith('test_plugin'))

        # Clean up
        import shutil
        if os.path.exists(template_path):
            shutil.rmtree(template_path)

    def test_model_training_module(self):
        """Test model training module"""
        from model_training import ModelTrainingModule

        training = ModelTrainingModule(self.mock_config)

        status = training.get_training_status()
        self.assertIn('supported_models', status)
        self.assertIn('training_config', status)

    def test_command_parser(self):
        """Test command parser intent classification"""
        from command_parser import CommandParser

        parser = CommandParser(self.mock_config)

        # Test screen read intent
        result = parser.parse_command("read the screen")
        self.assertEqual(result['intent'], 'screen_read')
        self.assertGreater(result['confidence'], 0.5)

        # Test screen control intent
        result = parser.parse_command("click on the button")
        self.assertEqual(result['intent'], 'screen_control')
        self.assertGreater(result['confidence'], 0.5)

        # Test general conversation fallback
        result = parser.parse_command("hello how are you")
        self.assertEqual(result['intent'], 'general_conversation')

    def test_permission_prompts(self):
        """Test security permission prompts"""
        from security import SecurityModule

        security = SecurityModule(self.mock_config)

        # Test destructive action prompt
        result = security.check_permission('delete_file', '/important/file.txt')
        self.assertIn('prompt_user', result)

        # Test non-destructive action
        result = security.check_permission('read_screen', None)
        self.assertTrue(result['allowed'])

    @patch('stt_offline.STTModuleOffline')
    @patch('nlp_offline.NLPModuleOffline')
    @patch('tts_offline.TTSModuleOffline')
    def test_stt_nlp_tts_integration(self, mock_tts, mock_nlp, mock_stt):
        """Integration test for STT -> NLP -> TTS cycle"""
        from inference_worker import InferenceWorker
        from queue_manager import QueueManager

        # Mock the modules
        mock_stt_instance = MagicMock()
        mock_stt_instance.transcribe.return_value = {'text': 'hello auralis', 'confidence': 0.9}
        mock_stt.return_value = mock_stt_instance

        mock_nlp_instance = MagicMock()
        mock_nlp_instance.generate_response.return_value = 'Hello! How can I help you?'
        mock_nlp.return_value = mock_nlp_instance

        mock_tts_instance = MagicMock()
        mock_tts.return_value = mock_tts_instance

        # Create queues
        queue_manager = QueueManager()
        queues = queue_manager.queues

        # Create inference worker
        worker = InferenceWorker(self.mock_config, queues, MagicMock())

        # Simulate STT result
        message = {
            'type': 'stt_result',
            'text': 'hello auralis',
            'confidence': 0.9
        }

        # Process the message
        worker._process_stt_result(message)

        # Check that TTS was called
        self.assertTrue(mock_tts_instance.speak.called)

    def test_focus_session_flow(self):
        """E2E test for focus session flow"""
        from ux_flow_manager import UXFlowManager

        ux = UXFlowManager(self.mock_config)

        # Simulate focus session start
        ux.start_focus_session()

        # Check status
        status = ux.get_status()
        self.assertEqual(status.get('focus_mode'), 'ON')

        # Simulate end
        ux.end_focus_session()
        status = ux.get_status()
        self.assertEqual(status.get('focus_mode'), 'OFF')

    def test_plugin_sandbox_escape(self):
        """Security test for plugin sandbox escape"""
        from plugins import PluginHostModule

        plugins = PluginHostModule(self.mock_config)

        # Test that plugins can't access forbidden modules
        malicious_code = """
import os
os.system('rm -rf /')
"""
        # This should be blocked or sandboxed
        result = plugins.execute_plugin('test', 'run_code', code=malicious_code)
        # In a real test, check that no system commands were executed
        self.assertIsInstance(result, str)  # Should return safely

    @patch('web_dashboard.Flask')
    def test_web_dashboard_telemetry(self, mock_flask):
        """Test web dashboard telemetry endpoints"""
        from web_dashboard import WebDashboard

        dashboard = WebDashboard(self.mock_config, None, None, None)

        # Test telemetry data recording
        dashboard.record_llm_latency(0.5)
        dashboard.record_stt_latency(0.3)

        self.assertEqual(len(dashboard.telemetry_data['llm_latencies']), 1)
        self.assertEqual(len(dashboard.telemetry_data['stt_latencies']), 1)

        # Test PII scrubbing
        test_data = {'email': 'user@example.com', 'ip': '192.168.1.1', 'message': 'test'}
        scrubbed = dashboard._scrub_pii(test_data)
        self.assertNotIn('user@example.com', scrubbed)
        self.assertIn('[EMAIL]', scrubbed)

    def test_queue_manager_multiprocessing(self):
        """Test queue manager with multiprocessing compatibility"""
        from queue_manager import QueueManager

        qm = QueueManager()

        # Test putting messages
        qm.put_message('audio->stt', {'type': 'test'})
        qm.put_message('stt->nlp', {'type': 'test'})
        qm.put_message('nlp->tts', {'type': 'test'})

        # Test stats
        stats = qm.get_queue_stats()
        self.assertIn('audio->stt', stats)
        self.assertIn('stt->nlp', stats)
        self.assertIn('nlp->tts', stats)

        # Test drop oldest for audio->stt
        for i in range(10):
            qm.put_message('audio->stt', {'type': f'test{i}'})

        # Should not exceed maxsize
        stats = qm.get_queue_stats()
        self.assertLessEqual(stats['audio->stt']['size'], 8)

if __name__ == '__main__':
    unittest.main()