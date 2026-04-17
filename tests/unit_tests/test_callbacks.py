"""Unit tests for KerqTelemetryHandler and KerqGuard — all mocked."""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from langchain_kerq.callbacks import KerqTelemetryHandler, KerqGuard, _safe_trust_score


@pytest.fixture
def handler():
    with patch("langchain_kerq.callbacks.KerqClient"):
        return KerqTelemetryHandler(api_key="test-key-123")


@pytest.fixture
def guard():
    with patch("langchain_kerq.callbacks.KerqClient"):
        return KerqGuard(api_key="test-key-123", min_score=70)


class TestSafeTrustScore:
    """Tests for _safe_trust_score helper."""

    def test_valid_dict_score(self):
        assert _safe_trust_score({"trust_score": 85}) == 85

    def test_none_returns_zero(self):
        assert _safe_trust_score(None) == 0

    def test_missing_key_returns_zero(self):
        assert _safe_trust_score({"other": "data"}) == 0

    def test_null_score_returns_zero(self):
        assert _safe_trust_score({"trust_score": None}) == 0

    def test_unparseable_returns_zero(self):
        assert _safe_trust_score({"trust_score": "not-a-number"}) == 0

    def test_raw_int(self):
        assert _safe_trust_score(92) == 92

    def test_raw_string_number(self):
        assert _safe_trust_score("75") == 75


class TestKerqTelemetryHandler:
    """Tests for telemetry callback."""

    def test_on_tool_start_records_time(self, handler):
        run_id = uuid4()
        handler.on_tool_start(
            serialized={"name": "test-tool"},
            input_str="test input",
            run_id=run_id,
        )
        assert str(run_id) in handler._start_times

    def test_on_tool_end_reports_telemetry(self, handler):
        run_id = uuid4()
        handler._start_times[str(run_id)] = 1000.0
        handler.on_tool_end(output="result", run_id=run_id)
        handler._client.report_telemetry.assert_called_once()
        payload = handler._client.report_telemetry.call_args[0][0]
        assert payload["status"] == "success"
        assert "duration_ms" in payload

    def test_on_tool_error_reports_telemetry(self, handler):
        run_id = uuid4()
        handler._start_times[str(run_id)] = 1000.0
        handler.on_tool_error(error=Exception("boom"), run_id=run_id)
        handler._client.report_telemetry.assert_called_once()
        payload = handler._client.report_telemetry.call_args[0][0]
        assert payload["status"] == "error"
        assert "boom" in payload["error"]

    def test_telemetry_disabled_skips_report(self, handler):
        handler.telemetry = False
        run_id = uuid4()
        handler.on_tool_end(output="result", run_id=run_id)
        handler._client.report_telemetry.assert_not_called()


class TestKerqGuard:
    """Tests for trust gating + telemetry guard."""

    def test_allows_high_score(self, guard):
        guard._client.get_trust_score.return_value = {"trust_score": 85}
        run_id = uuid4()
        # Should not raise
        guard.on_tool_start(
            serialized={"name": "trusted-tool"},
            input_str="test",
            run_id=run_id,
        )

    def test_blocks_low_score(self, guard):
        guard._client.get_trust_score.return_value = {"trust_score": 40}
        run_id = uuid4()
        with pytest.raises(ValueError, match="trust gate blocked"):
            guard.on_tool_start(
                serialized={"name": "sketchy-tool"},
                input_str="test",
                run_id=run_id,
            )

    def test_blocks_null_score(self, guard):
        guard._client.get_trust_score.return_value = {"trust_score": None}
        run_id = uuid4()
        with pytest.raises(ValueError, match="trust gate blocked"):
            guard.on_tool_start(
                serialized={"name": "unknown-tool"},
                input_str="test",
                run_id=run_id,
            )

    def test_blocks_on_api_failure(self, guard):
        guard._client.get_trust_score.side_effect = Exception("API down")
        run_id = uuid4()
        with pytest.raises(ValueError, match="trust gate blocked"):
            guard.on_tool_start(
                serialized={"name": "any-tool"},
                input_str="test",
                run_id=run_id,
            )
