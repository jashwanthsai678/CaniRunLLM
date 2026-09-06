import sys

__version__ = "0.1.0"

if sys.version_info < (3, 10):
    raise RuntimeError(
        "CanIRunLLM requires Python 3.10 or newer "
        f"(you're running {sys.version_info.major}.{sys.version_info.minor}).\n\n"
        "If you have multiple Python versions installed on Windows, "
        "your 'python'/'pip' commands may be pointing at an older one. "
        "Check what's installed with:\n"
        "    py -0\n"
        "Then install using a specific newer version, e.g.:\n"
        "    py -3.11 -m pip install canirunllm\n"
        "    py -3.11 -m canirunllm.cli scan"
    )
