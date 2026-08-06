"""OpenAI client construction and the single chokepoint every model call goes through.

Every request in the pipeline is routed through `chat_json` so the settings that
control run-to-run reproducibility are declared in exactly one place. Setting
them per-call site is how they drift apart.

`temperature=0` alone is NOT determinism: on a batched, mixture-of-experts
backend, greedy decoding still varies with how requests are grouped. `seed` asks
the backend for a reproducible sample, and `system_fingerprint` reports which
backend configuration served it -- if the fingerprint changes between runs, the
model moved underneath us and output differences are expected rather than a bug
in our prompting.
"""

import json
import os

from openai import AzureOpenAI, OpenAI

# Fixed so a re-run of the same repo issues byte-identical requests.
REQUEST_SEED = 20240101
REQUEST_TEMPERATURE = 0


def get_client() -> OpenAI:
    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


def chat_json(
    client: OpenAI,
    system_prompt: str,
    user_content: str,
    fingerprints: list[str] | None = None,
    seed: int | None = None,
    temperature: float | None = None,
) -> dict:
    """Issue one JSON-mode completion under the fixed determinism settings.

    `seed` and `temperature` are overridable for self-consistency sampling,
    which needs several *different* samples of the same prompt. That is not a
    hole in the determinism contract: the sampler varies the seed over a fixed,
    known sequence, so the set of samples is itself reproducible.

    Appends the response's system_fingerprint to `fingerprints` when supplied,
    so the caller can record which backend served the run.
    """
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=REQUEST_TEMPERATURE if temperature is None else temperature,
        seed=REQUEST_SEED if seed is None else seed,
    )

    if fingerprints is not None:
        fingerprint = getattr(response, "system_fingerprint", None)
        if fingerprint:
            fingerprints.append(fingerprint)

    return json.loads(response.choices[0].message.content)
