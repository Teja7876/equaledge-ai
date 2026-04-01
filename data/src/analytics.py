import sqlite3
import hashlib
from datetime import datetime

DB_PATH = "analytics.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            question_hash TEXT,
            provider TEXT,
            confidence TEXT,
            response_time REAL,
            citation TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def log_query(question, provider, confidence, response_time, citation):

    question_hash = hashlib.sha256(
        question.lower().strip().encode()
    ).hexdigest()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO query_logs (
            question,
            question_hash,
            provider,
            confidence,
            response_time,
            citation,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        question,
        question_hash,
        provider,
        confidence,
        response_time,
        citation,
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()
