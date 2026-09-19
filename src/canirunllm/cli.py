import errno
import shutil
import sys
from pathlib import Path

from canirunllm.application.scanner_service import ScannerService
from canirunllm.compatibility.decision import OverallVerdict
from canirunllm.performance.prediction import predict_performance
from canirunllm.web.launcher import run_dashboard, DEFAULT_PORT

ISSUES_URL = "https://github.com/jashwanthsai678/CaniRunLLM/issues"


def bytes_to_gb(value):
    return value / (1024 ** 3)


def format_performance(performance):

    if performance.generation_speed is None:
        return "not available (not expected to run on this hardware)"

    speed = performance.generation_speed

    return (
        f"~{speed.low:.0f}-{speed.high:.0f} {speed.unit} "
        f"(estimated, {performance.confidence.value} confidence, not benchmarked)"
    )


def _python_version_str() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def find_pip_mismatch() -> str | None:
    """Detects the exact confusion that sends people to Google: the
    `pip` on PATH belongs to a different Python install than the one
    actually running canirunllm right now, so `pip install --upgrade
    canirunllm` silently does nothing to this copy.

    Returns a ready-to-use warning (with the correct fix command
    already filled in) if there's a real mismatch, or None if this
    install and the PATH's pip agree - which is the common case, and
    stays completely silent.
    """

    pip_path = shutil.which("pip") or shutil.which("pip3")

    if pip_path is None:
        return None

    try:
        pip_resolved = Path(pip_path).resolve()
        exec_prefix = Path(sys.exec_prefix).resolve()
    except OSError:
        return None

    if str(pip_resolved).lower().startswith(str(exec_prefix).lower()):
        return None

    return (
        f"Note: the 'pip' on your PATH doesn't belong to the Python running "
        f"canirunllm (this install is on Python {_python_version_str()} at "
        f"{sys.executable}). Plain 'pip install --upgrade canirunllm' won't "
        f"update this copy.\n"
        f"To upgrade THIS install, run:\n"
        f'  "{sys.executable}" -m pip install --upgrade canirunllm'
    )


def _is_port_in_use_error(exc: OSError) -> bool:
    return (
        getattr(exc, "errno", None) == errno.EADDRINUSE
        or "10048" in str(exc)
        or "address already in use" in str(exc).lower()
    )


def _print_unexpected_error(exc: Exception) -> None:
    print()
    print(f"Something went wrong: {exc}")
    print("If this looks like a bug, please report it:")
    print(f"  {ISSUES_URL}")


