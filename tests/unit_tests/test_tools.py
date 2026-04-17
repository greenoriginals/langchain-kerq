"""Unit tests for KerqTrustTool — all mocked, no network needed."""

import pytest
from unittest.mock import patch, MagicMock
import httpx

from langchain_kerq.tools import KerqTrustTool, _format_error


@pytest.fixture
def tool():
    return KerqTrustTool(api_key="test-key-123")


class TestKerqTrustTool:
    """Tests for KerqTrustTool._run (sync)."""

    def test_successful_score_lookup(self, tool):
        mock_response = {
            "trust_score": 87,
            "tier": "high",
            "score_breakdown": {"uptime": 95, "response_time": 80}
        }
        with patch.object(tool, "_run", return_value=str(mock_response)):
            result = tool.invoke("github-mcp-server")
            assert "87" in result
            assert "high" in result

    def test_tool_not_found_404(self, tool):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        error = httpx.HTTPStatusError("Not found", request=MagicMock(), response=mock_resp)
        with patch("langchain_kerq.client.KerqClient.get_trust_score", side_effect=error):
            result = tool._run("nonexistent-tool")
            assert "not found" in result.lower()

    def test_invalid_api_key_401(self, tool):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        error = httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=mock_resp)
        with patch("langchain_kerq.client.KerqClient.get_trust_score", side_effect=error):
            result = tool._run("some-tool")
            assert "invalid api key" in result.lower()

    def test_rate_limit_429(self, tool):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        error = httpx.HTTPStatusError("Rate limited", request=MagicMock(), response=mock_resp)
        with patch("langchain_kerq.client.KerqClient.get_trust_score", side_effect=error):
            result = tool._run("some-tool")
            assert "rate limit" in result.lower()

    def test_server_error_500(self, tool):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        error = httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_resp)
        with patch("langchain_kerq.client.KerqClient.get_trust_score", side_effect=error):
            result = tool._run("some-tool")
            assert "server error" in result.lower()

    def test_network_timeout(self, tool):
        error = httpx.TimeoutException("Connection timed out")
        with patch("langchain_kerq.client.KerqClient.get_trust_score", side_effect=error):
            result = tool._run("some-tool")
            assert "timed out" in result.lower()

    def test_connection_error(self, tool):
        error = httpx.ConnectError("Failed to connect")
        with patch("langchain_kerq.client.KerqClient.get_trust_score", side_effect=error):
            result = tool._run("some-tool")
            assert "could not connect" in result.lower()

    def test_tool_name_and_description(self, tool):
        assert tool.name == "kerq_trust_check"
        assert "trust score" in tool.description.lower()
