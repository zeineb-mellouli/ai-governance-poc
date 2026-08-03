"""Builds whichever OpenAI-compatible client the environment is configured for.

Prefers Azure OpenAI (AZURE_OPENAI_ENDPOINT set) and falls back to plain
OpenAI (OPENAI_API_KEY) otherwise. Both expose the identical
client.chat.completions.create(...) interface, so nothing in auditor_agent.py
or remediation_agent.py needs to know which one is actually in use.
"""

import os

from openai import AzureOpenAI, OpenAI


def get_client() -> OpenAI:
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if azure_endpoint:
        return AzureOpenAI(
            azure_endpoint=azure_endpoint,
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
    return OpenAI()


def get_default_model() -> str:
    """The value to pass as `model=` in chat.completions.create().

    For Azure this must be the deployment name you chose in Azure OpenAI
    Studio, not the underlying model family name -- they are often not the
    same string.
    """
    return (
        os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        or os.environ.get("OPENAI_MODEL")
        or "gpt-5o-mini"
    )
