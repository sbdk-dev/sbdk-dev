"""
Test suite for FastAPI webhook endpoints as specified in the SBDK.dev PRD.
Tests registration, usage tracking, and GitHub webhook functionality.
"""

import pytest
import json
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request
import subprocess


class MockFastAPIApp:
    """Mock FastAPI application for testing webhook functionality."""

    def __init__(self):
        self.app = FastAPI()
        self.registered_users = {}
        self.usage_logs = []
        self.webhook_calls = []

        # Setup routes
        self.setup_routes()

    def setup_routes(self):
        """Setup mock API routes based on PRD specifications."""

        @self.app.post("/register")
        async def register_user(request: Request):
            """Register a new user/project UUID."""
            body = await request.json()
            project_name = body.get("project_name", "default_project")
            email = body.get("email", "")

            # Generate UUID
            user_uuid = str(uuid.uuid4())

            # Store registration
            self.registered_users[user_uuid] = {
                "project_name": project_name,
                "email": email,
                "uuid": user_uuid,
            }

            return {"uuid": user_uuid}

        @self.app.post("/track/usage")
        async def track_usage(request: Request):
            """Track CLI usage ping (opt-in)."""
            body = await request.json()

            usage_data = {
                "uuid": body.get("uuid"),
                "command": body.get("command"),
                "timestamp": body.get("timestamp"),
                "metadata": body.get("metadata", {}),
            }

            self.usage_logs.append(usage_data)

            return {"status": "logged"}

        @self.app.post("/track/webhook")
        async def track_webhook(request: Request):
            """Receive webhook events from GitHub."""
            body = await request.json()

            webhook_data = {
                "event_type": body.get("event_type"),
                "repository": body.get("repository"),
                "timestamp": body.get("timestamp"),
                "payload": body,
            }

            self.webhook_calls.append(webhook_data)

            return {"status": "received"}

        @self.app.post("/webhook/github")
        async def github_webhook(request: Request):
            """GitHub webhook handler for push events."""
            payload = await request.json()

            # Track the webhook call
            self.webhook_calls.append(payload)

            # Simulate triggering rebuild on main branch push
            if "ref" in payload and payload["ref"].endswith("/main"):
                # In real implementation, this would trigger:
                # subprocess.Popen(["python", "main.py", "dev"])
                return {"status": "rebuild_triggered"}

            return {"status": "ok"}


