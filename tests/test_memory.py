import pytest

try:
    from modules.memory import ConversationMemory
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False

@pytest.mark.skipif(not HAS_MEMORY, reason="Memory module dependencies not available")
def test_memory_add_and_get():
    memory = ConversationMemory(max_turns=3, enable_long_term=False)
    memory.add_interaction("Hello", "Hi there")
    memory.add_interaction("How are you?", "I'm fine")
    context = memory.get_context()
    assert len(context) == 2
    assert context[0]['user'] == "Hello"
    assert context[1]['response'] == "I'm fine"

@pytest.mark.skipif(not HAS_MEMORY, reason="Memory module dependencies not available")
def test_memory_max_turns():
    memory = ConversationMemory(max_turns=2, enable_long_term=False)
    memory.add_interaction("1", "1")
    memory.add_interaction("2", "2")
    memory.add_interaction("3", "3")
    context = memory.get_context()
    assert len(context) == 2
    assert context[0]['user'] == "2"