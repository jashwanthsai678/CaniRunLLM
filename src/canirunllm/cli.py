import sys

from canirunllm.scanner import scan_models


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

    if command == "scan":

        hardware, results = scan_models()

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

            model = item["model"]
            result = item["result"]

            print(
                f"{model.name:<25}"
                f"{result.verdict:<12}"
                f"{result.reason}"
            )

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()