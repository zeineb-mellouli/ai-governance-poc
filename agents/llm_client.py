"""Builds whichever OpenAI-compatible client the environment is configured for.

Prefers Azure OpenAI (AZURE_OPENAI_ENDPOINT set) and falls back to plain
OpenAI (OPENAI_API_KEY) otherwise. Both expose the identical
client.chat.completions.create(...) interface, so nothing in auditor_agent.py
or remediation_agent.py needs to know which one is actually in use.
"""

import os

from openai import AzureOpenAI, OpenAI


def get_client() -> OpenAI:
    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )
