from __future__ import annotations
from typing import Any, Optional, List
import json
import time
import sqlite3
import threading
from src.util import logger
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from src.config import settings
from psycopg2 import OperationalError

class BaseDb:
    """Base class storing common SQL strings and helper logic."""

    COL_ID = "id"
    COL_IMAGE_PATH = "image_path"
    COL_DETECTION_DATA = "detection_data"
    COL_CREATED_AT = "created_at"
    COL_SYNCED = "synced"

    SQL_INSERT = (
        "INSERT INTO {table} ({image_col}, {data_col}, {ts_col}) "
        "VALUES (%s, %s, %s) RETURNING id"
    )
    SQL_SELECT_BY_ID = "SELECT * FROM {table} WHERE id=%s"
    SQL_SELECT_ALL = "SELECT * FROM {table}"
    SQL_SELECT_RECENT = "SELECT * FROM {table} ORDER BY {ts_col} DESC LIMIT %s"

    def _format_query(self, sql: str, table: str) -> str:
        """Format SQL string with actual table/column names."""
        return sql.format(
            table=table,
            image_col=self.COL_IMAGE_PATH,
            data_col=self.COL_DETECTION_DATA,
            ts_col=self.COL_CREATED_AT
        )

    def insert_detection(
        self,
        image_path: str,
        detection_data: dict[str, Any]
    ) -> int:
        """Insert detection - implemented by subclasses."""
        raise NotImplementedError()

    def get_detection_by_id(
        self,
        detection_id: int
    ) -> Optional[dict[str, Any]]:
        """Get detection by ID - implemented by subclasses."""
        raise NotImplementedError()
    
    def get_recent(self, limit: int = 10) -> List[dict[str, Any]]:
        raise NotImplementedError()


