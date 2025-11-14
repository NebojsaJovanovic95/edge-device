from __future__ import annotations
from typing import Any, Optional, List
import json
import time
import sqlite3
import threading
from src.util import logger
import psycopg2
from psycopg2.extras import RealDictCursor
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
    SQLITE_TABLE_NAME = "cache_detections"

    SQL_CREATE_TABLE = f"""
        CREATE TABLE IF NOT EXISTS {SQLITE_TABLE_NAME} (
            {BaseDb.COL_ID} INTEGER PRIMARY KEY AUTOINCREMENT,
            {BaseDb.COL_IMAGE_PATH} TEXT NOT NULL,
            {BaseDb.COL_DETECTION_DATA} TEXT NOT NULL,
            {BaseDb.COL_CREATED_AT} REAL NOT NULL,
            {BaseDb.COL_SYNCED} INTEGER DEFAULT 0
        )
    """

    SQL_SELECT_UNSYNCED = f"""
        SELECT * FROM {SQLITE_TABLE_NAME} WHERE {BaseDb.COL_SYNCED}=0
        ORDER BY {BaseDb.COL_CREATED_AT} ASC
    """

    SQL_UPDATE_SYNCED = f"""
        UPDATE {SQLITE_TABLE_NAME} SET {BaseDb.COL_ID}=?, {BaseDb.COL_SYNCED}=1
        WHERE rowid=?
    """

    SQL_INSERT = f"""
        INSERT INTO {SQLITE_TABLE_NAME} (
            {BaseDb.COL_IMAGE_PATH},
            {BaseDb.COL_DETECTION_DATA},
            {BaseDb.COL_CREATED_AT},
            {BaseDb.COL_SYNCED}
        )
        VALUES (?, ?, ?, 0)
    """

    SQL_INSERT_WITH_ID = f"""
        INSERT INTO {SQLITE_TABLE_NAME} (
            {BaseDb.COL_ID},
            {BaseDb.COL_IMAGE_PATH},
            {BaseDb.COL_DETECTION_DATA},
            {BaseDb.COL_CREATED_AT},
            {BaseDb.COL_SYNCED}
        )
        VALUES (?, ?, ?, ?, 1)
    """

    SQL_SELECT_BY_ID = f"""
        SELECT *
        FROM {SQLITE_TABLE_NAME}
        WHERE {BaseDb.COL_ID}=?
    """

    SQL_SELECT_RECENT = f"""
        SELECT *
        FROM {SQLITE_TABLE_NAME}
        ORDER BY {BaseDb.COL_CREATED_AT} DESC
        LIMIT ?
    """

    SQL_PRUNE = f"""
        DELETE FROM {SQLITE_TABLE_NAME}
        WHERE {BaseDb.COL_ID} NOT IN (
            SELECT {BaseDb.COL_ID}
            FROM {SQLITE_TABLE_NAME}
            ORDER BY {BaseDb.COL_CREATED_AT} DESC
            LIMIT ?
        )
    """

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
            conn.execute(self.SQL_CREATE_TABLE)
            conn.commit()

    def insert_detection(
        self,
        image_path: str,
        detection_data: dict[str, Any],
        ts: Optional[int] = None,
        id_override: Optional[int] = None
    ) -> int:
        ts = ts or int(time.time())
        with self._get_conn() as conn:
            cursor = conn.cursor()
            if id_override:
                cursor.execute(
                    self.SQL_INSERT_WITH_ID,
                    (
                        id_override,
                        image_path,
                        json.dumps(detection_data),
                        ts
                    )
                )
                conn.commit()
                return id_override
            else:
                cursor.execute(
                    self.SQL_INSERT,
                    (
                        image_path,
                        json.dumps(detection_data),
                        ts
                    )
                )
            conn.commit()
            return cursor.lastrowid

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
    SQL_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS {table} (
        {id_col} SERIAL PRIMARY KEY,
        {image_col} TEXT NOT NULL,
        {data_col} JSONB NOT NULL,
        {ts_col} BIGINT NOT NULL
    )
    """

    def __init__(self, conn_str: str, table_name: str):
        self.conn_str = conn_str
        self.table = table_name
        self._init_table()

    def _get_conn(self):
        return psycopg2.connect(
            self.conn_str,
            cursor_factory=RealDictCursor
        )
    
    def _init_table(self):
        # Format the stored SQL template with the actual table/column names
        query = self.SQL_CREATE_TABLE.format(
            table=self.table,
            id_col=self.COL_ID,
            image_col=self.COL_IMAGE_PATH,
            data_col=self.COL_DETECTION_DATA,
            ts_col=self.COL_CREATED_AT
        )
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                conn.commit()

    def insert_detection(
        self,
        image_path: str,
        detection_data: dict,
        ts: Optional[int] = None
    ) -> int:
        ts = ts or int(time.time())
        query = self._format_query(
            self.SQL_INSERT,
            self.table
        )
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        image_path,
                        json.dumps(detection_data),
                        ts
                    )
                )
                conn.commit()
                return cur.fetchone()[0]

    def get_detection_by_id(
        self,
        detection_id: int
    ) -> Optional[dict]:
        query = self._format_query(
            self.SQL_SELECT_BY_ID,
            self.table
        )
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (detection_id,))
                row = cur.fetchone()
                if row:
                    return {
                        self.COL_ID: row[0],
                        self.COL_IMAGE_PATH: row[1],
                        self.COL_DETECTION_DATA: json.loads(
                            row[2]
                        ),
                        self.COL_CREATED_AT: row[3]
                    }
                return None

    def get_recent(self, limit: int = 100) -> List[dict[str, Any]]:
        query = self._format_query(
            self.SQL_SELECT_RECENT,
            self.table
        )
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (limit,))
                rows = cur.fetchall()
                return [
                    {
                        self.COL_ID: row[0],
                        self.COL_IMAGE_PATH: row[1],
                        self.COL_DETECTION_DATA: json.loads(
                            row[2]
                        ),
                        self.COL_CREATED_AT: row[3]
                    }
                    for row in rows
                ]
            

class DetectionDb:
    """High-level interface combining Postgres + SQLite cache with offline handling."""

    def __init__(
        self,
        postgres_dsn: str,
        sqlite_path: str
    ):
        self.cache = SqliteDb(sqlite_path)
        self.main_db = PostgresDb(
            postgres_dsn,
            table_name=settings.POSTGRES_TABLE_NAME
        )
        self.cache.prune_cache(max_rows=100)
        self._start_sync_thread()

    def insert_detection(
        self,
        image_path: str,
        detection_data: dict[str, Any]
    ) -> int:
        """Insert into both cache and main DB."""
        ts: int = int(time.time())
        local_id = self.cache.insert_detection(
            image_path,
            detection_data,
            ts
        )
        try:
            pg_id = self.main_db.insert_detection(
                image_path,
                detection_data,
                ts
            )
            self.cache.mark_synced(
                local_id,
                pg_id
            )
            return pg_id
        except Exception as e:
            logger.warning(
                f"Postgres insert failed: {e}, keeping local cache ID {local_id}"
            )
            return local_id

    def get_detection_by_id(
        self,
        detection_id: int
    ) -> Optional[dict[str, Any]]:
        """Try cache first, then main DB."""
        cached = self.cache.get_detection_by_id(detection_id)
        if cached:
            return cached
        record = self.main_db.get_detection_by_id(detection_id)
        if record:
            self.cache.insert_detection(
                record[BaseDb.COL_IMAGE_PATH],
                record[BaseDb.COL_DETECTION_DATA],
                record[BaseDb.COL_CREATED_AT],
            )
        return record

    def get_recent(self, limit: int = 10) -> List[dict]:
        return self.cache.get_recent(limit)
    
    def _sync_unsynced(self):
        """Background thread to push unsynced cache rows to Postgres."""
        delay = 5
        while True:
            unsynced = self.cache.get_unsynced()
            synced_any = False
            for row in unsynced:
                try:
                    pg_id = self.main_db.insert_detection(
                        image_path=row[BaseDb.COL_IMAGE_PATH],
                        detection_data=json.loads(row[BaseDb.COL_DETECTION_DATA]),
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