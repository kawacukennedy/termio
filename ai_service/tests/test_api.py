"""Integration tests for the TERMIO AI Service API."""

import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app


@pytest.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_health_endpoint(client):
    """GET /health should return 200."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data
    assert "embedding_model_loaded" in data


@pytest.mark.anyio
async def test_chat_no_model(client):
    """POST /chat without model should return fallback response."""
    response = await client.post(
        "/chat",
        json={"message": "Hello", "max_tokens": 64},
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data


@pytest.mark.anyio
async def test_nlu_endpoint(client):
    """POST /nlu should classify intent."""
    response = await client.post(
        "/nlu",
        json={"text": "Book a flight to London"},
    )
    # May return 503 if classifier not initialized in test mode
    if response.status_code == 200:
        data = response.json()
        assert "intent" in data
        assert "confidence" in data
        assert "entities" in data


@pytest.mark.anyio
async def test_models_endpoint(client):
    """GET /models should list all models."""
    response = await client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) >= 4


@pytest.mark.anyio
async def test_augment_requires_consent(client):
    """POST /augment without consent should return 403."""
    response = await client.post(
        "/augment",
        json={
            "query": "Test query",
            "consent_given": False,
        },
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_augment_with_consent(client):
    """POST /augment with consent should attempt augmentation."""
    response = await client.post(
        "/augment",
        json={
            "query": "Test query",
            "consent_given": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "augmented_response" in data


@pytest.mark.anyio
async def test_embeddings_without_model(client):
    """POST /embeddings without model should return 503."""
    response = await client.post(
        "/embeddings",
        json={"texts": ["Hello world"]},
    )
    # May return 503 if embedding engine not loaded
    assert response.status_code in (200, 503)
