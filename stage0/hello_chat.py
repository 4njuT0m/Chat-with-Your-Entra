"""Stage 0 - Hello World chat with Azure OpenAI.

Sends one question to the model and prints the reply.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

# Read the values from the .env file
load_dotenv()

endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]

# Azure OpenAI v1 API: normal OpenAI client, Azure endpoint + /openai/v1/
client = OpenAI(
    base_url=f"{endpoint}/openai/v1/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

response = client.chat.completions.create(
    model=deployment,  # this is the deployment name, not the model name
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! In one sentence, what is Microsoft Entra ID?"},
    ],
)

print("Deployment:", deployment)
print("Reply:", response.choices[0].message.content)
print("Tokens used:", response.usage.total_tokens)
