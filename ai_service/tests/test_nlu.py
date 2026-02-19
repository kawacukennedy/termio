"""Tests for NLU intent classification."""

import asyncio
import pytest

from src.nlu import IntentClassifier, IntentType, extract_entities


@pytest.fixture
def classifier():
    """Create a classifier instance without ML model."""
    return IntentClassifier()


def test_conversation_intent(classifier):
    """General conversation should classify as CONVERSATION."""
    result = asyncio.run(classifier.classify("Hello, how are you doing today?"))
    assert result.intent == IntentType.CONVERSATION


def test_action_request_intent(classifier):
    """Action keywords should classify as ACTION_REQUEST."""
    result = asyncio.run(classifier.classify("Please book a meeting for tomorrow"))
    assert result.intent == IntentType.ACTION_REQUEST
    assert result.confidence > 0


def test_memory_query_intent(classifier):
    """Memory-related queries should classify as MEMORY_QUERY."""
    result = asyncio.run(classifier.classify("Do you remember what I said yesterday?"))
    assert result.intent == IntentType.MEMORY_QUERY


def test_health_query_intent(classifier):
    """Health-related queries should classify as HEALTH_QUERY."""
    result = asyncio.run(classifier.classify("What was my heart rate this morning?"))
    assert result.intent == IntentType.HEALTH_QUERY


def test_device_control_intent(classifier):
    """Device control commands should classify correctly."""
    result = asyncio.run(classifier.classify("Turn off the living room lights"))
    assert result.intent == IntentType.DEVICE_CONTROL


def test_entity_extraction_time():
    """Time entities should be extracted."""
    entities = extract_entities("Meeting at 3:30 pm")
    time_entities = [e for e in entities if e.entity_type == "time"]
    assert len(time_entities) >= 1


def test_entity_extraction_email():
    """Email entities should be extracted."""
    entities = extract_entities("Send to user@example.com")
    email_entities = [e for e in entities if e.entity_type == "email"]
    assert len(email_entities) == 1
    assert email_entities[0].value == "user@example.com"


def test_entity_extraction_number():
    """Number entities should be extracted."""
    entities = extract_entities("I ran 5.2 miles today")
    number_entities = [e for e in entities if e.entity_type == "number"]
    assert len(number_entities) >= 1


def test_classifier_returns_nlu_result(classifier):
    """Classifier should return complete NluResult."""
    result = asyncio.run(classifier.classify("Schedule a call"))
    assert result.raw_text == "Schedule a call"
    assert isinstance(result.entities, list)
    assert 0 <= result.confidence <= 1


def test_classifier_ml_not_loaded(classifier):
    """Classifier should report ML model not loaded."""
    assert not classifier.is_ml_loaded
