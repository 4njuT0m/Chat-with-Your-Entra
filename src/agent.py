"""Stage 2 - Entra security assistant: agent loop with function calling.

The model can call the tools in tools.py as many times as it needs
(up to MAX_TOOL_ROUNDS) before it writes the final answer.

Run from the repo folder:
    python src\\agent.py                                  # chat mode, type 'exit' to stop
    python src\\agent.py "Who are the Global Admins?"     # one question, then exit
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOLS, run_tool

load_dotenv()

endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]

client = OpenAI(
    base_url=f"{endpoint}/openai/v1/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.md"
SYSTEM_PROMPT = PROMPT_FILE.read_text(encoding="utf-8")

MAX_TOOL_ROUNDS = 8  # safety limit so the loop can't run forever


def ask(messages: list[dict]) -> str:
    """Run the agent loop for the last user message and return the final answer."""
    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(model=deployment, messages=messages, tools=TOOLS)
        msg = response.choices[0].message

        # No tool requested: this is the final answer
        if not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content})
            return msg.content

        # Save the model's tool requests in the history
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

        # Run each tool and send the result back to the model
        for call in msg.tool_calls:
            print(f"  [tool] {call.function.name}({call.function.arguments})")
            result = run_tool(call.function.name, call.function.arguments)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return "Stopped: the agent used too many tool calls in a row."


def main() -> None:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # One-question mode: python src\agent.py "question"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        print(f"You: {question}")
        messages.append({"role": "user", "content": question})
        print(f"AI: {ask(messages)}")
        return

    print("Entra security assistant. Type 'exit' to stop.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue
        messages.append({"role": "user", "content": question})
        print(f"AI: {ask(messages)}\n")


if __name__ == "__main__":
    main()
