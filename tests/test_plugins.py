import pytest

try:
    from modules.plugins import PluginModule
    HAS_PLUGINS = True
except ImportError:
    HAS_PLUGINS = False

@pytest.mark.skipif(not HAS_PLUGINS, reason="Plugins module dependencies not available")
def test_plugins_load_and_execute():
    plugins = PluginModule()
    plugins.load_plugins()
    # Assuming calculator plugin exists
    result = plugins.execute('calculator', '2', '+', '3')
    assert '5' in result or 'Result: 5' in result