def print_help():
    print("CanIRunLLM - find out which local LLMs your machine can run.")
    print()
    print("Usage:")
    print("  canirunllm scan               scan hardware, evaluate models, open the dashboard")
    print("  canirunllm scan --no-browser  same, but skip opening the dashboard (CI/headless)")
    print("  canirunllm scan --technical   also print the full technical breakdown in the terminal")
    print()
    print("  canirunllm search <query>     search the model registry, e.g. canirunllm search qwen")
    print("  canirunllm check <model>      check one model or a whole family, e.g. canirunllm check Qwen3-8B")
    print("  canirunllm recommend          ranked list of models for your hardware")
    print()
    print("  canirunllm web                launch the dashboard on its own")
    print("  canirunllm web --port 9000    on a custom port")
    print()
    print("  canirunllm --help             show this message")
    print("  canirunllm --version          show the installed version")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print_help()
        return

    if sys.argv[1] in ("--version", "-v"):
        from canirunllm import __version__
        print(f"canirunllm {__version__} (Python {_python_version_str()} at {sys.executable})")
        return

    mismatch = find_pip_mismatch()
    if mismatch:
        print(mismatch)
        print()

    command = sys.argv[1]

    service = ScannerService()
    attempted_port = DEFAULT_PORT

    try:
        if command == "scan":

            technical = "--technical" in sys.argv[2:]
            no_browser = "--no-browser" in sys.argv[2:]

            print("CanIRunLLM")
            print()
            print("Checking your computer...")

            hardware, results = service.scan()

            print("  CPU detected")
            print("  RAM detected")

            if hardware.gpus:
                print("  GPU detected")
                print("  VRAM detected")
            else:
                print("  No dedicated GPU detected (CPU-only mode)")

            print()
            print("Analyzing local AI models...")
            print(f"  {len(results)} models analyzed")

            can_run = sum(
                1 for item in results
                if item.compatibility.overall_verdict == OverallVerdict.CAN_RUN
            )
            offload = sum(
                1 for item in results
                if item.compatibility.overall_verdict
                == OverallVerdict.CAN_RUN_WITH_OFFLOAD
            )

            print()

            if can_run:
                print(f"You can run {can_run} model(s) comfortably.")
                if offload:
                    print(f"{offload} more can run with CPU/RAM offload (slower).")
            elif offload:
                print(f"You can run {offload} model(s) with CPU/RAM offload (slower).")
            else:
                print(
                    "None of the models in this catalog currently fit "
                    "your available memory."
                )

            if not technical:
                print()
                print("Run with --technical to see the full hardware and "
                      "compatibility breakdown here in the terminal.")

            if technical:

                print()
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

                    performance = predict_performance(model, result)

                    print()
                    print(model.name)
                    print(f"  Memory:      {result.memory_verdict.value}")
                    print(f"  Strategy:    {result.memory_strategy}")
                    print(f"  Runtime:     {result.runtime_verdict.value}")
                    print(f"  Verdict:     {result.overall_verdict.value}")
                    print(f"  Confidence:  {result.confidence.value}")
                    print(f"  Performance: {format_performance(performance)}")

            if no_browser:
                return

            print()
            print("Opening your local AI report...")

            run_dashboard(port=DEFAULT_PORT)

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
                    f"{model.name:<38}"
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
                print("Run 'canirunllm search <query>' to see close matches.")
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

                performance = predict_performance(variant, result)

                print()
                print(f"Memory:       {result.memory_verdict.value}")
                print(f"Strategy:     {result.memory_strategy}")
                print(f"Runtime:      {result.runtime_verdict.value}")
                print()
                print(f"Verdict:      {result.overall_verdict.value}")
                print(f"Confidence:   {result.confidence.value}")
                print(f"Performance:  {format_performance(performance)}")
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
                performance = predict_performance(model, result)

                speed = performance.generation_speed
                speed_text = (
                    f"~{speed.low:.0f}-{speed.high:.0f} tok/s"
                    if speed is not None
                    else "n/a"
                )

                print(
                    f"{model.name:<38}"
                    f"{result.overall_verdict.value:<22}"
                    f"{speed_text:<16}"
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
                print(f"  Tier:        {entry.tier.value}")
                print(f"  Verdict:     {entry.compatibility.overall_verdict.value}")
                print(f"  Strategy:    {entry.compatibility.memory_strategy}")
                print(f"  Confidence:  {entry.compatibility.confidence.value}")
                print(f"  Performance: {format_performance(entry.performance)}")

        elif command == "web":

            attempted_port = DEFAULT_PORT

            if "--port" in sys.argv:
                port_index = sys.argv.index("--port")
                if port_index + 1 < len(sys.argv):
                    attempted_port = int(sys.argv[port_index + 1])

            print("CanIRunLLM Dashboard")

            run_dashboard(port=attempted_port)

        else:
            print(f"Unknown command: {command}")
            print("Run 'canirunllm --help' to see available commands.")

    except KeyboardInterrupt:
        print()
        print("Cancelled.")

    except OSError as exc:
        if _is_port_in_use_error(exc):
            print()
            print(f"Port {attempted_port} is already in use - is canirunllm already running?")
            print(f"Try a different port: canirunllm web --port 9000")
        else:
            _print_unexpected_error(exc)

    except Exception as exc:
        _print_unexpected_error(exc)


if __name__ == "__main__":
    main()
