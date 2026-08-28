import sqlite3
import re
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from prometheus_client import Counter, generate_latest

app = FastAPI(title="Door Code Distributor")

DOOR_CODE_SUCCESS = Counter("get_door_code_success_total", "Successful door code distributions")
DOOR_CODE_FAILURE = Counter("get_door_code_failure_total", "Failed door code distributions")

DB_PATH = Path("/app/data/codes.db")


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=wal")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                use_count INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()


init_db()

CODE_PATTERN = re.compile(r"^\d{3}-\d{4}$")


class IngestRequest(BaseModel):
    codes: str  # newline-separated codes


class IngestResponse(BaseModel):
    added: int
    duplicates: int
    invalid: list[str]


class DoorCodeResponse(BaseModel):
    code: str


@app.post("/ingestCodes", response_model=IngestResponse)
def ingest_codes(req: IngestRequest):
    lines = [line.strip() for line in req.codes.splitlines() if line.strip()]
    added = 0
    duplicates = 0
    invalid = []

    with get_db() as conn:
        for line in lines:
            if not CODE_PATTERN.match(line):
                invalid.append(line)
                continue
            try:
                conn.execute("INSERT INTO codes (code) VALUES (?)", (line,))
                added += 1
            except sqlite3.IntegrityError:
                duplicates += 1
        conn.commit()

    return IngestResponse(added=added, duplicates=duplicates, invalid=invalid)


@app.get("/getDoorCode", response_model=DoorCodeResponse)
def get_door_code():
    with get_db() as conn:
        row = conn.execute(
            """
            UPDATE codes SET use_count = use_count + 1
            WHERE id = (
                SELECT id FROM codes
                WHERE use_count = (SELECT MIN(use_count) FROM codes)
                ORDER BY RANDOM()
                LIMIT 1
            )
            RETURNING code
            """
        ).fetchone()
        conn.commit()

        if row is None:
            DOOR_CODE_FAILURE.inc()
            raise HTTPException(status_code=404, detail="No codes available")

    DOOR_CODE_SUCCESS.inc()
    return DoorCodeResponse(code=row[0])


@app.delete("/clearCodes")
def clear_all_codes():
    with get_db() as conn:
        result = conn.execute("DELETE FROM codes")
        conn.commit()

    return {"deleted": result.rowcount}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
