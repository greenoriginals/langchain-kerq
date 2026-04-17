"""Integration tests — skipped unless KERQ_API_KEY environment variable is set."""

import os
import pytest

from langchain_kerq.tools import KerqTrustTool
from langchain_kerq.callbacks import KerqTelemetryHandler, KerqGuard

KERQ_API_KEY = os.environ.get("KERQ_API_KEY")

skip_no_key = pytest.mark.skipif(
    not KERQ_API_KEY,
    reason="KERQ_API_KEY not set — skipping integration tests",
)


@skip_no_key
class TestLiveTrustTool:
    """Live tests against Kerq API."""

    def test_lookup_known_tool(self):
        tool = KerqTrustTool(api_key=KERQ_API_KEY)
        result = tool._run("github-mcp-server")
        assert "trust_score" in result or "Error" in result

    def test_lookup_unknown_tool(self):
        tool = KerqTrustTool(api_key=KERQ_API_KEY)
        result = tool._run("this-tool-does-not-exist-12345")
        assert "not found" in result.lower() or "Error" in result


@skip_no_key
class TestLiveTelemetry:
    """Live telemetry tests."""

    def test_handler_creation(self):
        handler = KerqTelemetryHandler(api_key=KERQ_API_KEY)
        assert handler.api_key == KERQ_API_KEY
        assert handler.telemetry is True

    def test_guard_creation(self):
        guard = KerqGuard(api_key=KERQ_API_KEY, min_score=50)
        assert guard.min_score == 50
        assert guard.telemetry is True
