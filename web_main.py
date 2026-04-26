import os
import sys
import traceback


def _setup_logging():
    """In PyInstaller console=True mode, keep stdout/stderr as-is.
    Only redirect to devnull if they are mysteriously None."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


if __name__ == "__main__":
    _setup_logging()

    try:
        import server.app  # ensure PyInstaller collects the server package
        import uvicorn
        import webbrowser
        import threading

        port = int(os.environ.get("PORT", 8099))
        url = f"http://127.0.0.1:{port}"

        print(f"SRT-SUMMARIZER v2.0  starting on {url}")
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()

        uvicorn.run(
            "server.app:create_app",
            host="127.0.0.1",
            port=port,
            reload=False,
            factory=True,
            log_level="info",
        )
    except Exception:
        traceback.print_exc()
        print("\nPress Ctrl+C or close this window to exit.")
        import time
        time.sleep(300)
