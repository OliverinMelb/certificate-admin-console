"""Run Uvicorn with a lifetime bounded by the launcher's stdin pipe."""

import argparse
import os
import sys
import threading

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = uvicorn.Server(uvicorn.Config(
        "app.main:create_app", factory=True, host="127.0.0.1", port=args.port,
    ))

    def watch_launcher() -> None:
        # The launcher never sends data. EOF also occurs if it is forcibly killed.
        # Avoid holding BufferedReader's lock during interpreter shutdown on bind failure.
        while os.read(sys.stdin.fileno(), 1):
            pass
        server.should_exit = True

    if not sys.stdin.isatty():
        threading.Thread(target=watch_launcher, daemon=True).start()
    try:
        server.run()
    except KeyboardInterrupt:
        # Uvicorn has already shut down; Ctrl+C is a normal user action.
        pass


if __name__ == "__main__":
    main()
