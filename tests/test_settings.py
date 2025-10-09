import pytest
import json
import os

try:
    from modules.settings import Settings
    HAS_SETTINGS = True
except ImportError:
    HAS_SETTINGS = False

@pytest.mark.skipif(not HAS_SETTINGS, reason="Settings module dependencies not available")
def test_settings_get():
    # Create a temp config
    config_data = {"app_name": "Test", "version": "1.0"}
    with open('test_config.json', 'w') as f:
        json.dump(config_data, f)
    settings = Settings(config_file='test_config.json')
    assert settings.get('app_name') == "Test"
    assert settings.get('missing', 'default') == 'default'
    os.remove('test_config.json')