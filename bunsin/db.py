"""
분신 기억 — SQLite 큐 저장소.
외부 의존 없이 봇 옆에 bunsin.db 파일 하나로 굴러간다.
"""

import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "bunsin.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS queue (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                title     TEXT NOT NULL,
                tag       TEXT,
                reason    TEXT,
                score     REAL,
                gate_a    TEXT,
                gate_b    TEXT,
                auto      INTEGER DEFAULT 0,   -- 1이면 '자동화 먼저 깔고' 과제
                status    TEXT DEFAULT 'open', -- open | done | cut
                raw       TEXT,                -- 던진 원문 파편
                created   INTEGER
            )
            """
        )


def add(item: dict, raw: str) -> int:
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO queue (title, tag, reason, score, gate_a, gate_b, auto, status, raw, created)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                item["title"],
                item["tag"],
                item["reason"],
                item["score"],
                item["gate_a"],
                item["gate_b"],
                1 if item.get("auto") else 0,
                "cut" if item.get("cut") else "open",
                raw,
                int(time.time()),
            ),
        )
        return cur.lastrowid


def open_queue(limit: int | None = None) -> list[sqlite3.Row]:
    q = "SELECT * FROM queue WHERE status='open' ORDER BY score DESC, created ASC"
    if limit:
        q += f" LIMIT {int(limit)}"
    with _conn() as c:
        return c.execute(q).fetchall()


def top() -> sqlite3.Row | None:
    rows = open_queue(limit=1)
    return rows[0] if rows else None


def mark(item_id: int, status: str) -> bool:
    with _conn() as c:
        cur = c.execute(
            "UPDATE queue SET status=? WHERE id=?", (status, item_id)
        )
        return cur.rowcount > 0
