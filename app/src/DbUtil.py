from __future__ import annotations
import sqlite3
import json
from typing import Any, Optional

class DbUtil:
    """SQLite utility class with strict schema and controlled queries."""

    # === Database schema definition ===
    DB_PATH: str = "app/detections.db"
    TABLE_NAME: str = "detections"

    # Column names (define once, used everywhere)
    COL_ID: str = "id"
    COL_IMAGE_PATH: str = "image_path"
    COL_DETECTION_DATA: str = "detection_data"

    # SQL statements (centralized to avoid typos)
    SQL_CREATE_TABLE: str = f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            {COL_ID} INTEGER PRIMARY KEY AUTOINCREMENT,
            {COL_IMAGE_PATH} TEXT NOT NULL,
            {COL_DETECTION_DATA} TEXT NOT NULL
        )
    """

    SQL_INSERT: str = f"""
        INSERT INTO {TABLE_NAME} ({COL_IMAGE_PATH}, {COL_DETECTION_DATA})
        VALUES (?, ?)
    """

    SQL_SELECT_ALL: str = f"""
        SELECT {COL_ID}, {COL_IMAGE_PATH}, {COL_DETECTION_DATA}
        FROM {TABLE_NAME}
    """

    SQL_SELECT_BY_ID: str = f"""
        SELECT {COL_ID}, {COL_IMAGE_PATH}, {COL_DETECTION_DATA}
        FROM {TABLE_NAME}
        WHERE {COL_ID} = ?
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or self.DB_PATH
        self._init_db()

    # === Internal helpers ===
    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(self.SQL_CREATE_TABLE)
            conn.commit()

    # === CRUD operations ===
    def insert_detection(
        self,
        image_path: str,
        detection_data: dict[str, Any]
    ) -> int:
        """Insert a detection record and return its database ID."""
        detection_json = json.dumps(detection_data)
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(self.SQL_INSERT, (image_path, detection_json))
            conn.commit()
            return cursor.lastrowid

    def get_all_detections(self) -> list[dict[str, Any]]:
        """Return all detection records."""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(self.SQL_SELECT_ALL)
            return [dict(row) for row in cursor.fetchall()]

    def get_detection_by_id(self, detection_id: int) -> Optional[dict[str, Any]]:
        """Return a single detection record by ID, or None if not found."""
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(self.SQL_SELECT_BY_ID, (detection_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
