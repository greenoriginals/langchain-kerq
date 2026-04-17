"""KerqTelemetryHandler and KerqGuard — telemetry and trust gating callbacks."""

import time
import logging
from typing import Any, Dict, Optional, Union
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from langchain_kerq.client import KerqClient

logger = logging.getLogger(__name__)


def _safe_trust_score(score_data: Any) -> int:
    """Extract trust score safely. Returns 0 if missing, null, or unparseable."""
    if score_data is None:
        return 0
    if isinstance(score_data, dict):
        raw = score_data.get("trust_score")
        if raw is None:
            return 0
        try:
            return int(raw)
        except (ValueError, TypeError):
            return 0
    try:
        return int(score_data)
    except (ValueError, TypeError):
        return 0


class KerqTelemetryHandler(BaseCallbackHandler):
    """Callback handler that reports tool call telemetry to Kerq.

    Telemetry is always fire-and-forget — it never blocks or crashes your agent.
    """

    api_key: str
    telemetry: bool

    def __init__(self, api_key: str, telemetry: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.telemetry = telemetry
        self._client = KerqClient(api_key=api_key)
        self._start_times: Dict[str, float] = {}

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Record tool start time."""
        self._start_times[str(run_id)] = time.time()

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list] = None,
        **kwargs: Any,
    ) -> None:
        """Report successful tool execution telemetry."""
        if not self.telemetry:
            return
        try:
            duration = time.time() - self._start_times.pop(str(run_id), time.time())
            self._client.report_telemetry({
                "run_id": str(run_id),
                "status": "success",
                "duration_ms": round(duration * 1000),
                "output_length": len(output) if output else 0,
            })
        except Exception:
            pass  # telemetry must never throw

    def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list] = None,
        **kwargs: Any,
    ) -> None:
        """Report failed tool execution telemetry."""
        if not self.telemetry:
            return
        try:
            duration = time.time() - self._start_times.pop(str(run_id), time.time())
            self._client.report_telemetry({
                "run_id": str(run_id),
                "status": "error",
                "duration_ms": round(duration * 1000),
                "error": str(error)[:500],
            })
        except Exception:
            pass  # telemetry must never throw


class KerqGuard(BaseCallbackHandler):
    """Combined trust gating + telemetry callback.

    Checks trust score before a tool runs. Blocks tools scoring
    below min_score. Reports telemetry on every execution.
    """

    api_key: str
    min_score: int
    telemetry: bool

    def __init__(
        self,
        api_key: str,
        min_score: int = 70,
        telemetry: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.min_score = min_score
        self.telemetry = telemetry
        self._client = KerqClient(api_key=api_key)
        self._start_times: Dict[str, float] = {}

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Check trust score and block if below threshold."""
        self._start_times[str(run_id)] = time.time()
        tool_name = serialized.get("name", "unknown")

        try:
            score_data = self._client.get_trust_score(tool_name)
            score = _safe_trust_score(score_data)
        except Exception as e:
            logger.warning(f"Kerq trust check failed for {tool_name}: {e}")
            score = 0

        if score < self.min_score:
            raise ValueError(
                f"Kerq trust gate blocked '{tool_name}': "
                f"score {score} < minimum {self.min_score}"
            )

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list] = None,
        **kwargs: Any,
    ) -> None:
        """Report successful execution telemetry."""
        if not self.telemetry:
            return
        try:
            duration = time.time() - self._start_times.pop(str(run_id), time.time())
            self._client.report_telemetry({
                "run_id": str(run_id),
                "status": "success",
                "duration_ms": round(duration * 1000),
                "output_length": len(output) if output else 0,
            })
        except Exception:
            pass

    def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list] = None,
        **kwargs: Any,
    ) -> None:
        """Report failed execution telemetry."""
        if not self.telemetry:
            return
        try:
            duration = time.time() - self._start_times.pop(str(run_id), time.time())
            self._client.report_telemetry({
                "run_id": str(run_id),
                "status": "error",
                "duration_ms": round(duration * 1000),
                "error": str(error)[:500],
            })
        except Exception:
            pass
