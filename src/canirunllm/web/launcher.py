import threading
import time
import webbrowser

import uvicorn

from canirunllm.api.server import app


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def open_browser_later(url: str, delay: float = 1.0) -> None:
    """Open the browser shortly after the caller starts the server.

    Runs on a background thread so the caller can immediately start
    a blocking server (e.g. uvicorn.run) without the browser trying
    to connect before the server is listening.
    """

    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_open, daemon=True).start()


def run_dashboard(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    open_browser: bool = True,
) -> None:

    url = f"http://{host}:{port}"

    print()
    print("Dashboard:")
    print(f"  {url}")

    if open_browser:
        print()
        print("Opening browser...")
        open_browser_later(url)

    uvicorn.run(app, host=host, port=port, log_level="warning")
