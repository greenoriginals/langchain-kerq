"""KerqTrustTool — check trust scores before connecting to any tool."""

from typing import Optional, Type

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from pydantic import BaseModel, Field

from langchain_kerq.client import KerqClient, AsyncKerqClient


class KerqTrustToolInput(BaseModel):
    """Input for KerqTrustTool."""
    tool_id: str = Field(description="The ID or slug of the tool to check trust score for")


def _format_error(e: Exception) -> str:
    """Format API errors into readable messages."""
    import httpx
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 401:
            return "Error: Invalid API key. Check your Kerq API key."
        elif status == 404:
            return "Error: Tool not found in Kerq index."
        elif status == 429:
            return "Error: Rate limit exceeded. Try again later."
        elif status >= 500:
            return "Error: Kerq API server error. Try again later."
        else:
            return f"Error: HTTP {status} from Kerq API."
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Kerq API request timed out."
    elif isinstance(e, httpx.ConnectError):
        return "Error: Could not connect to Kerq API."
    return f"Error: {str(e)}"


class KerqTrustTool(BaseTool):
    """Check a tool's trust score on Kerq before connecting to it.

    Returns trust score, tier, and score breakdown for any tool
    in the Kerq index.
    """

    name: str = "kerq_trust_check"
    description: str = (
        "Check the trust score of an AI tool before connecting to it. "
        "Returns trust score (0-100), trust tier, and detailed breakdown. "
        "Use this to verify a tool is trustworthy before your agent uses it."
    )
    args_schema: Type[BaseModel] = KerqTrustToolInput
    api_key: str = ""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key=api_key, **kwargs)

    def _run(
        self,
        tool_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Synchronously fetch trust score."""
        client = KerqClient(api_key=self.api_key)
        try:
            result = client.get_trust_score(tool_id)
            return str(result)
        except Exception as e:
            return _format_error(e)
        finally:
            client.close()

    async def _arun(
        self,
        tool_id: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Asynchronously fetch trust score."""
        client = AsyncKerqClient(api_key=self.api_key)
        try:
            result = await client.get_trust_score(tool_id)
            return str(result)
        except Exception as e:
            return _format_error(e)
        finally:
            await client.close()
