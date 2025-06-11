from http import HTTPMethod as Method

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.exceptions import catch_all_exception_handler, internal_server_error_handler
from app.routes.health import router as health_router
from app.routes.urls import router as urls_router


def create_test_app() -> FastAPI:
    """Create a test app instance without rate limiting middleware"""
    app = FastAPI(
        title="URL Shortener Service - Test",
        description="Test API for shortening URLs",
        version="0.1.0",
    )

    # Register routers
    app.include_router(urls_router, prefix="/api/v1", tags=["urls"])
    app.include_router(health_router, tags=["health"])

    # Add CORS middleware (but not rate limiting)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=[
            Method.GET,
            Method.POST,
            Method.DELETE,
            Method.HEAD,
        ],
        allow_headers=["*"],
    )

    # Register exception handlers
    app.add_exception_handler(500, internal_server_error_handler)
    app.add_exception_handler(Exception, catch_all_exception_handler)

    return app


@pytest.fixture
def client():
    return TestClient(create_test_app())


def test_should_create_short_url_when_valid_url_posted(client):
    response = client.post("/api/v1/", json={"url": "https://www.example.com"})

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    url_data = data["data"]
    assert "short_link" in url_data
    assert "link" in url_data
    assert "created_at" in url_data
    assert len(url_data["short_link"]) == 8


def test_should_reject_invalid_url_when_posted(client):
    response = client.post("/api/v1/", json={"url": "not-a-valid-url"})

    assert response.status_code == 422


def test_should_redirect_when_valid_short_code_requested(client):
    create_response = client.post("/api/v1/", json={"url": "https://www.example.com"})
    short_link = create_response.json()["data"]["short_link"]

    response = client.get(f"/api/v1/{short_link}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "https://www.example.com" in str(data["data"]["link"])


def test_should_return_404_when_short_code_not_found(client):
    response = client.get("/api/v1/missing1")

    assert response.status_code == 404


def test_should_return_health_check_when_requested(client):
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_should_list_all_urls_when_requested(client):
    client.post("/api/v1/", json={"url": "https://www.example.com"})
    client.post("/api/v1/", json={"url": "https://www.github.com"})

    response = client.get("/api/v1/")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 2


def test_should_delete_url_when_valid_short_code_provided(client):
    create_response = client.post("/api/v1/", json={"url": "https://www.example.com"})
    short_link = create_response.json()["data"]["short_link"]

    delete_response = client.delete(f"/api/v1/{short_link}")
    assert delete_response.status_code == 200

    get_response = client.get(f"/api/v1/{short_link}")
    assert get_response.status_code == 404


def test_should_handle_malformed_json_gracefully(client):
    response = client.post("/api/v1/", content="invalid json")

    assert response.status_code == 422


def test_should_handle_missing_link_field_gracefully(client):
    response = client.post("/api/v1/", json={})

    assert response.status_code == 422


def test_should_handle_empty_link_field_gracefully(client):
    response = client.post("/api/v1/", json={"url": ""})

    assert response.status_code == 422


def test_should_preserve_query_parameters_in_redirect(client):
    original_url = "https://www.example.com/path?param=value&other=test"
    create_response = client.post("/api/v1/", json={"url": original_url})
    short_link = create_response.json()["data"]["short_link"]

    response = client.get(f"/api/v1/{short_link}")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert original_url in str(data["data"]["link"])


def test_should_handle_multiple_identical_urls(client):
    url = "https://www.example.com"

    response1 = client.post("/api/v1/", json={"url": url})
    response2 = client.post("/api/v1/", json={"url": url})

    assert response1.status_code == 201
    assert response2.status_code == 201

    data1 = response1.json()
    data2 = response2.json()

    # Both responses should return the same short link for the same URL
    assert data1["data"]["short_link"] == data2["data"]["short_link"]
    assert str(data1["data"]["link"]) == str(data2["data"]["link"])
