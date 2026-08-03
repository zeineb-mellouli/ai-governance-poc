"""Shared test doubles: a scripted stand-in for the OpenAI client so tests never call the real API."""

import json
from types import SimpleNamespace


def _fake_response(content: str):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class FakeOpenAIClient:
    """Returns a scripted verdicts/remediation payload based on a substring match on the prompt.

    verdicts_by_path_substring: {substring -> list of verdict dicts} for per-file Auditor calls.
    holistic_verdicts: list of verdict dicts for the whole-repo Auditor call (empty by default).
    remediation_by_policy_id: {policy_id -> {"description": ..., "fix": ...}} for Remediation Agent calls.
    raise_for_substring: if set, raises instead of responding when the prompt contains this substring.

    Dispatch is by prompt prefix: "Policy: " -> remediation, "Repository: " -> the
    holistic pass, anything else ("File path: ") -> per-file. This matters because
    the holistic prompt contains every file's content, so it would otherwise also
    match a per-file substring meant only for one specific file.
    """

    def __init__(
        self,
        verdicts_by_path_substring: dict | None = None,
        holistic_verdicts: list | None = None,
        remediation_by_policy_id: dict | None = None,
        raise_for_substring: str | None = None,
    ):
        self._verdicts = verdicts_by_path_substring or {}
        self._holistic_verdicts = holistic_verdicts or []
        self._remediations = remediation_by_policy_id or {}
        self._raise_for = raise_for_substring
        self.chat = SimpleNamespace(completions=self)

    def create(self, model, messages, response_format, temperature):
        user_content = messages[1]["content"]

        if self._raise_for and self._raise_for in user_content:
            raise RuntimeError("simulated LLM failure")

        if user_content.startswith("Policy: "):
            for policy_id, remediation in self._remediations.items():
                if user_content.startswith(f"Policy: {policy_id}"):
                    return _fake_response(json.dumps(remediation))
            return _fake_response(json.dumps({"description": "no-op", "fix": "# no fix scripted"}))

        if user_content.startswith("Repository: "):
            return _fake_response(json.dumps({"verdicts": self._holistic_verdicts}))

        for substring, verdicts in self._verdicts.items():
            if substring in user_content:
                return _fake_response(json.dumps({"verdicts": verdicts}))
        return _fake_response(json.dumps({"verdicts": []}))
