"""Azure OpenAI client construction, and the one call every model request uses.

Routing every request through `chat_json` keeps the reproducibility settings in
one place instead of drifting across call sites.

`temperature=0` alone is not determinism: on a batched backend, greedy decoding
still varies with how requests are grouped. `seed` asks for a reproducible
sample, and `system_fingerprint` records which backend served it -- so if the
fingerprint changes between runs, the model moved underneath us and the output
differences are not a bug in our prompts.

See docs/ARCHITECTURE.md for the full reproducibility contract.
"""

import json
import os

from openai import AzureOpenAI, OpenAI

# Fixed so a re-run of the same repo issues byte-identical requests.
REQUEST_SEED = 20240101
REQUEST_TEMPERATURE = 0


def get_client() -> AzureOpenAI:
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
    """One JSON-mode completion under the fixed determinism settings.

    `seed` and `temperature` are overridable for self-consistency sampling, which
    needs several *different* samples of one prompt. The sampler walks a fixed
    seed sequence, so the set of samples stays reproducible.

    Appends the response's system_fingerprint to `fingerprints` when supplied.
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
