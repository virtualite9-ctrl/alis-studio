"""Alis Studio as a native desktop window (pywebview → WKWebView on macOS).

Same local server as the web app, but in its own native window instead of a browser tab —
real title bar, dock icon, and menu, with no browser or Chromium bundle. Install the desktop
extra: `python3 -m pip install pywebview` (it pulls the macOS WebKit backend).
"""

from __future__ import annotations

import os

from . import __version__
from .server import start_http


def main():
    import webview

    # bind a free loopback port (or honor ALIS_PORT) and run the server in a background thread
    port = int(os.environ.get("ALIS_PORT") or 0)
    server, port = start_http("127.0.0.1", port)
    webview.create_window(
        f"Alis Studio {__version__}", f"http://127.0.0.1:{port}/",
        width=1120, height=860, min_size=(840, 600),
    )
    try:
        webview.start()  # runs the native UI loop on the main thread; blocks until the window closes
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
