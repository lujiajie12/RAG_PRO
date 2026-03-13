from __future__ import annotations

import argparse
import posixpath
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


class SPARequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, **kwargs):
        self._spa_root = Path(directory).resolve()
        super().__init__(*args, directory=str(self._spa_root), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        requested = self._resolve_request_path(parsed.path)

        if requested.is_file():
            return super().do_GET()

        self.path = "/index.html"
        return super().do_GET()

    def _resolve_request_path(self, raw_path: str) -> Path:
        normalized = posixpath.normpath(unquote(raw_path))
        parts = [part for part in normalized.split("/") if part and part != ".."]
        return self._spa_root.joinpath(*parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve a Vite dist directory with SPA fallback.")
    parser.add_argument("--root", required=True, help="Path to frontend dist directory")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5173)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"Dist directory not found: {root}")

    def handler(*handler_args, **handler_kwargs):
        return SPARequestHandler(*handler_args, directory=str(root), **handler_kwargs)

    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {root} at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
