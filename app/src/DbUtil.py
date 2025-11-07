from __future__ import annotations
import json
import sqlite3
from typing import Any, Optional

class DbUtil:
    def __init__(
        self,
        db_path: str="app/detections.db"
    ) -> None:
        self.db_path: str = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT,
                detection_data TEXT
            )
        """)
        conn.commit()
        conn.close()

    def insert_detection(
        self,
        image_path: str,
        detection_data: str
    ) -> int:
        """Insert a detection and return its database ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO detections (image_path, detection_data) VALUES (?, ?)",
            (image_path, detection_data),
        )
        conn.commit()
        detection_id: int = cursor.lastrowid
        conn.close()
        return detection_id
    
    def get_all_detections(self) -> list[dict[str, Any]]:
        """Retrieves the entire contents of the database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor
        cursor.execute("SELECT * FROM detections")
        detections = [dict[row] for row in cursor.fetchall()]
        conn.close()
        return detections

    def get_detection_by_id(
        self,
        detection_id: int
    ) -> Optional[dict[str,Any]]:
        """Retreaves detection based on id."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM detection WHERE id = ?",
            (detection_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None