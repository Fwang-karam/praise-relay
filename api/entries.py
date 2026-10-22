"""칭찬 릴레이 API. Vercel에서는 이 파일의 `handler`가 /api/* 요청을 받아요."""
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _store  # noqa: E402

MAX_BODY = 8 * 1024


class handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def error(self, status, message):
        self.send_json(status, {"error": message})

    def api_path(self):
        return self.path.split("?", 1)[0].rstrip("/") == "/api/entries"

    def do_GET(self):
        if not self.api_path():
            return self.error(404, "없는 주소예요.")
        try:
            entries = _store.list_entries()
        except Exception as exc:
            print(f"list_entries 실패: {exc!r}", file=sys.stderr)
            return self.error(500, "목록을 불러오지 못했어요.")
        self.send_json(200, {"entries": entries})

    def do_POST(self):
        if not self.api_path():
            return self.error(404, "없는 주소예요.")
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self.error(400, "Content-Length가 올바르지 않아요.")
        if length > MAX_BODY:
            return self.error(413, "본문이 8KiB를 넘어요.")
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            return self.error(415, "JSON 형식으로 보내 주세요.")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self.error(400, "JSON이 깨졌어요.")
        if not isinstance(data, dict):
            return self.error(400, "JSON 객체로 보내 주세요.")

        name, message, tag = data.get("name"), data.get("message"), data.get("tag")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 40:
            return self.error(400, "칭찬하는 사람은 1~40자로 써 주세요.")
        if not isinstance(message, str) or not 1 <= len(message.strip()) <= 500:
            return self.error(400, "칭찬 한마디는 1~500자로 써 주세요.")
        if tag is not None and not isinstance(tag, str):
            return self.error(400, "칭찬 종류는 문자열이어야 해요.")

        row = {
            "id": uuid.uuid4().hex,
            "name": name.strip(),
            "message": message.strip(),
            "tag": (tag or "").strip()[:20] or None,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        try:
            entry = _store.add_entry(row)
        except Exception as exc:
            print(f"add_entry 실패: {exc!r}", file=sys.stderr)
            return self.error(500, "저장하지 못했어요. 잠시 뒤 다시 해 주세요.")
        self.send_json(201, {"entry": entry})

    def do_PUT(self):
        self.error(404, "없는 주소예요.")

    do_DELETE = do_PATCH = do_PUT
