import time

from fastapi import APIRouter, HTTPException

from src.api.utils import get_db_connection

router = APIRouter()

START_TIME = time.time()


@router.get("/health")
def get_health():
    """
    Returns server health status, uptime, version, and database row counts for all tables.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get list of tables in sqlite_master
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        db_row_counts = {}
        for tbl in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
            db_row_counts[tbl] = cursor.fetchone()[0]

        conn.close()

        uptime = time.time() - START_TIME
        return {
            "status": "ok",
            "uptime_seconds": round(uptime, 2),
            "version": "1.0.0",
            "db_row_counts": db_row_counts,
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {e!s}")
