import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.anyio
async def test_health_check():
    """Test health endpoint returns ok"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data


@pytest.mark.anyio
async def test_roi_endpoint_returns_json():
    """Test ROI endpoint returns valid JSON structure"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/api/roi")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data


@pytest.mark.anyio
async def test_roi_endpoint_with_session_filter():
    """Test ROI endpoint accepts session_id filter"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/api/roi?session_id=test-session-123")
        assert response.status_code == 200


@pytest.mark.anyio
async def test_roi_endpoint_with_limit():
    """Test ROI endpoint accepts limit parameter"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/api/roi?limit=10")
        assert response.status_code == 200


@pytest.mark.anyio
async def test_docs_available():
    """Test that API docs are accessible"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/docs")
        assert response.status_code == 200