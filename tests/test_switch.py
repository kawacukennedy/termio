import pytest

try:
    from modules.offline_online_switch import OfflineOnlineSwitchModule
    HAS_SWITCH = True
except ImportError:
    HAS_SWITCH = False

@pytest.mark.skipif(not HAS_SWITCH, reason="Switch module dependencies not available")
def test_switch_modes():
    import os
    switch = OfflineOnlineSwitchModule()
    assert switch.get_mode() == 'offline'
    # Mock API key
    os.environ['OPENAI_API_KEY'] = 'test_key'
    switch.switch_to_online()
    assert switch.get_mode() == 'online'
    switch.switch_to_offline()
    assert switch.get_mode() == 'offline'
    # Clean up
    del os.environ['OPENAI_API_KEY']