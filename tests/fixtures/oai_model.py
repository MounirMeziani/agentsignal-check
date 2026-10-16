"""Offline scripted agents.Model (no API key). First turn emits tool calls; later turns echo tool output."""
import json
from agents import Model, ModelResponse, Usage
from openai.types.responses import ResponseFunctionToolCall, ResponseOutputMessage, ResponseOutputText

class ScriptedModel(Model):
    def __init__(self, calls):
        self.calls = calls
    async def get_response(self, system_instructions, input, *a, **kw):
        items = input if isinstance(input, list) else []
        outs = [i for i in items if isinstance(i, dict) and i.get("type") == "function_call_output"]
        if not outs:
            out = [ResponseFunctionToolCall(type="function_call", id=f"fc_{n}", call_id=f"call_{n}",
                                            name=name, arguments=json.dumps(args))
                   for n, (name, args) in enumerate(self.calls)]
        else:
            text = "done: " + " | ".join(f"{o['call_id']}={o['output']}" for o in outs)
            out = [ResponseOutputMessage(type="message", id="msg_1", role="assistant", status="completed",
                   content=[ResponseOutputText(type="output_text", text=text, annotations=[])])]
        return ModelResponse(output=out, usage=Usage(), response_id=None)
    def stream_response(self, *a, **kw):
        raise NotImplementedError
