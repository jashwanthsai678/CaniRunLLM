import sys

from canirunllm.hardware.scanner import scan_hardware


def main():
    if len(sys.argv) < 2:
        print("Can I Run LLM?")
        print()
        print("Usage:")
        print("  canirunllm scan")
        return

    command = sys.argv[1]

    if command == "scan":
        hardware = scan_hardware()

        print("Can I Run LLM?")
        print()
        print("Hardware detected:")
        print()
        print("CPU:")
        print(f"  Name: {hardware['cpu']['name']}")
        print(f"  Physical cores: {hardware['cpu']['physical_cores']}")
        print(f"  Logical cores: {hardware['cpu']['logical_cores']}")

        print()
        print("Memory:")
        print(
            f"  Total: "
            f"{hardware['memory']['total_bytes'] / (1024 ** 3):.2f} GB"
        )

        print()
        print("Operating System:")
        print(f"  System: {hardware['os']['system']}")
        print(f"  Release: {hardware['os']['release']}")

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()