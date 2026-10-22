"""저장소: SUPABASE_URL이 있으면 Supabase(REST), 없으면 로컬 SQLite를 써요."""
import json
import os
import sqlite3
import urllib.error
import urllib.request

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "praise.db")


def _utc_z(value):
    return value.replace("+00:00", "Z") if isinstance(value, str) else value


def to_entry(row):
    entry = {
        "id": row["id"],
        "name": row["name"],
        "message": row["message"],
        "created_at": _utc_z(row["created_at"]),
    }
    if row["tag"]:
        entry["tag"] = row["tag"]
    return entry


# ---- Supabase ----

def _supabase(method, query, payload=None):
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/entries{query}",
        method=method,
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode("utf-8"))


# ---- SQLite ----

def _sqlite():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS entries (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            message TEXT NOT NULL,
            tag TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    return conn


def list_entries(limit=200):
    if SUPABASE_URL:
        rows = _supabase("GET", f"?select=id,name,message,tag,created_at&order=seq.desc&limit={limit}")
    else:
        with _sqlite() as conn:
            rows = conn.execute(
                "SELECT * FROM entries ORDER BY seq DESC LIMIT ?", (limit,)
            ).fetchall()
    return [to_entry(r) for r in rows]


def add_entry(row):
    if SUPABASE_URL:
        _supabase("POST", "", row)
    else:
        with _sqlite() as conn:
            conn.execute(
                "INSERT INTO entries (id, name, message, tag, created_at) "
                "VALUES (:id, :name, :message, :tag, :created_at)",
                row,
            )
    return to_entry(row)
