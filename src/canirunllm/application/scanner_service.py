from canirunllm.hardware.scanner import scan_hardware
from canirunllm.models.resolver import ModelResolver
from canirunllm.models.results import ModelCheckResult
from canirunllm.compatibility.engine import check_compatibility
from canirunllm.recommendation.engine import rank_models


class ScannerService:

    def __init__(self):
        self.resolver = ModelResolver()

    def scan(self):
        hardware = scan_hardware()
        models = self.resolver.resolve_all()

        results = []

        for model in models:
            result = check_compatibility(
                hardware,
                model,
            )

            results.append(
                ModelCheckResult(
                    model=model,
                    compatibility=result,
                )
            )

        return hardware, results

    def recommend(self):
        hardware, results = self.scan()

        return hardware, rank_models(results)

    def search(self, query: str):
        return self.resolver.search(query)

    def check(self, query: str):

        hardware = scan_hardware()

        variant = self.resolver.get_variant(query)

        if variant is not None:
            result = check_compatibility(
                hardware,
                variant,
            )

            return {
                "type": "variant",
                "models": [
                    ModelCheckResult(
                        model=variant,
                        compatibility=result,
                    )
                ],
            }

        family_models = self.resolver.get_by_family(query)

        if family_models:

            results = []

            for model in family_models:
                result = check_compatibility(
                    hardware,
                    model,
                )

                results.append(
                    ModelCheckResult(
                        model=model,
                        compatibility=result,
                    )
                )

            return {
                "type": "family",
                "models": results,
            }

        return None
