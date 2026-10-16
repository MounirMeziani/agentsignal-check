"""OpenAI Agents SDK: approval-gated charge tool with NO idempotency key (charges on every invocation)."""
from agents import Agent, RunContextWrapper, function_tool
from tests.fixtures import payments
from tests.fixtures.oai_model import ScriptedModel

@function_tool(needs_approval=True)
def charge(ctx: RunContextWrapper[dict], amount: int) -> str:
    """Charge the customer."""
    return payments.charge(amount)

def build():
    return Agent(name="Billing", instructions="bill", model=ScriptedModel([("charge", {"amount": 1999})]), tools=[charge])
