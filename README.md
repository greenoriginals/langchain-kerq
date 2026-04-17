# langchain-kerq

LangChain integration for [Kerq](https://kerq.dev) — trust scoring and telemetry for AI agent tool calls.

## Why Kerq?

AI agents connect to dozens of tools. Kerq scores each one for trust, security, and reliability before your agent runs it — and tracks performance telemetry so you can see exactly what's happening.

## Installation

```bash
pip install langchain-kerq

Quick Start
Get your API key at kerq.dev. Full API docs at kerq.dev/docs.

KerqTrustTool
Check a tool's trust score before connecting to it. Works as a standard LangChain tool that agents can invoke directly.
from langchain_kerq import KerqTrustTool

kerq = KerqTrustTool(api_key="your-api-key")

# Invoke directly
result = kerq.invoke("github-mcp-server")
print(result)
# {"trust_score": 87, "tier": "high", "score_breakdown": {...}}

# Or let your agent use it as a tool
from langchain_core.agents import AgentExecutor

agent = ...  # your LangChain agent
agent_executor = AgentExecutor(agent=agent, tools=[kerq])


KerqTelemetryHandler
Automatically intercept every tool call and report telemetry to Kerq. Telemetry is always fire-and-forget — it never blocks your agent.
from langchain_kerq import KerqTelemetryHandler

handler = KerqTelemetryHandler(api_key="your-api-key")

# Attach to any agent invocation
result = agent.invoke(
    {"input": "search the web for news"},
    config={"callbacks": [handler]},
)

Options:
Parameter
Type
Default
Description
api_key
str
required
Your Kerq API key
telemetry
bool
True
Enable/disable telemetry reporting


KerqGuard
The full package: trust gating + telemetry in one callback. Blocks tools that score below your threshold and reports all executions to Kerq.
from langchain_kerq import KerqGuard

guard = KerqGuard(
    api_key="your-api-key",
    min_score=70,   # block any tool scoring below 70
    telemetry=True, # report execution telemetry
)

result = agent.invoke(
    {"input": "run my workflow"},
    config={"callbacks": [guard]},
)

Options:
Parameter
Type
Default
Description
api_key
str
required
Your Kerq API key
min_score
int
70
Minimum trust score to allow a tool to run (0–100)
telemetry
bool
True
Enable/disable telemetry reporting

Trust score rules:
Score >= min_score -> tool runs
Score < min_score -> tool is blocked
Score missing, null, or unparseable -> treated as 0 -> blocked

Error Handling
All components handle API errors gracefully:
401 Invalid key -> warning logged, operation skipped
404 Not found -> clear error returned
429 Rate limited -> warning logged, operation skipped
500 Server error -> warning logged, operation skipped
Network errors -> warning logged, operation skipped
Errors never crash your agent.

License
MIT — see LICENSE.
