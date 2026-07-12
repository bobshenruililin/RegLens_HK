#!/usr/bin/env python3
"""Static file server that prefers index.html for directories (no listings)."""

from __future__ import annotations

import argparse
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class IndexHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs):
        self._root = Path(directory or os.getcwd()).resolve()
        super().__init__(*args, directory=str(self._root), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        raw = self.path.split("?", 1)[0]
        translated = Path(self.translate_path(raw))
        if translated.is_dir():
            index = translated / "index.html"
            if index.is_file():
                rel = index.relative_to(self._root).as_posix()
                self.path = "/" + rel
            else:
                self.send_error(404, "Directory listing disabled")
                return
        return SimpleHTTPRequestHandler.do_GET(self)

    def list_directory(self, path: str):  # type: ignore[override]
        self.send_error(404, "Directory listing disabled")
        return None

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"{self.address_string()} - {fmt % args}\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dir", type=Path, default=Path("apps/lawtrace/out"))
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=3010)
    args = ap.parse_args()
    root = args.dir.resolve()
    if not root.is_dir():
        raise SystemExit(
            f"Missing build output at {root}. Run: make lawtrace-build "
            "(or make lawtrace-web-data-local && cd apps/lawtrace && npm run build)"
        )
    if not (root / "index.html").is_file():
        raise SystemExit(f"No index.html in {root}; production build incomplete.")

    handler = lambda *a, **k: IndexHandler(*a, directory=str(root), **k)  # noqa: E731
    httpd = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{args.port}/"
    print(f"LawTrace preview: {url}", flush=True)
    print(f"Serving {root} (index.html preferred; listings disabled)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
