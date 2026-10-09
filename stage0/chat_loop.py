"""Stage 0 - Chat loop with message history.

Type a message and get a reply. The script keeps every earlier message,
so the model remembers the conversation. Type 'exit' to stop.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]

client = OpenAI(
    base_url=f"{endpoint}/openai/v1/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

# The history starts with the system prompt. Every question and answer is added to it.
messages = [
    {"role": "system", "content": "You are a helpful assistant. Keep answers short."},
]

print("Chat started. Type 'exit' to stop.\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ("exit", "quit"):
        break
    if not user_input:
        continue

    messages.append({"role": "user", "content": user_input})

    # The whole history is sent every time. The model itself has no memory.
    response = client.chat.completions.create(model=deployment, messages=messages)
    reply = response.choices[0].message.content

    messages.append({"role": "assistant", "content": reply})
    print(f"AI: {reply}\n")

print(f"Chat ended. Messages in history: {len(messages)}")
