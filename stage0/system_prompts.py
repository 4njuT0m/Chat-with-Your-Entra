"""Stage 0 - Compare system prompts.

Asks the same question three times, each time with a different system prompt,
to see how the system prompt changes the answer.
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

question = "Should I give every user the Global Administrator role so they can fix their own problems?"

system_prompts = {
    "Friendly helper": "You are a friendly, helpful assistant.",
    "Strict security auditor": (
        "You are a strict Microsoft Entra security auditor. "
        "Answer in at most 3 bullet points. Always name the security risk."
    ),
    "JSON only": (
        "Reply only with JSON in this format and no other text: "
        '{"answer": "yes or no", "risk": "low, medium or high", "reason": "one sentence"}'
    ),
}

print(f"Question: {question}\n")

for name, prompt in system_prompts.items():
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
    )
    print(f"===== {name} =====")
    print(response.choices[0].message.content)
    print()
