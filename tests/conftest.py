"""Pytest session fixtures shared across all test modules.

Sets the Azure deployment env var to a dummy value so that
os.environ["AZURE_OPENAI_DEPLOYMENT"] does not raise KeyError during tests
that use FakeOpenAIClient (which ignores the model name entirely).
"""

import os
import pytest


@pytest.fixture(autouse=True)
def set_azure_deployment_env(monkeypatch):
    if "AZURE_OPENAI_DEPLOYMENT" not in os.environ:
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "fake-deployment")
