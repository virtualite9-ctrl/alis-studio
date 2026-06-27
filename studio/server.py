"""Alis Studio — local HTTP server.

Dependency-free (Python standard library): serves web/index.html, exposes the registered
models at /api/models, and streams generation progress as NDJSON from /api/generate. Binds to
127.0.0.1 by default — set ALIS_HOST=0.0.0.0 to expose on your LAN, ALIS_PORT to change the port.
"""

from __future__ import annotations

import base64
import io
import json
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .registry import Registry

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB = os.path.join(ROOT, "web")
HOST = os.environ.get("ALIS_HOST", "127.0.0.1")
PORT = int(os.environ.get("ALIS_PORT") or os.environ.get("PORT") or "7860")

_REGISTRY: Registry | None = None
_LOCK = threading.Lock()  # one GPU — serialize generation


def _registry() -> Registry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = Registry()
    return _REGISTRY


def _png_datauri(im) -> str:
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _apply_safety(images, enabled):
    """App-level NSFW filter (reuses krea2's pure-MLX classifier). Passes through if unavailable."""
    if not enabled:
        return images, 0
    try:
        from krea2 import safety
        return safety.apply(images, enabled=True)
    except Exception:
        return list(images), 0


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body=b""):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if body:
            self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB, "index.html"), "rb") as f:
                    self._send(200, "text/html; charset=utf-8", f.read())
            except OSError:
                self._send(500, "text/plain", b"web/index.html is missing")
        elif path == "/api/models":
            self._send(200, "application/json", json.dumps({"backends": _registry().models()}).encode())
        elif path == "/favicon.ico":
            self._send(204, "text/plain")
        else:
            self._send(404, "text/plain", b"not found")

    def do_POST(self):
        if self.path != "/api/generate":
            self._send(404, "text/plain", b"not found")
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._send(400, "text/plain", b"bad request")
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def emit(obj):
            self.wfile.write((json.dumps(obj) + "\n").encode())
            self.wfile.flush()

        with _LOCK:
            try:
                backend, variant = _registry().resolve(req.get("model", ""))
                size = int(req.get("size", backend.default_size))
                steps = int(req.get("steps", backend.default_steps))
                seed = int(req.get("seed", 0))
                t0 = time.time()
                imgs = backend.generate(
                    prompt=str(req.get("prompt", "")), variant=variant, width=size, height=size,
                    steps=steps, seed=seed, num_images=int(req.get("num_images", 1)),
                    step_callback=lambda s, total: emit({"type": "step", "step": s, "total": total}),
                )
                imgs, flagged = _apply_safety(imgs, req.get("safety", True))
                emit({"type": "done", "flagged": flagged,
                      "images": [_png_datauri(im) for im in imgs],
                      "meta": {"model": backend.label, "size": size, "steps": steps,
                               "seed": seed, "seconds": round(time.time() - t0, 1)}})
            except ValueError as e:
                emit({"type": "error", "message": str(e)})
            except Exception as e:
                m = str(e).lower()
                if any(k in m for k in ("memory", "alloc", "metal")):
                    emit({"type": "error", "message": "Out of memory — try a smaller size, fewer "
                          "images, or a lighter model build."})
                else:
                    emit({"type": "error", "message": f"Generation failed: {e}"})


def serve():
    _registry()  # build the registry up front so /api/models is ready and startup fails loudly
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{'localhost' if HOST in ('127.0.0.1', '0.0.0.0') else HOST}:{PORT}"
    print(f"Alis Studio  →  {url}")
    print("First run downloads the model (a few minutes). Press Ctrl+C to stop.")
    if HOST in ("127.0.0.1", "0.0.0.0"):
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
        server.shutdown()
