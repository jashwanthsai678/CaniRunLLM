from canirunllm.hardware.scanner import scan_hardware
from canirunllm.models.resolver import ModelResolver
from canirunllm.compatibility.engine import check_compatibility


def scan_models():

    hardware = scan_hardware()

    resolver = ModelResolver()

    models = resolver.resolve_all()

    results = []

    for model in models:

        result = check_compatibility(
            hardware,
            model,
        )

        results.append(
            {
                "model": model,
                "result": result,
            }
        )

    return hardware, results
