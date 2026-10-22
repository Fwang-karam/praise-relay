"""로컬 개발용 서버: index.html을 보여 주고 /api/*는 api/entries.py에 넘겨요."""
import os
import sys
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "api"))
from entries import handler as ApiHandler  # noqa: E402

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8080"))
INDEX_PATH = os.path.join(ROOT, "index.html")


class Handler(ApiHandler):
    def do_GET(self):
        if self.path.split("?", 1)[0] in ("/", "/index.html"):
            with open(INDEX_PATH, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()


if __name__ == "__main__":
    print(f"칭찬 릴레이: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
