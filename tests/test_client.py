"""Tests for CodeiumClient."""

import json
from subprocess import CalledProcessError
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests
from requests.exceptions import ConnectionError, Timeout

from nitrodump.client import CodeiumClient, CodeiumServerError
from nitrodump.models import GetUserStatusResponse


@pytest.fixture
def mock_process_output():
    """Mock process output for pgrep and ps commands."""
    return {
        "pid": "12345",
        "command_line": (
            "/path/to/language_server_macos_arm --enable_lsp --csrf_token "
            "test-token-123 --random_port"
        ),
    }


@pytest.fixture
def mock_lsof_output():
    """Mock lsof output for finding the server port."""
    return "language_  12345 user   23u  IPv4 0x123  TCP 127.0.0.1:61958 (LISTEN)"


@pytest.fixture
def sample_api_response():
    """Sample API response data."""
    return {
        "userStatus": {
            "name": "Test User",
            "email": "test@example.com",
            "planStatus": {
                "planInfo": {
                    "teamsTier": "TEAMS_TIER_PRO",
                    "planName": "Pro",
                    "monthlyPromptCredits": 50000,
                    "monthlyFlowCredits": 150000,
                }
            },
            "userTier": {
                "id": "g1-pro-tier",
                "name": "Google AI Pro",
                "description": "Google AI Pro",
            },
            "availablePromptCredits": 500,
            "availableFlowCredits": 100,
            "cascadeModelConfigData": {
                "clientModelConfigs": [
                    {
                        "label": "Claude Sonnet 4.5",
                        "modelOrAlias": {"model": "MODEL_CLAUDE_4_5_SONNET"},
                        "supportsImages": True,
                        "isRecommended": True,
                        "quotaInfo": {
                            "remainingFraction": 1.0,
                            "resetTime": "2026-02-19T12:00:00Z",
                        },
                    }
                ]
            },
        },
    }


def _make_mock_result(stdout: str, returncode: int = 0):
    """Create a mock CompletedProcess-like object."""
    result = MagicMock()
    result.stdout = stdout
    result.returncode = returncode
    return result


class TestCodeiumClient:
    """Test suite for CodeiumClient."""

    def test_find_server_process_success(self, mock_process_output):
        """Test successfully finding the server process."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(mock_process_output["pid"])
            client = CodeiumClient()
            assert client.pid == 12345

    def test_find_server_process_not_running(self):
        """Test when server process is not running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result("", returncode=1)
            client = CodeiumClient()
            assert client.pid is None

    def test_extract_csrf_token_success(self, mock_process_output):
        """Test successfully extracting CSRF token."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(mock_process_output["command_line"])
            client = CodeiumClient()
            token = client._extract_csrf_token(12345)
            assert token == "test-token-123"

    def test_extract_csrf_token_not_found(self):
        """Test when CSRF token is not in command line."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(
                "/path/to/language_server_macos_arm --enable_lsp"
            )
            client = CodeiumClient()
            token = client._extract_csrf_token(12345)
            assert token is None

    def test_find_server_port_success(self, mock_lsof_output):
        """Test successfully finding server port."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result(mock_lsof_output)
            client = CodeiumClient()
            port = client._find_server_port(12345)
            assert port == 61958

    def test_find_server_port_not_found(self):
        """Test when server port cannot be found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result("", returncode=1)
            client = CodeiumClient()
            port = client._find_server_port(12345)
            assert port is None

    def test_get_user_status_success(self, sample_api_response):
        """Test successful API call."""
        with patch("subprocess.run") as mock_run:
            # Mock subprocess calls
            mock_run.side_effect = [
                _make_mock_result("12345"),  # pgrep
                _make_mock_result("--csrf_token test-token"),  # ps
                _make_mock_result(
                    "language_ 12345 user   23u  IPv4 TCP 127.0.0.1:61958 (LISTEN)"
                ),  # lsof
            ]

            with patch("requests.post") as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = sample_api_response
                mock_response.raise_for_status = Mock()
                mock_post.return_value = mock_response

                client = CodeiumClient()
                status = client.get_user_status()

                assert isinstance(status, GetUserStatusResponse)
                assert status.user_status.name == "Test User"
                assert status.user_status.email == "test@example.com"

    def test_get_user_status_server_not_running(self):
        """Test error when server is not running."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = _make_mock_result("", returncode=1)
            client = CodeiumClient()

            with pytest.raises(CodeiumServerError) as exc_info:
                client.get_user_status()

            assert "not running" in str(exc_info.value).lower()

    def test_get_user_status_connection_error(self):
        """Test handling of connection errors."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                _make_mock_result("12345"),
                _make_mock_result("--csrf_token test-token"),
                _make_mock_result("language_ 12345 TCP 127.0.0.1:61958 (LISTEN)"),
            ]

            with patch("requests.post") as mock_post:
                mock_post.side_effect = ConnectionError("Connection refused")
                client = CodeiumClient()

                with pytest.raises(CodeiumServerError) as exc_info:
                    client.get_user_status()

                assert "failed to contact server" in str(exc_info.value).lower()

    def test_get_user_status_timeout(self):
        """Test handling of request timeouts."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                _make_mock_result("12345"),
                _make_mock_result("--csrf_token test-token"),
                _make_mock_result("language_ 12345 TCP 127.0.0.1:61958 (LISTEN)"),
            ]

            with patch("requests.post") as mock_post:
                mock_post.side_effect = Timeout("Request timed out")
                client = CodeiumClient()

                with pytest.raises(CodeiumServerError) as exc_info:
                    client.get_user_status()

                assert "failed to contact server" in str(exc_info.value).lower()

    def test_get_user_status_invalid_json(self):
        """Test handling of invalid JSON response."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                _make_mock_result("12345"),
                _make_mock_result("--csrf_token test-token"),
                _make_mock_result("language_ 12345 TCP 127.0.0.1:61958 (LISTEN)"),
            ]

            with patch("requests.post") as mock_post:
                mock_response = Mock()
                mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
                mock_response.raise_for_status = Mock()
                mock_post.return_value = mock_response

                client = CodeiumClient()

                with pytest.raises(CodeiumServerError) as exc_info:
                    client.get_user_status()

                assert "failed to parse response" in str(exc_info.value).lower()

    def test_custom_ide_name(self):
        """Test client with custom IDE name."""
        client = CodeiumClient(ide_name="vscode")
        assert client.ide_name == "vscode"
        assert client.DEFAULT_IDE == "antigravity"
