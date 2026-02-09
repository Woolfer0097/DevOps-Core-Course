"""
Unit tests for the DevOps Info Service FastAPI application.

Tests cover all endpoints, response structures, error cases, and edge cases.
"""

import platform
import socket
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app import app, get_runtime_info, get_system_info


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestMainEndpoint:
    """Tests for the main endpoint (/)."""

    def test_main_endpoint_returns_200(self, client):
        """Test that the main endpoint returns HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_main_endpoint_returns_json(self, client):
        """Test that the main endpoint returns JSON content."""
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_main_endpoint_has_required_fields(self, client):
        """Test that the response contains all required top-level fields."""
        response = client.get("/")
        data = response.json()

        required_fields = ["service", "system", "runtime", "request", "endpoints"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_service_info_structure(self, client):
        """Test that service info contains correct fields and values."""
        response = client.get("/")
        service = response.json()["service"]

        assert service["name"] == "devops-info-service"
        assert service["version"] == "1.0.0"
        assert service["description"] == "DevOps course info service"
        assert service["framework"] == "FastAPI"

    def test_system_info_structure(self, client):
        """Test that system info contains expected fields."""
        response = client.get("/")
        system = response.json()["system"]

        required_fields = [
            "hostname",
            "platform",
            "platform_version",
            "architecture",
            "cpu_count",
            "python_version",
        ]
        for field in required_fields:
            assert field in system, f"Missing system field: {field}"

        # Verify types
        assert isinstance(system["hostname"], str)
        assert isinstance(system["platform"], str)
        assert isinstance(system["cpu_count"], int | type(None))

    def test_runtime_info_structure(self, client):
        """Test that runtime info contains expected fields."""
        response = client.get("/")
        runtime = response.json()["runtime"]

        required_fields = [
            "uptime_seconds",
            "uptime_human",
            "current_time",
            "timezone",
        ]
        for field in required_fields:
            assert field in runtime, f"Missing runtime field: {field}"

        # Verify types
        assert isinstance(runtime["uptime_seconds"], int)
        assert runtime["uptime_seconds"] >= 0
        assert isinstance(runtime["uptime_human"], str)
        assert runtime["timezone"] == "UTC"

        # Verify timestamp format (ISO 8601)
        datetime.fromisoformat(runtime["current_time"])

    def test_request_info_structure(self, client):
        """Test that request info captures request details."""
        response = client.get("/")
        request_info = response.json()["request"]

        required_fields = ["client_ip", "user_agent", "method", "path"]
        for field in required_fields:
            assert field in request_info, f"Missing request field: {field}"

        assert request_info["method"] == "GET"
        assert request_info["path"] == "/"

    def test_endpoints_list_structure(self, client):
        """Test that endpoints list contains correct information."""
        response = client.get("/")
        endpoints = response.json()["endpoints"]

        assert isinstance(endpoints, list)
        assert len(endpoints) == 2

        # Check that each endpoint has required fields
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "method" in endpoint
            assert "description" in endpoint

    def test_custom_user_agent_captured(self, client):
        """Test that custom User-Agent headers are captured."""
        custom_ua = "TestBot/1.0"
        response = client.get("/", headers={"User-Agent": custom_ua})
        request_info = response.json()["request"]

        assert request_info["user_agent"] == custom_ua


class TestHealthEndpoint:
    """Tests for the health check endpoint (/health)."""

    def test_health_endpoint_returns_200(self, client):
        """Test that the health endpoint returns HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that the health endpoint returns JSON content."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_structure(self, client):
        """Test that health response contains required fields."""
        response = client.get("/health")
        data = response.json()

        required_fields = ["status", "timestamp", "uptime_seconds"]
        for field in required_fields:
            assert field in data, f"Missing health field: {field}"

    def test_health_status_value(self, client):
        """Test that health status is 'healthy'."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"

    def test_health_timestamp_format(self, client):
        """Test that timestamp is in valid ISO 8601 format."""
        response = client.get("/health")
        data = response.json()

        # Should not raise an exception
        datetime.fromisoformat(data["timestamp"])

    def test_health_uptime_is_positive(self, client):
        """Test that uptime is a non-negative integer."""
        response = client.get("/health")
        data = response.json()

        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_404_on_invalid_endpoint(self, client):
        """Test that invalid endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_404_error_structure(self, client):
        """Test that 404 errors return proper error structure."""
        response = client.get("/invalid")
        data = response.json()

        assert "error" in data
        assert "message" in data
        assert data["error"] == "Not Found"

    def test_405_on_wrong_method(self, client):
        """Test that wrong HTTP methods return 405."""
        response = client.post("/")
        assert response.status_code == 405

    def test_405_error_structure(self, client):
        """Test that 405 errors return proper error structure."""
        response = client.post("/")
        data = response.json()

        assert "error" in data
        assert "message" in data


class TestHelperFunctions:
    """Tests for internal helper functions."""

    def test_get_system_info_returns_dict(self):
        """Test that get_system_info returns a dictionary."""
        info = get_system_info()
        assert isinstance(info, dict)

    def test_get_system_info_has_hostname(self):
        """Test that system info includes hostname."""
        info = get_system_info()
        assert "hostname" in info
        assert info["hostname"] == socket.gethostname()

    def test_get_system_info_has_platform(self):
        """Test that system info includes platform."""
        info = get_system_info()
        assert "platform" in info
        assert info["platform"] == platform.system()

    def test_get_runtime_info_returns_dict(self):
        """Test that get_runtime_info returns a dictionary."""
        info = get_runtime_info()
        assert isinstance(info, dict)

    def test_get_runtime_info_has_uptime(self):
        """Test that runtime info includes uptime."""
        info = get_runtime_info()
        assert "uptime_seconds" in info
        assert isinstance(info["uptime_seconds"], int)

    def test_get_runtime_info_uptime_increases(self):
        """Test that uptime increases over time."""
        import time

        info1 = get_runtime_info()
        time.sleep(1)
        info2 = get_runtime_info()

        assert info2["uptime_seconds"] >= info1["uptime_seconds"]


class TestResponseConsistency:
    """Tests for response consistency across multiple requests."""

    def test_multiple_health_checks_succeed(self, client):
        """Test that multiple health checks all succeed."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"

    def test_service_info_consistent(self, client):
        """Test that service info remains consistent."""
        response1 = client.get("/")
        response2 = client.get("/")

        service1 = response1.json()["service"]
        service2 = response2.json()["service"]

        assert service1 == service2

    def test_system_info_consistent(self, client):
        """Test that system info remains consistent."""
        response1 = client.get("/")
        response2 = client.get("/")

        system1 = response1.json()["system"]
        system2 = response2.json()["system"]

        # System info should be identical across requests
        assert system1 == system2
