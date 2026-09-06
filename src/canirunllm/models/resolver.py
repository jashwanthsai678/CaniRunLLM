from canirunllm.models.model import ModelSpec
from canirunllm.registry.models import get_known_models


class ModelResolver:

    def __init__(self):
        self.models = get_known_models()

    def resolve_all(self) -> list[ModelSpec]:
        return self.models

    def search(self, query: str) -> list[ModelSpec]:

        query = query.lower().strip()

        return [
            model
            for model in self.models
            if (
                query in model.name.lower()
                or query in model.family.lower()
                or query in model.architecture.lower()
                or query in model.quantization.lower()
            )
        ]

    def get_by_family(
        self,
        family: str,
    ) -> list[ModelSpec]:

        family = family.lower().strip()

        return [
            model
            for model in self.models
            if model.family.lower() == family
        ]

    def get_variant(
        self,
        name: str,
    ) -> ModelSpec | None:

        name = name.lower().strip()

        for model in self.models:

            if model.name.lower() == name:
                return model

        return None
