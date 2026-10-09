"""Stage 0 - Simple tool-calling agent.

The model gets one tool: get_current_time. When a question needs the time,
the model asks for the tool, this script runs it, and the result goes back
to the model so it can write the final answer.
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]

client = OpenAI(
    base_url=f"{endpoint}/openai/v1/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)


def get_current_time(timezone: str) -> str:
    """The real Python function. The model never runs it, this script does."""
    try:
        now = datetime.now(ZoneInfo(timezone))
    except Exception:
        return json.dumps({"error": f"Unknown timezone: {timezone}"})
    return json.dumps({"timezone": timezone, "time": now.strftime("%Y-%m-%d %H:%M:%S")})


# The tool description the model sees: name, what it does, which parameters it takes
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time in a timezone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone name, for example Europe/Berlin or Asia/Tokyo",
                    }
                },
                "required": ["timezone"],
            },
        },
    }
]

question = input("Ask a question (Enter = 'What time is it in Tokyo?'): ").strip()
if not question:
    question = "What time is it in Tokyo?"

messages = [
    {"role": "system", "content": "You are a helpful assistant. Use tools when you need live data."},
    {"role": "user", "content": question},
]

# 1st call: the model decides if it needs the tool
response = client.chat.completions.create(model=deployment, messages=messages, tools=tools)
msg = response.choices[0].message

if msg.tool_calls:
    # Save the model's tool request in the history
    messages.append(
        {
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {"name": call.function.name, "arguments": call.function.arguments},
                }
                for call in msg.tool_calls
            ],
        }
    )

    # Run each requested tool and send the result back
    for call in msg.tool_calls:
        args = json.loads(call.function.arguments)
        print(f"[tool call]   {call.function.name}({args})")
        result = get_current_time(**args)
        print(f"[tool result] {result}")
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    # 2nd call: the model writes the answer using the tool result
    response = client.chat.completions.create(model=deployment, messages=messages, tools=tools)
    msg = response.choices[0].message
else:
    print("[no tool call] the model answered without the tool")

print(f"AI: {msg.content}")
