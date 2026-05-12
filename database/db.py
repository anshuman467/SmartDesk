import sqlite3
from pathlib import Path
from typing import Iterable, Optional, TypedDict

import pandas as pd

from core.schema import RECORD_COLUMNS


DB_PATH = Path(__file__).resolve().parent / "investigation.db"


RECORD_TABLE_SQL_COLUMNS = {
    "source_file": "TEXT",
    "file_type": "TEXT",
    "phone_number": "TEXT",
    "other_party_number": "TEXT",
    "imei": "TEXT",
    "imsi": "TEXT",
    "source_ip": "TEXT",
    "destination_ip": "TEXT",
    "source_port": "REAL",
    "destination_port": "REAL",
    "protocol": "TEXT",
    "domain": "TEXT",
    "service_provider": "TEXT",
    "tower_id": "TEXT",
    "tower_location": "TEXT",
    "tower_latitude": "REAL",
    "tower_longitude": "REAL",
    "mcc": "REAL",
    "mnc": "REAL",
    "lac": "REAL",
    "cellid": "REAL",
    "tac": "REAL",
    "radio": "TEXT",
    "approx_radius_meters": "REAL",
    "date_time": "TEXT",
    "duration": "REAL",
    "bytes_used": "REAL",
    "call_type": "TEXT",
    "service_name": "TEXT",
}


class CaseSummary(TypedDict):
    files: int
    records: int
    unique_numbers: int
    unique_towers: int


class UserRecord(TypedDict):
    id: int
    full_name: str
    email: str


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_database() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            file_type TEXT,
            phone_number TEXT,
            other_party_number TEXT,
            imei TEXT,
            imsi TEXT,
            source_ip TEXT,
            destination_ip TEXT,
            source_port REAL,
            destination_port REAL,
            protocol TEXT,
            domain TEXT,
            service_provider TEXT,
            tower_id TEXT,
            tower_location TEXT,
            tower_latitude REAL,
            tower_longitude REAL,
            date_time TEXT,
            duration REAL,
            bytes_used REAL,
            call_type TEXT,
            service_name TEXT
        )
        """
    )
    existing_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(records)").fetchall()
    }
    for column_name, column_type in RECORD_TABLE_SQL_COLUMNS.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE records ADD COLUMN {column_name} {column_type}")
    conn.commit()
    conn.close()


def insert_records(file_name: str, file_type: str, df: pd.DataFrame) -> int:
    ensure_database()
    working = df.copy()
    for col in RECORD_COLUMNS:
        if col not in working.columns:
            working[col] = pd.NA
    working = working[RECORD_COLUMNS]
    working["source_file"] = file_name
    working["file_type"] = file_type
    working = working.where(pd.notnull(working), None)

    conn = get_connection()
    conn.execute(
        "INSERT INTO uploaded_files (file_name, file_type, record_count) VALUES (?, ?, ?)",
        (file_name, file_type, len(working)),
    )
    working.to_sql("records", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()
    return len(working)


def fetch_records(where_clause: str = "", params: Iterable = ()) -> pd.DataFrame:
    ensure_database()
    query = "SELECT * FROM records"
    if where_clause:
        query = f"{query} WHERE {where_clause}"
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    if "date_time" in df.columns:
        df["date_time"] = pd.to_datetime(df["date_time"], errors="coerce")
    return df


def fetch_uploaded_files() -> pd.DataFrame:
    ensure_database()
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, file_name, file_type, record_count, uploaded_at FROM uploaded_files ORDER BY id DESC",
        conn,
    )
    conn.close()
    return df


def get_case_summary() -> CaseSummary:
    ensure_database()
    conn = get_connection()
    summary: CaseSummary = {
        "files": int(conn.execute("SELECT COUNT(*) FROM uploaded_files").fetchone()[0]),
        "records": int(conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]),
        "unique_numbers": int(
            conn.execute(
            "SELECT COUNT(DISTINCT phone_number) FROM records WHERE phone_number IS NOT NULL"
        ).fetchone()[0]
        ),
        "unique_towers": int(
            conn.execute(
            "SELECT COUNT(DISTINCT tower_id) FROM records WHERE tower_id IS NOT NULL"
        ).fetchone()[0]
        ),
    }
    conn.close()
    return summary


def clear_database() -> None:
    ensure_database()
    conn = get_connection()
    conn.execute("DELETE FROM uploaded_files")
    conn.execute("DELETE FROM records")
    conn.commit()
    conn.close()


def create_user(full_name: str, email: str, password_hash: str) -> bool:
    ensure_database()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
            (full_name.strip(), email.strip().lower(), password_hash),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    ensure_database()
    conn = get_connection()
    row = conn.execute(
        "SELECT id, full_name, email, password_hash FROM users WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    conn.close()
    return row


def authenticate_user(email: str, password_hash: str) -> Optional[UserRecord]:
    user = get_user_by_email(email)
    if not user or user["password_hash"] != password_hash:
        return None
    return {
        "id": int(user["id"]),
        "full_name": str(user["full_name"]),
        "email": str(user["email"]),
    }