class SqliteDb(BaseDb):
    """Two-table SQLite cache mirroring Postgres: frame + detection."""

    SQL_CREATE_FRAME = """
    CREATE TABLE IF NOT EXISTS frame (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_path TEXT NOT NULL,
        camera_id TEXT,
        model_name TEXT,
        created_at INTEGER NOT NULL
    );
    """

    SQL_CREATE_DETECTION = """
    CREATE TABLE IF NOT EXISTS detection (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        frame_id INTEGER NOT NULL REFERENCES frame(id) ON DELETE CASCADE,
        class_name TEXT NOT NULL,
        confidence REAL NOT NULL,
        bbox TEXT NOT NULL,      -- store as JSON string
        attributes TEXT,         -- optional JSON metadata
        created_at INTEGER NOT NULL
    );
    """

    SQL_INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_frame_created_at ON frame(created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_detection_class ON detection(class_name);",
        "CREATE INDEX IF NOT EXISTS idx_detection_frame ON detection(frame_id);",
    ]
    def __init__(
        self,
        db_path: str = settings.CACHE_DB_PATH
    ):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute(self.SQL_CREATE_FRAME)
            conn.execute(self.SQL_CREATE_DETECTION)
            for idx in self.SQL_INDEXES:
                conn.execute(idx)
            conn.commit()
        logger.infor("SQLite: Cache schema initialized.")

    def insert_frame(
        self,
        image_path: str,
        camera_id: str = None,
        model_name: str = None,
        ts: Optional[int] = None
    ) -> int:
        ts = ts or int(time.time())
        with self._get_conn() as conn:
            cursor.conn.execute(
                """
                INSERT INTO frame (
                    image_path,
                    camera_id,
                    model_name,
                    created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    image_path,
                    camera_id,
                    model_name,
                    ts
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_frames(self, limit: int = 20) -> List[dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM frame ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def insert_detection(
        self,
        frame_id: int,
        class_name: str,
        confidence: float,
        bbox: dict,
        attrs: dict = None,
        ts: Optional[int] = None
    ) -> int:
        ts = ts or int(time.time())
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO detection (
                    frame_id,
                    class_name,
                    confidence,
                    bbox,
                    attributes,
                    created_at,
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    frame_id,
                    class_name,
                    confidence,
                    json.dumps(bbox),
                    json.dumps(attrs or {}),
                    ts
                )
            )
            conn.commit()
            return cursor.lastrowid

    def get_detection_for_frame(self, frame_id: int) -> List[dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM detection WHERE frame_id=? ORDER BY id ASC",
                (frame_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_detection_by_class(
        self,
        class_name: str,
        limit: int = 50
    ) -> List[dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM detection WHERE class_name=? ORDER BY created_at DESC LIMIT ?",
                (class_name, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_detection_by_id(
        self,
        detection_id: int
    ) -> Optional[dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                self.SQL_SELECT_BY_ID,
                (detection_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_unsynced(self) -> List[dict]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(self.SQL_SELECT_UNSYNCED)
            return [dict(r) for r in cursor.fetchall()]

    def mark_synced(self, local_rowid: int, new_id: int):
        with self._get_conn() as conn:
            conn.execute(self.SQL_UPDATE_SYNCED, (new_id, local_rowid))
            conn.commit()

    def get_recent(
        self,
        limit: int = 10
    ) -> List[dict[str, Any]]:
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                self.SQL_SELECT_RECENT,
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def prune_cache(
        self,
        max_rows: int = 100
    ) -> None:
        """Optional: remove oldest rows beyond max_rows"""
        with self._get_conn() as conn:
            conn.execute(
                self.SQL_PRUNE,
                (max_rows,)
            )
            conn.commit()
        

class PostgresDb(BaseDb):
    """POstgres main DB."""
    SQL_CREATE_FRAME = """
    CREATE TABLE IF NOT EXISTS frame (
        id SERIAL PRIMARY KEY,
        image_path TEXT NOT NULL,
        camera_id TEXT,
        model_name TEXT,
        created_at BIGINT NOT NULL
    );
    """

    SQL_CREATE_DETECTION = """
    CREATE TABLE IF NOT EXISTS detection (
        id SERIAL PRIMARY KEY,
        frame_id INTEGER NOT NULL REFERENCES frame(id) ON DELETE CASCADE,
        class_name TEXT NOT NULL,
        confidence REAL NOT NULL,
        bbox JSONB NOT NULL,      -- [x, y, w, h] or similar
        attributes JSONB          -- optional additional metadata
    );
    """

    SQL_INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_frames_ts ON frame (created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_frames_camera ON frame (camera_id);",
        "CREATE INDEX IF NOT EXISTS idx_detections_class ON detection (class_name);",
        "CREATE INDEX IF NOT EXISTS idx_detections_frame ON detection (frame_id);",
    ]
    def __init__(self, conn_str: str):
        self.conn_str = conn_str
        self._init_tables()

    def _get_conn(self):
        return psycopg2.connect(
            self.conn_str,
            cursor_factory=RealDictCursor
        )
    
    def _init_tables(self):
        # Format the stored SQL template with the actual table/column names
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(self.SQL_CREATE_FRAME)
                cur.execute(self.SQL_CREATE_DETECTION)
                for idx in self.SQL_INDEXES:
                    cur.execute(idx)
                conn.commit()
        logger.info("Postgres: normalized schema initialized.")

    def insert_frame(
        self,
        image_path,
        camera_id,
        model_name,
        ts
    ):
        query = """
        INSERT INTO frame (
            image_path,
            camera_id,
            model_name,
            created_at
        ) VALUES (%s, %s, %s, %s)
        RETURNING id;
        """
        with self._get_conn() as conn:
            with self.cursor() as cur:
                cur.execute(
                    query,
                    (
                        image_path,
                        camera_id,
                        model_name,
                        ts
                    )
                )
                frame_id = cur.fetchone()["id"]
                conn.commit()
                return frame_id

    def insert_detection(
        self,
        frame_id: uuid,
        class_name: str,
        confidence: float,
        bbox,
        attrs=None
    ) -> int:
        query = """
        INSERT INTO detection (
            frame_id,
            class_name,
            confidence,
            bbox,
            attributes
        ) VALUES (%s, %s, %s, %s, %s);
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        frame_id,
                        class_name,
                        confidence,
                        Json(bbox),
                        Json(attrs or {})
                    )
                )
                conn.commit()            

    def get_detection_by_id(
        self,
        detection_id: int
    ) -> Optional[dict]:
        query = self._format_query(
            self.SQL_SELECT_BY_ID,
            self.table
        )
        qyery = "SELECT * FROM detection WHERE id=%s"
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (detection_id,))
                return cur.fetchone()

    def get_recent_frames(self, limit: int = 20) -> List[dict[str, Any]]:
        query = """
            SELECT * FROM frame
            ORDER BY created_at DESC
            LIMIT %s;
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (limit,))
                return cur.fetchall()

    def get_detection_by_class(
        self,
        class_name: str,
        limit: int = 50
    ):
        query = """
            SELECT * FROM detection
            WHERE class_name=%s
            ORDER BY created_at DESC
            LIMIT %s;
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (class_name, limit))
                return cur.fetchall()

    def get_detections_for_frame(self, frame_id: int):
        query = """
            SELECT * FROM detections
            WHERE frame_id=%s
            ORDER BY id ASC;
        """
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (frame_id,))
                return cur.fetchall()


