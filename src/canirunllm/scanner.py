from canirunllm.hardware.scanner import scan_hardware
from canirunllm.registry.models import get_known_models
from canirunllm.compatibility.engine import check_compatibility


def scan_models():

    hardware = scan_hardware()

    models = get_known_models()

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
