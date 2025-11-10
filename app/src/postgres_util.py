import psycopg2
from psycopg2.extras import RealDictCursor
import json

class PostgresUtil:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._init_db()

    def _get_conn(self):
        return psycopg2.connect(self.dsn, cursor_factory=RealDictCursor)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id SERIAL PRIMARY KEY,
                    image_path TEXT NOT NULL,
                    detection_data JSONB NOT NULL
                )
            """)
            conn.commit()

    def insert_detection(self, image_path: str, detection_data: dict) -> int:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO detections (image_path, detection_data) VALUES (%s, %s) RETURNING id",
                    (image_path, json.dumps(detection_data))
                )
                conn.commit()
                return cur.fetchone()["id"]

    def get_all_detections(self) -> list[dict]:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM detections")
                return cur.fetchall()
