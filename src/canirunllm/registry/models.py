import json
from pathlib import Path

from canirunllm.models.model import ModelSpec


REGISTRY_PATH = Path(__file__).parent / "models.json"


def get_known_models() -> list[ModelSpec]:

    with open(REGISTRY_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    return [
        ModelSpec(**model)
        for model in data
    ]
