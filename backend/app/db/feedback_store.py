"""
User Feedback Store — Phase 7
Persists user 👍 / 👎 ratings and preferences on individual stops to SQLite
and appends structured samples to backend/data/user_feedback.jsonl for LoRA fine-tuning dataset generation.
"""
from __future__ import annotations
import sqlite3
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.models.schemas import StopFeedbackRequest
from app.db.history_store import DEFAULT_DB_PATH, _get_connection

JSONL_FEEDBACK_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "user_feedback.jsonl")
)


def init_feedback_db(db_path: Optional[str] = None) -> None:
    """Initialize the feedback table in SQLite."""
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stop_feedback (
                id TEXT PRIMARY KEY,
                itinerary_id TEXT,
                stop_id TEXT NOT NULL,
                stop_name TEXT NOT NULL,
                destination TEXT NOT NULL,
                rating INTEGER NOT NULL,
                category TEXT,
                is_niche INTEGER NOT NULL,
                comment TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_feedback_dest
            ON stop_feedback (destination)
            """
        )
        conn.commit()


def record_stop_feedback(feedback: StopFeedbackRequest, db_path: Optional[str] = None) -> dict:
    """
    Save feedback to SQLite and append to user_feedback.jsonl.
    """
    init_feedback_db(db_path)
    record_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO stop_feedback (
                id, itinerary_id, stop_id, stop_name, destination, rating, category, is_niche, comment, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                feedback.itinerary_id,
                feedback.stop_id,
                feedback.stop_name,
                feedback.destination,
                feedback.rating,
                feedback.category,
                1 if feedback.is_niche else 0,
                feedback.comment,
                now_iso,
            ),
        )
        conn.commit()

    # Append to JSONL for dataset curation / fine-tuning
    try:
        os.makedirs(os.path.dirname(JSONL_FEEDBACK_PATH), exist_ok=True)
        sample = {
            "id": record_id,
            "itinerary_id": feedback.itinerary_id,
            "stop_id": feedback.stop_id,
            "stop_name": feedback.stop_name,
            "destination": feedback.destination,
            "rating": feedback.rating,
            "category": feedback.category,
            "is_niche": feedback.is_niche,
            "comment": feedback.comment,
            "timestamp": now_iso,
        }
        with open(JSONL_FEEDBACK_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[feedback_store] Warning: Failed writing to JSONL: {e}")

    return {
        "status": "success",
        "feedback_id": record_id,
        "rating": feedback.rating,
        "stop_name": feedback.stop_name,
    }
