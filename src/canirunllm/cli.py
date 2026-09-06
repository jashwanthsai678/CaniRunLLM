import sys

from canirunllm.application.scanner_service import ScannerService


def bytes_to_gb(value):
    return value / (1024 ** 3)


def main():
    if len(sys.argv) < 2:
        print("Can I Run LLM?")
        print()
        print("Usage:")
        print("  canirunllm scan")
        return

    command = sys.argv[1]

    service = ScannerService()

    if command == "scan":

        hardware, results = service.scan()

        print("Can I Run LLM?")
        print("=" * 40)

        print()
        print("CPU")
        print("-" * 40)

        cpu = hardware.cpu

        print(f"Name:           {cpu.name}")
        print(f"Physical cores: {cpu.physical_cores}")
        print(f"Logical cores:  {cpu.logical_cores}")

        print()
        print("RAM")
        print("-" * 40)

        memory = hardware.memory

        print(
            f"Total: "
            f"{bytes_to_gb(memory.total_bytes):.2f} GB"
        )

        print(
            f"Available: "
            f"{bytes_to_gb(memory.available_bytes):.2f} GB"
        )

        print()
        print("GPU")
        print("-" * 40)

        gpus = hardware.gpus

        if not gpus:
            print("No supported GPU detected.")

        for index, gpu in enumerate(gpus):

            print(f"GPU {index}: {gpu.name}")

            print(
                f"  VRAM: "
                f"{bytes_to_gb(gpu.memory_total_bytes):.2f} GB"
            )

            print(
                f"  VRAM Free: "
                f"{bytes_to_gb(gpu.memory_free_bytes):.2f} GB"
            )

            print(
                f"  Utilization: "
                f"{gpu.utilization_percent:.1f}%"
            )

        print()
        print("Operating System")
        print("-" * 40)

        os_info = hardware.os

        print(f"System:  {os_info.system}")
        print(f"Release: {os_info.release}")

        print()
        print("MODEL COMPATIBILITY")
        print("-" * 60)

        for item in results:

            model = item.model
            result = item.compatibility

            print()
            print(model.name)
            print(f"  Memory:     {result.memory_verdict.value}")
            print(f"  Strategy:   {result.memory_strategy}")
            print(f"  Runtime:    {result.runtime_verdict.value}")
            print(f"  Verdict:    {result.overall_verdict.value}")
            print(f"  Confidence: {result.confidence.value}")

    elif command == "search":

        if len(sys.argv) < 3:
            print("Usage:")
            print("  canirunllm search <query>")
            return

        query = sys.argv[2]

        models = service.search(query)

        print()
        print("MODEL SEARCH")
        print("-" * 60)

        if not models:
            print("No models found.")
            return

        for model in models:
            print(
                f"{model.name:<30}"
                f"{model.quantization:<12}"
                f"{model.runtime or 'unknown'}"
            )

    elif command == "check":

        if len(sys.argv) < 3:
            print("Usage:")
            print("  canirunllm check <model>")
            return

        query = sys.argv[2]

        outcome = service.check(query)

        if outcome is None:
            print(f"Model not found: {query}")
            return

        if outcome["type"] == "variant":

            item = outcome["models"][0]
            variant = item.model
            result = item.compatibility

            print()
            print("MODEL CHECK")
            print("-" * 60)

            print(f"Model:        {variant.name}")
            print(f"Family:       {variant.family}")
            print(f"Parameters:   {variant.parameters:,}")
            print(f"Quantization: {variant.quantization}")
            print(f"Runtime:      {variant.runtime or 'unknown'}")

            print()
            print(f"Memory:       {result.memory_verdict.value}")
            print(f"Strategy:     {result.memory_strategy}")
            print(f"Runtime:      {result.runtime_verdict.value}")
            print()
            print(f"Verdict:      {result.overall_verdict.value}")
            print(f"Confidence:   {result.confidence.value}")
            print()
            print(f"Reason:       {result.reason}")

            return

        print()
        print("MODEL FAMILY CHECK")
        print("-" * 60)

        print(f"Family: {query}")

        print()

        for item in outcome["models"]:

            model = item.model
            result = item.compatibility

            print(
                f"{model.name:<30}"
                f"{result.overall_verdict.value:<22}"
                f"{result.confidence.value}"
            )

    elif command == "recommend":

        hardware, ranked = service.recommend()

        print("RECOMMENDED MODELS")
        print("-" * 60)

        for entry in ranked:

            stars = "*" * entry.stars + "." * (5 - entry.stars)

            print()
            print(f"{entry.model.name}  [{stars}]")
            print(f"  Tier:       {entry.tier.value}")
            print(f"  Verdict:    {entry.compatibility.overall_verdict.value}")
            print(f"  Strategy:   {entry.compatibility.memory_strategy}")
            print(f"  Confidence: {entry.compatibility.confidence.value}")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
