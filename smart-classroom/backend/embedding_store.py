"""
CSTPE Embedding Store (Feature 10 - Part 1)
SQLite-backed storage of recent face embeddings per student.
Used by the Session Recovery module to re-link detections after gap events.
"""

import sqlite3
import numpy as np
import json
import os

DATA_DIR = os.getenv("DATA_DIR", "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "attendance.db")


def init_embedding_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embedding_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            embedding TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_embedding_table()


def store_embedding(student_name, embedding, timestamp_str):
    """
    Store a face embedding for a student (keep last N per student).
    """
    from policy_engine import policy
    max_embeddings = policy.get_int("max_stored_embeddings", 5)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Serialize the embedding as a JSON list of floats
    emb_json = json.dumps(embedding.tolist())

    cursor.execute(
        "INSERT INTO embedding_store (student_name, embedding, timestamp) VALUES (?, ?, ?)",
        (student_name, emb_json, timestamp_str),
    )

    # Trim old embeddings beyond the max
    cursor.execute("""
        DELETE FROM embedding_store
        WHERE id NOT IN (
            SELECT id FROM embedding_store
            WHERE student_name = ?
            ORDER BY id DESC
            LIMIT ?
        ) AND student_name = ?
    """, (student_name, max_embeddings, student_name))

    conn.commit()
    conn.close()


def get_recent_embeddings(student_name, limit=5):
    """
    Retrieve the most recent face embeddings for a student.
    Returns a list of numpy arrays.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT embedding FROM embedding_store WHERE student_name = ? ORDER BY id DESC LIMIT ?",
        (student_name, limit),
    )
    rows = cursor.fetchall()
    conn.close()

    embeddings = []
    for row in rows:
        arr = np.array(json.loads(row[0]))
        embeddings.append(arr)

    return embeddings


def get_all_recent_embeddings(limit_per_student=5):
    """
    Retrieve all students' recent embeddings.
    Returns {student_name: [embedding1, embedding2, ...]}.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT student_name FROM embedding_store")
    students = [row[0] for row in cursor.fetchall()]
    conn.close()

    result = {}
    for name in students:
        result[name] = get_recent_embeddings(name, limit_per_student)

    return result
