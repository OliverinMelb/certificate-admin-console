"""Local-only manual UI acceptance proxy; forwards real API and static responses.

Mode file values: normal, slow-alice (2s), fail (API 503).
This is test infrastructure, never imported by the application or startup command.
"""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import time
import socket
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", default="http://127.0.0.1:8010")
    parser.add_argument("--port", type=int, default=8012)
    parser.add_argument("--mode-file", type=Path, required=True)
    args = parser.parse_args()
    if not args.upstream.startswith("http://127.0.0.1:"):
        parser.error("Only a loopback upstream is permitted")

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            return self.do_GET()

        def do_GET(self):
            mode = args.mode_file.read_text(encoding="utf-8").strip() if args.mode_file.exists() else "normal"
            actor = self.headers.get("X-Actor-Id", "")
            api = self.path.startswith("/api/")
            if api and mode == "slow-alice" and actor == "alice":
                print(f"DELAY {actor} {self.path}", flush=True)
                time.sleep(2)
            if api and mode == "fail":
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"detail":"Acceptance test: service unavailable"}')
                return
            body = self.rfile.read(int(self.headers.get("Content-Length", "0"))) if self.command == "POST" else None
            key = self.headers.get("Idempotency-Key", "")
            request = Request(args.upstream + self.path, data=body, method=self.command,
                              headers={"X-Actor-Id": actor, "Idempotency-Key": key,
                                       "Content-Type": self.headers.get("Content-Type", "application/json")})
            opener = build_opener(ProxyHandler({}))
            try:
                response = opener.open(request, timeout=10)
            except HTTPError as error:
                response = error
            with response:
                payload = response.read()
                if self.command == "POST":
                    print(f"POST {actor} {self.path} key={key} status={response.status}", flush=True)
                if mode == "drop-issue-once" and self.path.endswith("/issue") and response.status == 200:
                    args.mode_file.write_text("normal", encoding="utf-8")
                    self.close_connection = True
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                self.send_response(response.status)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/octet-stream"))
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                try:
                    self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass  # Browser canceled the superseded request.

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
