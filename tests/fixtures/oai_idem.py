"""OpenAI Agents SDK: same agent, but the tool passes a key derived from stable run data
(order_id from the run context + tool name), so retries/resumes are deduped by the provider."""
from agents import Agent, function_tool
from agents.tool_context import ToolContext
from tests.fixtures import payments
from tests.fixtures.oai_model import ScriptedModel

@function_tool(needs_approval=True)
def charge(ctx: ToolContext[dict], amount: int) -> str:
    """Charge the customer."""
    return payments.charge(amount, idempotency_key=f"{ctx.context['order_id']}:{ctx.tool_name}")

def build():
    return Agent(name="Billing", instructions="bill", model=ScriptedModel([("charge", {"amount": 1999})]), tools=[charge])
