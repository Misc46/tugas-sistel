"""Zero-dependency local HTTP server for the Paraphraser web app."""
from __future__ import annotations

import json
import mimetypes
import os
import random
import socket
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .metrics import compute_text_metrics
from .pipeline import paraphrase_text
from .ranker import DEFAULT_MODEL, Ranker

# Find workspace root where app.html lives
PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent.parent


def find_app_html() -> Path | None:
    candidates = [
        REPO_ROOT / "app.html",
        PACKAGE_DIR.parent / "app.html",
        PACKAGE_DIR / "app.html",
        Path.cwd() / "app.html",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


class ParaphraserHandler(BaseHTTPRequestHandler):
    ranker: Ranker | None = None

    def log_message(self, format: str, *args) -> None:
        """Route access logs to stdout (info) and errors to stderr to avoid red false-alarm terminal highlights."""
        status_str = str(args[1]) if len(args) > 1 else ""
        req_str = str(args[0]) if len(args) > 0 else ""
        msg = f"[server] {req_str} -> {status_str}\n"
        try:
            code = int(status_str)
        except ValueError:
            code = 200

        if code >= 400:
            sys.stderr.write(msg)
            sys.stderr.flush()
        else:
            sys.stdout.write(msg)
            sys.stdout.flush()

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self._send_cors_headers()
            self.end_headers()
            return

        if path in ("", "/", "/index.html", "/app.html"):
            app_file = find_app_html()
            if app_file and app_file.is_file():
                content = app_file.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "app.html not found"})
            return

        if path == "/api/health":
            ranker = self.ranker or getattr(self.server, "ranker", None)
            is_lm = ranker.available if ranker else False
            model_id = ranker.model_id if ranker else DEFAULT_MODEL
            self._send_json(HTTPStatus.OK, {
                "status": "ok",
                "lm_available": is_lm,
                "model": model_id,
                "supported_languages": ["id", "en"],
            })
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Endpoint not found: {path}"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Empty request body"})
            return

        try:
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"Invalid JSON payload: {e}"})
            return

        if path == "/api/metrics":
            text = payload.get("text", "")
            metrics = compute_text_metrics(text)
            self._send_json(HTTPStatus.OK, {"metrics": metrics})
            return

        if path == "/api/paraphrase":
            text = payload.get("text", "")
            if not text or not text.strip():
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Text cannot be empty"})
                return

            lang = str(payload.get("lang", "id")).lower()
            if lang not in ("id", "en"):
                lang = "id"

            try:
                density = float(payload.get("density", 0.35))
                density = max(0.05, min(0.9, density))
            except (ValueError, TypeError):
                density = 0.35

            try:
                novelty = int(payload.get("novelty", 3))
                novelty = max(1, min(10, novelty))
            except (ValueError, TypeError):
                novelty = 3

            seed = payload.get("seed")
            if seed is None or seed == "":
                seed = random.randint(1, 999999)
            else:
                try:
                    seed = int(seed)
                except (ValueError, TypeError):
                    seed = random.randint(1, 999999)

            is_tex = bool(payload.get("is_tex", True))

            ranker = self.ranker or getattr(self.server, "ranker", None)
            if ranker is None:
                ranker = Ranker.__new__(Ranker)
                ranker.model = None
                ranker.tok = None

            rng = random.Random(seed)
            stats = {
                "prose_lines": 0,
                "changed_lines": 0,
                "replacements": 0,
                "splits": 0,
                "connectors": 0,
                "openers": 0,
                "merges": 0,
                "enumerations": 0,
            }

            before_metrics = compute_text_metrics(text)
            paraphrased, stats, diff_items = paraphrase_text(
                text=text,
                rng=rng,
                ranker=ranker,
                density=density,
                stats=stats,
                novelty=novelty,
                lang=lang,
                is_tex=is_tex,
            )
            after_metrics = compute_text_metrics(paraphrased)

            improvement = 0.0
            if before_metrics["burstiness"] > 0:
                improvement = round(
                    ((after_metrics["burstiness"] - before_metrics["burstiness"]) / before_metrics["burstiness"]) * 100,
                    1,
                )

            self._send_json(HTTPStatus.OK, {
                "paraphrased": paraphrased,
                "stats": stats,
                "metrics": {
                    "before": before_metrics,
                    "after": after_metrics,
                    "improvement_pct": improvement,
                },
                "diff": diff_items,
                "config": {
                    "lang": lang,
                    "density": density,
                    "novelty": novelty,
                    "seed": seed,
                    "is_tex": is_tex,
                },
            })
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Endpoint not found: {path}"})


def find_free_port(start_port: int = 8000, max_attempts: int = 50) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            res = sock.connect_ex(("127.0.0.1", port))
            if res != 0:
                return port
    return start_port


def run_server(
    port: int = 8000,
    model_id: str = DEFAULT_MODEL,
    open_browser: bool = True,
    use_lm: bool = True,
) -> None:
    chosen_port = find_free_port(port)
    server_address = ("127.0.0.1", chosen_port)

    print("=" * 64)
    if use_lm:
        print(f"Initializing Paraphraser Engine (model={model_id})...")
        ranker = Ranker(model_id)
        if ranker.available:
            print("[engine] XLM-RoBERTa ranker ready.")
        else:
            print("[engine] Running in lightweight mode (random candidate selection).")
    else:
        ranker = Ranker.__new__(Ranker)
        ranker.model = None
        ranker.tok = None
        ranker.model_id = "offline-rules"
        print("[engine] Running in fast lightweight mode (rule-based candidate selection).")
    print("=" * 64)

    httpd = ThreadingHTTPServer(server_address, ParaphraserHandler)
    httpd.ranker = ranker  # type: ignore[attr-defined]

    url = f"http://127.0.0.1:{chosen_port}"
    print(f"\n[server] Running at: {url}")
    print(f"[server] Serving: {find_app_html() or 'app.html'}")
    print("[server] Press Ctrl+C to stop the server.\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] Shutting down...")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    use_lm = "--no-lm" not in sys.argv and "--fast" not in sys.argv
    run_server(use_lm=use_lm)

