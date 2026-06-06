import sqlite3
import json
import time
import os
import shutil
import threading
from datetime import datetime, timedelta
from typing import Optional
from config import DB_PATH, BACKUPS_DIR, DB_BACKUP_RETENTION_DAYS


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


_MIGRATIONS = [
    ("tasks", "output_date", "TEXT", None),
    ("tasks", "ref_image_urls", "TEXT", None),
    ("tasks", "duration_sec", "INTEGER", None),
    ("accounts", "total_tasks", "INTEGER", 0),
    ("accounts", "video_used", "INTEGER", 0),
    ("accounts", "last_sync_at", "REAL", 0),
]


def _seed_video_used():
    conn = get_conn()
    cur = conn.execute("PRAGMA table_info(accounts)")
    cols = {r["name"] for r in cur.fetchall()}
    if "video_used" not in cols:
        conn.execute("ALTER TABLE accounts ADD COLUMN video_used INTEGER DEFAULT 0")
    conn.execute(
        "UPDATE accounts SET video_used = 0 WHERE video_used = 1 OR video_used = 0"
    )
    conn.execute(
        "UPDATE accounts SET video_used = 1 WHERE points_remaining < 200"
    )
    conn.commit()
    conn.close()


def run_migrations():
    conn = get_conn()
    for table, column, col_type, default in _MIGRATIONS:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        existing = {row["name"] for row in cursor.fetchall()}
        if column not in existing:
            default_clause = f"DEFAULT {default}" if default is not None else ""
            sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type} {default_clause}"
            conn.execute(sql)
            print(f"[DB] Migration: added {column} to {table}")
    conn.commit()
    conn.close()


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            token TEXT DEFAULT '',
            token_expiry REAL DEFAULT 0,
            points_remaining INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            workspace_id TEXT DEFAULT '',
            last_used_at REAL DEFAULT 0,
            created_at REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            task_type TEXT NOT NULL,
            model_name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            ratio TEXT DEFAULT '16:9',
            resolution TEXT DEFAULT '720p',
            duration INTEGER DEFAULT 5,
            status TEXT DEFAULT 'pending',
            task_id TEXT DEFAULT '',
            result_uri TEXT DEFAULT '',
            local_path TEXT DEFAULT '',
            points_cost INTEGER DEFAULT 0,
            error_message TEXT DEFAULT '',
            created_at REAL DEFAULT 0,
            completed_at REAL DEFAULT 0,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        );
    """)
    conn.commit()
    conn.close()
    run_migrations()
    _seed_video_used()


class AccountDB:
    @staticmethod
    def add(email: str, password: str, token: str = "", workspace_id: str = "",
            points: int = 0) -> int:
        conn = get_conn()
        cur = conn.execute(
            "INSERT OR IGNORE INTO accounts "
            "(email, password, token, workspace_id, points_remaining, total_earned, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'active', ?)",
            (email, password, token, workspace_id, points, points, time.time())
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    @staticmethod
    def get_all():
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM accounts ORDER BY points_remaining DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(account_id: int) -> Optional[dict]:
        conn = get_conn()
        row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    _rr_offset = 0
    _rr_lock = threading.Lock()

    @staticmethod
    def get_available(min_points: int = 10, prefer_lowest: bool = False,
                      video_pool: bool = False) -> Optional[dict]:
        conn = get_conn()
        order = "points_remaining ASC" if prefer_lowest else "points_remaining DESC"
        rows = conn.execute(
            "SELECT * FROM accounts "
            "WHERE status = 'active' AND points_remaining >= ? "
            f"ORDER BY {order}",
            (min_points,)
        ).fetchall()
        conn.close()
        if not rows:
            return None
        with AccountDB._rr_lock:
            idx = AccountDB._rr_offset % len(rows)
            AccountDB._rr_offset += 1
        return dict(rows[idx])

    @staticmethod
    def get_any_active(min_points: int = 10, prefer_lowest: bool = False) -> Optional[dict]:
        conn = get_conn()
        order = "points_remaining ASC" if prefer_lowest else "points_remaining DESC"
        rows = conn.execute(
            "SELECT * FROM accounts "
            "WHERE status = 'active' AND points_remaining >= ? "
            f"ORDER BY {order}",
            (min_points,)
        ).fetchall()
        conn.close()
        if not rows:
            return None
        with AccountDB._rr_lock:
            idx = AccountDB._rr_offset % len(rows)
            AccountDB._rr_offset += 1
        return dict(rows[idx])

    @staticmethod
    def mark_video_used(account_id: int):
        conn = get_conn()
        conn.execute(
            "UPDATE accounts SET video_used = 1 WHERE id = ?", (account_id,)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def reset_video_used(account_id: int):
        conn = get_conn()
        conn.execute(
            "UPDATE accounts SET video_used = 0 WHERE id = ?", (account_id,)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_token(account_id: int, token: str, expiry: float):
        conn = get_conn()
        conn.execute(
            "UPDATE accounts SET token = ?, token_expiry = ? WHERE id = ?",
            (token, expiry, account_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_points(account_id: int, points: int, spent: int = 0):
        conn = get_conn()
        conn.execute(
            "UPDATE accounts SET points_remaining = ?, total_spent = total_spent + ? WHERE id = ?",
            (points, spent, account_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_points_with_sync(account_id: int, points: int, sync_timestamp: float):
        conn = get_conn()
        conn.execute(
            "UPDATE accounts SET points_remaining = ?, last_sync_at = ? WHERE id = ?",
            (points, sync_timestamp, account_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def try_deduct_points(account_id: int, cost: int) -> bool:
        conn = get_conn()
        row = conn.execute(
            "SELECT points_remaining FROM accounts WHERE id = ? AND status = 'active'",
            (account_id,)
        ).fetchone()
        if not row or row["points_remaining"] < cost:
            conn.close()
            return False
        conn.execute(
            "UPDATE accounts SET points_remaining = points_remaining - ?, total_spent = total_spent + ? WHERE id = ? AND points_remaining >= ?",
            (cost, cost, account_id, cost)
        )
        changed = conn.total_changes
        conn.commit()
        conn.close()
        return changed > 0

    @staticmethod
    def refund_points(account_id: int, cost: int):
        conn = get_conn()
        conn.execute(
            "UPDATE accounts SET points_remaining = points_remaining + ?, total_spent = total_spent - ? WHERE id = ?",
            (cost, cost, account_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_status(account_id: int, status: str):
        conn = get_conn()
        conn.execute(
            "UPDATE accounts SET status = ? WHERE id = ?", (status, account_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_workspace(account_id: int, workspace_id: str):
        conn = get_conn()
        conn.execute(
            "UPDATE accounts SET workspace_id = ? WHERE id = ?",
            (workspace_id, account_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_last_used(account_id: int):
        conn = get_conn()
        conn.execute(
            "UPDATE accounts SET last_used_at = ? WHERE id = ?",
            (time.time(), account_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def delete(account_id: int):
        conn = get_conn()
        conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def total_points() -> int:
        conn = get_conn()
        row = conn.execute(
            "SELECT COALESCE(SUM(points_remaining), 0) as total FROM accounts WHERE status = 'active'"
        ).fetchone()
        conn.close()
        return row["total"]

    @staticmethod
    def active_count() -> int:
        conn = get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM accounts WHERE status = 'active'"
        ).fetchone()
        conn.close()
        return row["cnt"]


class TaskDB:
    @staticmethod
    def add(account_id: int, task_type: str, model_name: str, prompt: str,
            ratio: str = "16:9", resolution: str = "720p", duration: int = 5,
            points_cost: int = 0) -> int:
        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO tasks "
            "(account_id, task_type, model_name, prompt, ratio, resolution, duration, "
            "points_cost, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)",
            (account_id, task_type, model_name, prompt, ratio, resolution, duration,
             points_cost, time.time())
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id

    @staticmethod
    def get_all(limit: int = 100):
        conn = get_conn()
        rows = conn.execute(
            "SELECT t.*, a.email as account_email FROM tasks t "
            "LEFT JOIN accounts a ON t.account_id = a.id "
            "ORDER BY t.created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(task_db_id: int) -> Optional[dict]:
        conn = get_conn()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_db_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_status(task_db_id: int, status: str, task_id: str = "",
                      result_uri: str = "", local_path: str = "",
                      error_message: str = ""):
        conn = get_conn()
        completed = time.time() if status in ("completed", "failed") else 0
        conn.execute(
            "UPDATE tasks SET status = ?, task_id = ?, result_uri = ?, "
            "local_path = ?, error_message = ?, completed_at = ? WHERE id = ?",
            (status, task_id, result_uri, local_path, error_message, completed, task_db_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_pending():
        conn = get_conn()
        rows = conn.execute(
            "SELECT * FROM tasks WHERE status IN ('pending', 'processing') ORDER BY created_at"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def stats():
        conn = get_conn()
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
        ).fetchall()
        conn.close()
        return {r["status"]: r["cnt"] for r in rows}


def backup_db():
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(BACKUPS_DIR, f"db_{timestamp}.db")

    if not os.path.exists(DB_PATH):
        print(f"[DB] DB file not found at {DB_PATH}, skipping backup")
        return None

    shutil.copy2(DB_PATH, backup_path)
    print(f"[DB] Backed up to {backup_path}")

    cutoff = datetime.now() - timedelta(days=DB_BACKUP_RETENTION_DAYS)
    for fname in os.listdir(BACKUPS_DIR):
        if fname.startswith("db_") and fname.endswith(".db"):
            fpath = os.path.join(BACKUPS_DIR, fname)
            mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
            if mtime < cutoff:
                os.remove(fpath)
                print(f"[DB] Removed old backup: {fname}")

    return backup_path


def export_tasks_json():
    os.makedirs(BACKUPS_DIR, exist_ok=True)
    tasks = TaskDB.get_all(limit=99999)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    export_path = os.path.join(BACKUPS_DIR, f"tasks_{timestamp}.json")

    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2, default=str)

    print(f"[DB] Exported {len(tasks)} tasks to {export_path}")
    return export_path
