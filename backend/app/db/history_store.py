"""
Trip History Store — Phase 4f
Persists generated itineraries to a local SQLite database (backend/data/trip_history.db).
Supports saving, retrieving lightweight metadata summaries, loading full itinerary JSON, and deletion.
"""
from __future__ import annotations
import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import Optional, Any

from app.models.schemas import Itinerary

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "trip_history.db")
)


def _get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the SQLite database and create trip_history table if needed."""
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trip_history (
                id TEXT PRIMARY KEY,
                destination TEXT NOT NULL,
                num_days INTEGER NOT NULL,
                total_cost_usd REAL,
                cover_image_url TEXT,
                created_at TEXT NOT NULL,
                itinerary_json TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_trip_history_created_at 
            ON trip_history (created_at DESC)
            """
        )
        conn.commit()


# Auto-initialize DB on import
init_db()


def save_itinerary(
    itinerary: Itinerary,
    db_path: Optional[str] = None,
    max_history_limit: int = 50,
) -> dict[str, Any]:
    """
    Upsert an itinerary into the SQLite database.
    Retains up to max_history_limit items, pruning oldest beyond that limit.
    Returns metadata dict of the saved record.
    """
    init_db(db_path)
    
    trip_id = str(itinerary.id)
    destination = itinerary.trip_request.destination if itinerary.trip_request else "Unknown Destination"
    num_days = len(itinerary.days) if itinerary.days else (itinerary.trip_request.num_days if itinerary.trip_request else 1)
    total_cost_usd = float(itinerary.total_cost_estimate_usd) if itinerary.total_cost_estimate_usd is not None else 0.0
    cover_image_url = itinerary.cover_image_url or (itinerary.days[0].cover_image_url if itinerary.days else None)
    created_at = datetime.now(timezone.utc).isoformat()
    itinerary_json = itinerary.model_dump_json()

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO trip_history (
                id, destination, num_days, total_cost_usd, cover_image_url, created_at, itinerary_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trip_id,
                destination,
                num_days,
                total_cost_usd,
                cover_image_url,
                created_at,
                itinerary_json,
            ),
        )

        # Enforce max limit by pruning oldest
        cursor.execute(
            """
            DELETE FROM trip_history
            WHERE id NOT IN (
                SELECT id FROM trip_history
                ORDER BY created_at DESC
                LIMIT ?
            )
            """,
            (max_history_limit,),
        )
        conn.commit()

    return {
        "id": trip_id,
        "destination": destination,
        "num_days": num_days,
        "total_cost_usd": total_cost_usd,
        "cover_image_url": cover_image_url,
        "created_at": created_at,
    }


def get_all_histories(
    limit: int = 50,
    db_path: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve lightweight summaries of saved trips for the sidebar / history panel.
    Omits full itinerary_json for performance.
    """
    init_db(db_path)
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, destination, num_days, total_cost_usd, cover_image_url, created_at
            FROM trip_history
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_itinerary_by_id(
    itinerary_id: str,
    db_path: Optional[str] = None,
) -> Optional[Itinerary]:
    """Retrieve full Itinerary object by its UUID / id."""
    init_db(db_path)
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT itinerary_json FROM trip_history WHERE id = ?",
            (str(itinerary_id),),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Itinerary.model_validate_json(row["itinerary_json"])


def delete_itinerary(
    itinerary_id: str,
    db_path: Optional[str] = None,
) -> bool:
    """Delete a saved itinerary record by id. Returns True if deleted."""
    init_db(db_path)
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trip_history WHERE id = ?", (str(itinerary_id),))
        conn.commit()
        return cursor.rowcount > 0
