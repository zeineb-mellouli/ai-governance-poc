"""Shared test doubles: a scripted stand-in for the OpenAI client so tests never call the real API."""

import json
import re
from types import SimpleNamespace


FAKE_FINGERPRINT = "fp_test_backend"


def _fake_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        system_fingerprint=FAKE_FINGERPRINT,
    )


def verdict(
    policy_id: str,
    *,
    applies: bool = True,
    violation: bool | None = True,
    quote: str = "",
    evidence: str = "e",
    reasoning: str = "",
) -> dict:
    """Build one structured verdict in the shape the Auditor now demands.

    The model no longer states a status, and is no longer asked for a confidence:
    it answers `applies` / `violation_present` and supplies a verbatim
    `evidence_quote`. Status is derived from those, and confidence is measured by
    the auditor as the agreement rate across samples.
    """
    return {
        "policy_id": policy_id,
        "reasoning": reasoning,
        "applies": applies,
        "violation_present": violation,
        "evidence_quote": quote,
        "evidence": evidence,
    }


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
        # Self-consistency sampling asks the same prompt several times. Counting
        # calls per prompt lets a test hand back a *different* answer each time,
        # which is the only way to exercise the vote.
        self._call_counts: dict[str, int] = {}
        self.chat = SimpleNamespace(completions=self)

    def call_count(self, prompt_substring: str) -> int:
        """How many times a prompt containing this substring was sent (i.e. k)."""
        return sum(n for prompt, n in self._call_counts.items() if prompt_substring in prompt)

    @staticmethod
    def _script_for_sample(scripted: list, sample_index: int) -> list:
        """Pick this sample's verdicts.

        A plain list of verdicts is used for every sample. A list *of lists* is a
        per-sample script, cycled: [[s1], [s2], [s3]] makes the three samples
        disagree so the majority vote has something to resolve.
        """
        if scripted and isinstance(scripted[0], list):
            return scripted[sample_index % len(scripted)]
        return scripted

    def create(self, model, messages, response_format, temperature, **kwargs):
        user_content = messages[1]["content"]

        if self._raise_for and self._raise_for in user_content:
            raise RuntimeError("simulated LLM failure")

        if user_content.startswith("Policy: "):
            for policy_id, remediation in self._remediations.items():
                if user_content.startswith(f"Policy: {policy_id}"):
                    return _fake_response(json.dumps(remediation))
            return _fake_response(json.dumps({"description": "no-op", "fix": "# no fix scripted"}))

        sample_index = self._call_counts.get(user_content, 0)
        self._call_counts[user_content] = sample_index + 1

        if user_content.startswith("Repository: "):
            scripted = self._script_for_sample(self._holistic_verdicts, sample_index)
            return _fake_response(json.dumps({"verdicts": self._complete(scripted, user_content)}))

        for substring, verdicts in self._verdicts.items():
            if substring in user_content:
                scripted = self._script_for_sample(verdicts, sample_index)
                return _fake_response(json.dumps({"verdicts": self._complete(scripted, user_content)}))
        return _fake_response(json.dumps({"verdicts": self._complete([], user_content)}))

    @staticmethod
    def _complete(scripted: list, user_content: str) -> list:
        """Pad the scripted verdicts out to one per candidate policy.

        The Auditor now requires a verdict for every policy it offered, and logs
        an error for any it does not get back. A fake that answered only the
        policy a test cares about would therefore inject spurious errors into
        every test, so it answers the rest with "does not apply" -- exactly what
        a well-behaved model does.
        """
        candidate_ids = re.findall(r"^- policy_id: (\S+)", user_content, re.MULTILINE)
        answered = {v["policy_id"] for v in scripted}
        return list(scripted) + [
            verdict(pid, applies=False, violation=None, evidence="does not apply")
            for pid in candidate_ids
            if pid not in answered
        ]