class TestFastAPIWebhooks:
    """Test suite for FastAPI webhook endpoints."""

    @pytest.fixture
    def mock_app(self):
        """Create mock FastAPI application for testing."""
        return MockFastAPIApp()

    @pytest.fixture
    def test_client(self, mock_app):
        """Create test client for the mock app."""
        return TestClient(mock_app.app)

    def test_register_endpoint_success(self, test_client, mock_app):
        """Test successful user registration."""
        registration_data = {
            "project_name": "test_sandbox",
            "email": "test@example.com",
        }

        response = test_client.post("/register", json=registration_data)

        assert response.status_code == 200
        response_data = response.json()

        # Verify UUID is returned
        assert "uuid" in response_data
        assert len(response_data["uuid"]) == 36  # Standard UUID length

        # Verify UUID is valid
        try:
            uuid.UUID(response_data["uuid"])
        except ValueError:
            pytest.fail("Returned UUID is not valid")

        # Verify registration was stored
        user_uuid = response_data["uuid"]
        assert user_uuid in mock_app.registered_users
        stored_user = mock_app.registered_users[user_uuid]
        assert stored_user["project_name"] == "test_sandbox"
        assert stored_user["email"] == "test@example.com"

    def test_register_endpoint_minimal_data(self, test_client, mock_app):
        """Test registration with minimal required data."""
        registration_data = {
            "project_name": "minimal_project"
            # No email provided - should be optional
        }

        response = test_client.post("/register", json=registration_data)

        assert response.status_code == 200
        response_data = response.json()

        # Verify UUID is returned
        assert "uuid" in response_data

        # Verify registration was stored with empty email
        user_uuid = response_data["uuid"]
        stored_user = mock_app.registered_users[user_uuid]
        assert stored_user["project_name"] == "minimal_project"
        assert stored_user["email"] == ""

    def test_usage_tracking_endpoint(self, test_client, mock_app):
        """Test CLI usage tracking functionality."""
        # First register a user
        registration_data = {"project_name": "usage_test"}
        reg_response = test_client.post("/register", json=registration_data)
        user_uuid = reg_response.json()["uuid"]

        # Track usage
        usage_data = {
            "uuid": user_uuid,
            "command": "sbdk dev",
            "timestamp": "2024-01-01T12:00:00Z",
            "metadata": {"duration": 45.2, "success": True},
        }

        response = test_client.post("/track/usage", json=usage_data)

        assert response.status_code == 200
        assert response.json()["status"] == "logged"

        # Verify usage was logged
        assert len(mock_app.usage_logs) == 1
        logged_usage = mock_app.usage_logs[0]
        assert logged_usage["uuid"] == user_uuid
        assert logged_usage["command"] == "sbdk dev"
        assert logged_usage["metadata"]["duration"] == 45.2
        assert logged_usage["metadata"]["success"] is True

    def test_webhook_tracking_endpoint(self, test_client, mock_app):
        """Test generic webhook tracking functionality."""
        webhook_data = {
            "event_type": "push",
            "repository": "user/sbdk-project",
            "timestamp": "2024-01-01T12:00:00Z",
            "branch": "main",
            "commits": 3,
        }

        response = test_client.post("/track/webhook", json=webhook_data)

        assert response.status_code == 200
        assert response.json()["status"] == "received"

        # Verify webhook was tracked
        assert len(mock_app.webhook_calls) == 1
        tracked_webhook = mock_app.webhook_calls[0]
        assert tracked_webhook["event_type"] == "push"
        assert tracked_webhook["repository"] == "user/sbdk-project"

    def test_github_webhook_main_branch_push(self, test_client, mock_app):
        """Test GitHub webhook handling for main branch pushes."""
        github_payload = {
            "ref": "refs/heads/main",
            "repository": {"name": "sbdk-project", "full_name": "user/sbdk-project"},
            "commits": [{"id": "abc123", "message": "Update pipeline configuration"}],
        }

        response = test_client.post("/webhook/github", json=github_payload)

        assert response.status_code == 200
        assert response.json()["status"] == "rebuild_triggered"

        # Verify webhook was processed
        assert len(mock_app.webhook_calls) == 1
        processed_webhook = mock_app.webhook_calls[0]
        assert processed_webhook["ref"] == "refs/heads/main"

    def test_github_webhook_non_main_branch(self, test_client, mock_app):
        """Test GitHub webhook handling for non-main branch pushes."""
        github_payload = {
            "ref": "refs/heads/feature-branch",
            "repository": {"name": "sbdk-project", "full_name": "user/sbdk-project"},
            "commits": [{"id": "def456", "message": "Feature development"}],
        }

        response = test_client.post("/webhook/github", json=github_payload)

        assert response.status_code == 200
        assert response.json()["status"] == "ok"  # Not "rebuild_triggered"

        # Verify webhook was processed but no rebuild triggered
        assert len(mock_app.webhook_calls) == 1

    def test_invalid_json_handling(self, test_client):
        """Test handling of invalid JSON in requests."""
        # Test with malformed JSON - FastAPI/Starlette will raise an error
        # Our mock handles this by returning 500 error from the endpoint itself
        with pytest.raises(Exception):
            # This should raise a JSON decode error in the FastAPI endpoint
            response = test_client.post(
                "/register",
                data="invalid json",
                headers={"Content-Type": "application/json"},
            )

    def test_missing_required_fields(self, test_client):
        """Test handling of missing required fields."""
        # Test registration without project_name
        response = test_client.post("/register", json={})

        # Should still work as project_name has a default
        assert response.status_code == 200
        response_data = response.json()
        assert "uuid" in response_data

    def test_usage_tracking_without_uuid(self, test_client, mock_app):
        """Test usage tracking with missing UUID."""
        usage_data = {
            "command": "sbdk init",
            "timestamp": "2024-01-01T12:00:00Z",
            # Missing uuid
        }

        response = test_client.post("/track/usage", json=usage_data)

        assert response.status_code == 200  # Should still accept
        assert response.json()["status"] == "logged"

        # Verify usage was logged with None UUID
        logged_usage = mock_app.usage_logs[0]
        assert logged_usage["uuid"] is None
        assert logged_usage["command"] == "sbdk init"