class DetectionDb:
    """High-level interface combining Postgres + SQLite cache with offline handling."""

    def __init__(
        self,
        postgres_dsn: str,
        sqlite_path: str
    ):
        self.cache = SqliteDb(sqlite_path)
        self.pg = PostgresDb(
            postgres_dsn,
        )
        self.cache.prune_cache(max_rows=100)
        self._start_sync_thread()

    def insert_frame_with_detections(
        self,
        camera_id: str,
        image_path: str,
        detections: list[dict]
    ) -> int:
        """
        High level insert:
        - insert frame
        - insert each detection
        - Cache raw record for offline model_name
        """
        ts = int(time.time())
        try:
            frame_id = self.pg.insert_frame(
                camera_id,
                image_path,
                ts
            )
            for det in detections:
                self.pg.insert_detection(
                    frame_id=frame_id,
                    class_name=det["class"],
                    confidence=det["confidence"],
                    bbox=det["bbox"],
                    ts=ts
                )
        except Exception as e:
            logger.eror(f"Postgres insert failed, falling back to cache: {e}")
            self.cache.insert_detection(
                image_path,
                detections,
                ts
            )
            return -1

        return frame_id

    def get_detection_by_id(self, det_id: int):
        return self.pg.get_detection_by_id(det_id)

    def get_recent_frames(self, limit=20):
        return self.pg.get_recent_frames(limit)

    def get_detection_by_class(self, class_name: str, limit=50):
        return self.pg.get_detections_for_frame(frame_id)
    
    def _sync_unsynced(self):
        """Background thread to push unsynced cache rows to Postgres."""
        delay = 5
        while True:
            unsynced = self.cache.get_unsynced()
            synced_any = False
            for row in unsynced:
                try:
                    frame_id = self.pg.insert_frame(
                        camera_id=row.get(
                            "camera_id",
                            "unknown"
                        ),
                        image_path=row["image_path"],
                        ts=row[BaseDb.COL_CREATED_AT]
                    )
                    for det in json.loads(row[BaseDb.COL_DETECTION_DATA]):
                        self.pg.insert_detection(
                            frame_id=frame_id,
                            class_name=det["class"],
                            confidence=det["confidence"],
                            bbox=det["bbox"],
                            ts=row[BaseDb.COL_CREATED_AT]
                        )

                    self.cache.mark_synced(row['id'], pg_id)
                    logger.info(
                        f"Synced local row {row['id']} -> Postgres ID {pg_id}"
                    )
                    synced_any = True
                    delay = 5
                except Exception as e:
                    logger.warning(
                        f"Failed to sync local row {row['id']} to Postgres: {e}"
                    )
                    delay = min(delay * 2, 300)
                    break

            if synced_any:
                try:
                    self.cache.prune_cache(max_rows=100)
                    logger.debug(
                        "Cache pruned to keep only 100 most recent rows."
                    )
                except Exception as e:
                    logger.warning(
                        f"Cache pruning failed: {e}"
                    )

            time.sleep(delay)
    
    def _start_sync_thread(self):
        t = threading.Thread(
            target=self._sync_unsynced,
            daemon=True
        )
        t.start()


def init_db_with_retry(
    max_retries: int = 10,
    delay: int = 3
) -> DetectionDb:
    for attempt in range(max_retries):
        logger.info(f"Connecting to Postgres: {settings.POSTGRES_DSN} (attempt {attempt + 1})")
        try:
            db_instance = DetectionDb(
                postgres_dsn=settings.POSTGRES_DSN,
                sqlite_path=settings.CACHE_DB_PATH
            )
            logger.info("Successfully connected to Postgres!")
            return db_instance
        except OperationalError as e:
            logger.warning(f"Postgres not ready (attempt {attempt + 1}): {e}")
            time.sleep(delay)
    raise RuntimeError("Failed to connect to Postgres after retries")

db: DetectionDb = init_db_with_retry()
