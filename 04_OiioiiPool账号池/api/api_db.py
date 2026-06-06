"""API 用户、Key、计费日志数据库"""
import sqlite3
import hashlib
import secrets
import time
import threading
from config import DB_PATH

_lock = threading.Lock()


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_api_tables():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS api_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL DEFAULT 0,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'active',
            created_at REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key_prefix TEXT NOT NULL,
            key_hash TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT '',
            quota REAL DEFAULT 0,
            used_quota REAL DEFAULT 0,
            rate_limit INTEGER DEFAULT 10,
            models TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            expires_at REAL DEFAULT 0,
            created_at REAL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES api_users(id)
        );

        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key_id INTEGER NOT NULL,
            task_id INTEGER DEFAULT 0,
            model TEXT DEFAULT '',
            task_type TEXT DEFAULT '',
            duration INTEGER DEFAULT 0,
            resolution TEXT DEFAULT '',
            cost_points INTEGER DEFAULT 0,
            cost_yuan REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            error_msg TEXT DEFAULT '',
            created_at REAL DEFAULT 0,
            completed_at REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS redeem_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            amount REAL NOT NULL,
            created_by INTEGER DEFAULT 0,
            used_by INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at REAL DEFAULT 0,
            used_at REAL DEFAULT 0
        );
    """)
    # 创建默认管理员
    cur = conn.execute("SELECT id FROM api_users WHERE username='admin'")
    if not cur.fetchone():
        _create_user_internal(conn, "admin", "admin123", role="admin")
        print("[API DB] Default admin created: admin / admin123")
    conn.commit()
    conn.close()


# ─── 用户 ───

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _create_user_internal(conn, username: str, password: str, role: str = "user") -> int:
    now = time.time()
    cur = conn.execute(
        "INSERT INTO api_users (username, password_hash, balance, role, status, created_at) VALUES (?,?,0,?,'active',?)",
        (username, _hash_password(password), role, now)
    )
    return cur.lastrowid


def create_user(username: str, password: str, role: str = "user") -> dict:
    with _lock:
        conn = _get_conn()
        try:
            uid = _create_user_internal(conn, username, password, role)
            conn.commit()
            return {"success": True, "user_id": uid}
        except sqlite3.IntegrityError:
            return {"success": False, "error": "Username already exists"}
        finally:
            conn.close()


def verify_user(username: str, password: str) -> dict:
    conn = _get_conn()
    cur = conn.execute(
        "SELECT id, username, balance, role, status FROM api_users WHERE username=? AND password_hash=?",
        (username, _hash_password(password))
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"success": False, "error": "Invalid credentials"}
    if row["status"] != "active":
        return {"success": False, "error": "Account disabled"}
    return {"success": True, "user_id": row["id"], "username": row["username"],
            "balance": row["balance"], "role": row["role"]}


def get_user(user_id: int) -> dict:
    conn = _get_conn()
    cur = conn.execute("SELECT id, username, balance, role, status, created_at FROM api_users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {}
    return dict(row)


def update_balance(user_id: int, amount: float) -> bool:
    """充值(amount>0)或扣费(amount<0)"""
    with _lock:
        conn = _get_conn()
        cur = conn.execute("SELECT balance FROM api_users WHERE id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False
        new_balance = round(row["balance"] + amount, 4)
        if new_balance < 0:
            conn.close()
            return False
        conn.execute("UPDATE api_users SET balance=? WHERE id=?", (new_balance, user_id))
        conn.commit()
        conn.close()
        return True


def list_users() -> list:
    conn = _get_conn()
    rows = conn.execute("SELECT id, username, balance, role, status, created_at FROM api_users ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── API Key ───

def create_api_key(user_id: int, name: str = "", quota: float = 0,
                   rate_limit: int = 10, models: str = "",
                   expires_at: float = 0) -> dict:
    raw_key = "sk-" + secrets.token_hex(24)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]
    now = time.time()

    with _lock:
        conn = _get_conn()
        try:
            cur = conn.execute(
                "INSERT INTO api_keys (user_id, key_prefix, key_hash, name, quota, used_quota, rate_limit, models, status, expires_at, created_at) VALUES (?,?,?,?,?,0,?,?,?,?,?)",
                (user_id, key_prefix, key_hash, name, quota, rate_limit, models, "active", expires_at, now)
            )
            conn.commit()
            key_id = cur.lastrowid
        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}
        conn.close()

    return {"success": True, "key_id": key_id, "key": raw_key, "prefix": key_prefix}


def verify_api_key(raw_key: str) -> dict:
    """验证 API Key，返回 key 信息 + 用户信息"""
    if not raw_key.startswith("sk-"):
        return {"success": False, "error": "Invalid key format"}

    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    conn = _get_conn()
    cur = conn.execute(
        """SELECT k.id, k.user_id, k.name, k.quota, k.used_quota, k.rate_limit, k.models, k.status, k.expires_at,
                  u.username, u.balance, u.role, u.status as user_status
           FROM api_keys k JOIN api_users u ON k.user_id = u.id
           WHERE k.key_hash=?""",
        (key_hash,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return {"success": False, "error": "Invalid API key"}
    if row["status"] != "active":
        return {"success": False, "error": "API key is disabled"}
    if row["user_status"] != "active":
        return {"success": False, "error": "Account is disabled"}
    if row["expires_at"] > 0 and time.time() > row["expires_at"]:
        return {"success": False, "error": "API key expired"}
    if row["quota"] > 0 and row["used_quota"] >= row["quota"]:
        return {"success": False, "error": "API key quota exceeded"}

    return {
        "success": True,
        "key_id": row["id"],
        "user_id": row["user_id"],
        "username": row["username"],
        "balance": row["balance"],
        "role": row["role"],
        "rate_limit": row["rate_limit"],
        "models": row["models"],
        "quota": row["quota"],
        "used_quota": row["used_quota"],
    }


def list_api_keys(user_id: int = 0) -> list:
    conn = _get_conn()
    if user_id:
        rows = conn.execute(
            "SELECT id, user_id, key_prefix, name, quota, used_quota, rate_limit, models, status, expires_at, created_at FROM api_keys WHERE user_id=? ORDER BY id",
            (user_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, user_id, key_prefix, name, quota, used_quota, rate_limit, models, status, expires_at, created_at FROM api_keys ORDER BY id"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def revoke_api_key(key_id: int) -> bool:
    with _lock:
        conn = _get_conn()
        conn.execute("UPDATE api_keys SET status='revoked' WHERE id=?", (key_id,))
        conn.commit()
        conn.close()
    return True


def update_key_used_quota(key_id: int, amount: float) -> bool:
    with _lock:
        conn = _get_conn()
        conn.execute("UPDATE api_keys SET used_quota = used_quota + ? WHERE id=?", (amount, key_id))
        conn.commit()
        conn.close()
    return True


# ─── 日志 ───

def create_log(user_id: int, key_id: int, model: str, task_type: str,
               duration: int = 0, resolution: str = "",
               cost_points: int = 0, cost_yuan: float = 0,
               task_id: int = 0) -> int:
    now = time.time()
    with _lock:
        conn = _get_conn()
        cur = conn.execute(
            "INSERT INTO api_logs (user_id, key_id, task_id, model, task_type, duration, resolution, cost_points, cost_yuan, status, created_at) VALUES (?,?,?,?,?,?,?,?,?,'pending',?)",
            (user_id, key_id, task_id, model, task_type, duration, resolution, cost_points, cost_yuan, now)
        )
        conn.commit()
        log_id = cur.lastrowid
        conn.close()
    return log_id


def update_log_status(log_id: int, status: str, error_msg: str = "", cost_yuan: float = 0):
    with _lock:
        conn = _get_conn()
        conn.execute(
            "UPDATE api_logs SET status=?, error_msg=?, cost_yuan=?, completed_at=? WHERE id=?",
            (status, error_msg, cost_yuan, time.time(), log_id)
        )
        conn.commit()
        conn.close()


def get_logs(user_id: int = 0, key_id: int = 0, limit: int = 100) -> list:
    conn = _get_conn()
    query = "SELECT * FROM api_logs"
    conditions = []
    params = []
    if user_id:
        conditions.append("user_id=?")
        params.append(user_id)
    if key_id:
        conditions.append("key_id=?")
        params.append(key_id)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_usage_stats(user_id: int = 0) -> dict:
    conn = _get_conn()
    if user_id:
        cur = conn.execute(
            "SELECT COUNT(*) as total, SUM(cost_yuan) as total_cost, SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as success_count, SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as fail_count FROM api_logs WHERE user_id=?",
            (user_id,)
        )
    else:
        cur = conn.execute(
            "SELECT COUNT(*) as total, SUM(cost_yuan) as total_cost, SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as success_count, SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as fail_count FROM api_logs"
        )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {"total": 0, "total_cost": 0, "success_count": 0, "fail_count": 0}


# ─── 兑换码 ───

def create_redeem_codes(amount: float, count: int, created_by: int = 0) -> list:
    """批量生成兑换码"""
    codes = []
    now = time.time()
    with _lock:
        conn = _get_conn()
        for _ in range(count):
            code = "RC-" + secrets.token_hex(6).upper()
            conn.execute(
                "INSERT INTO redeem_codes (code, amount, created_by, status, created_at) VALUES (?,?,?,'active',?)",
                (code, amount, created_by, now)
            )
            codes.append({"code": code, "amount": amount})
        conn.commit()
        conn.close()
    return codes


def redeem_code(code: str, user_id: int) -> dict:
    """用户兑换码"""
    with _lock:
        conn = _get_conn()
        cur = conn.execute("SELECT id, amount, status FROM redeem_codes WHERE code=?", (code,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {"success": False, "error": "兑换码不存在"}
        if row["status"] != "active":
            conn.close()
            return {"success": False, "error": "兑换码已使用"}
        # 标记已使用
        conn.execute("UPDATE redeem_codes SET status='used', used_by=?, used_at=? WHERE id=?",
                     (user_id, time.time(), row["id"]))
        # 充值
        cur2 = conn.execute("SELECT balance FROM api_users WHERE id=?", (user_id,))
        user = cur2.fetchone()
        if not user:
            conn.close()
            return {"success": False, "error": "用户不存在"}
        new_balance = round(user["balance"] + row["amount"], 4)
        conn.execute("UPDATE api_users SET balance=? WHERE id=?", (new_balance, user_id))
        conn.commit()
        conn.close()
    return {"success": True, "amount": row["amount"], "new_balance": new_balance}


def list_redeem_codes(status: str = "", limit: int = 200) -> list:
    conn = _get_conn()
    if status:
        rows = conn.execute("SELECT * FROM redeem_codes WHERE status=? ORDER BY id DESC LIMIT ?", (status, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM redeem_codes ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