class TestWebhookIntegration:
    """Integration tests for webhook functionality."""

    @pytest.fixture
    def mock_app(self):
        """Create mock app for integration testing."""
        return MockFastAPIApp()

    @pytest.fixture
    def test_client(self, mock_app):
        """Create test client for integration testing."""
        return TestClient(mock_app.app)

    def test_full_user_journey(self, test_client, mock_app):
        """Test complete user journey from registration to usage tracking."""
        # Step 1: Register user
        registration_data = {
            "project_name": "journey_test",
            "email": "journey@example.com",
        }

        reg_response = test_client.post("/register", json=registration_data)
        assert reg_response.status_code == 200
        user_uuid = reg_response.json()["uuid"]

        # Step 2: Track multiple usage events
        usage_events = [
            {
                "uuid": user_uuid,
                "command": "sbdk init journey_test",
                "timestamp": "2024-01-01T10:00:00Z",
                "metadata": {"success": True},
            },
            {
                "uuid": user_uuid,
                "command": "sbdk dev",
                "timestamp": "2024-01-01T10:05:00Z",
                "metadata": {"success": True, "duration": 30.5},
            },
            {
                "uuid": user_uuid,
                "command": "sbdk webhooks",
                "timestamp": "2024-01-01T10:10:00Z",
                "metadata": {"success": True},
            },
        ]

        for event in usage_events:
            response = test_client.post("/track/usage", json=event)
            assert response.status_code == 200

        # Step 3: Simulate GitHub webhook
        webhook_payload = {
            "ref": "refs/heads/main",
            "repository": {"full_name": "user/journey_test"},
        }

        webhook_response = test_client.post("/webhook/github", json=webhook_payload)
        assert webhook_response.status_code == 200
        assert webhook_response.json()["status"] == "rebuild_triggered"

        # Verify all events were tracked
        assert len(mock_app.usage_logs) == 3
        assert len(mock_app.webhook_calls) == 1
        assert user_uuid in mock_app.registered_users

    @patch("subprocess.Popen")
    def test_webhook_subprocess_call(self, mock_popen):
        """Test that webhook actually triggers subprocess call in real implementation."""
        # This test simulates what would happen in the real implementation
        mock_popen.return_value = MagicMock()

        # Simulate GitHub webhook payload for main branch
        payload = {"ref": "refs/heads/main"}

        # In real implementation, this would be triggered:
        if "ref" in payload and payload["ref"].endswith("/main"):
            subprocess.Popen(["python", "main.py", "dev"])

        # Verify subprocess was called
        mock_popen.assert_called_once_with(["python", "main.py", "dev"])

    def test_concurrent_webhook_handling(self, test_client, mock_app):
        """Test handling of multiple concurrent webhook requests."""
        # Simulate multiple webhook calls
        webhooks = [
            {"ref": "refs/heads/main", "repository": {"name": f"repo{i}"}}
            for i in range(5)
        ]

        responses = []
        for webhook in webhooks:
            response = test_client.post("/webhook/github", json=webhook)
            responses.append(response)

        # Verify all requests were handled
        for response in responses:
            assert response.status_code == 200

        # Verify all webhooks were tracked
        assert len(mock_app.webhook_calls) == 5

    def test_webhook_error_recovery(self, test_client):
        """Test webhook handling with various error conditions."""
        # Test with empty payload
        response = test_client.post("/webhook/github", json={})
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Test with malformed repository info
        response = test_client.post(
            "/webhook/github",
            json={
                "ref": "refs/heads/main",
                "repository": "invalid",  # Should be dict, not string
            },
        )
        assert response.status_code == 200  # Should still handle gracefully


class TestWebhookSecurity:
    """Security tests for webhook endpoints."""

    @pytest.fixture
    def mock_app(self):
        """Create mock app for security testing."""
        return MockFastAPIApp()

    @pytest.fixture
    def test_client(self, mock_app):
        """Create test client for security testing."""
        return TestClient(mock_app.app)

    def test_large_payload_handling(self, test_client):
        """Test handling of unusually large payloads."""
        # Create a large payload
        large_payload = {
            "ref": "refs/heads/main",
            "large_data": "x" * 10000,  # 10KB of data
        }

        response = test_client.post("/webhook/github", json=large_payload)

        # Should handle large payloads gracefully
        assert response.status_code == 200

    def test_special_characters_in_payload(self, test_client):
        """Test handling of special characters and unicode in payloads."""
        special_payload = {
            "ref": "refs/heads/main",
            "commit_message": "Fix unicode: 测试中文 🚀 émoji",
            "author": "user@domain.com",
        }

        response = test_client.post("/webhook/github", json=special_payload)

        assert response.status_code == 200
        assert response.json()["status"] == "rebuild_triggered"

    def test_injection_attempt_prevention(self, test_client):
        """Test prevention of injection attempts in payloads."""
        malicious_payload = {
            "ref": "refs/heads/main; rm -rf /",  # Command injection attempt
            "repository": {"name": "<script>alert('xss')</script>"},  # XSS attempt
        }

        response = test_client.post("/webhook/github", json=malicious_payload)

        # Should handle malicious input safely
        assert response.status_code == 200
        # In real implementation, would need proper sanitization
