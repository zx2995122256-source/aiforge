import sqlite3
import time
import hashlib
import os
from config import DB_PATH, NEW_USER_BONUS


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nickname TEXT DEFAULT '',
            points INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user',
            created_at REAL,
            updated_at REAL
            register_ip TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id TEXT NOT NULL,
            amount REAL NOT NULL,
            points INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            trade_no TEXT DEFAULT '',
            created_at REAL,
            paid_at REAL
        );
        CREATE TABLE IF NOT EXISTS point_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            reason TEXT DEFAULT '',
            created_at REAL
        );
        CREATE TABLE IF NOT EXISTS redeem_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            points INTEGER NOT NULL,
            used_by INTEGER DEFAULT 0,
            used_at REAL DEFAULT 0,
            created_at REAL
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_type TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            points_cost INTEGER DEFAULT 0,
            oiioii_task_id INTEGER DEFAULT 0,
            result_url TEXT DEFAULT '',
            created_at REAL,
            finished_at REAL,
            reference_images TEXT DEFAULT '',
            reference_video TEXT DEFAULT ''
        );
    """)
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN reference_images TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN reference_video TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN error TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN register_ip TEXT DEFAULT ''")
    except Exception:
        pass
    # Projects table for 一键成片
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                script TEXT DEFAULT '',
                raw_script TEXT DEFAULT '',
                video_model TEXT DEFAULT 'Gemini Omni',
                image_model TEXT DEFAULT 'GPT-Image2',
                ratio TEXT DEFAULT '16:9',
                resolution TEXT DEFAULT '720p',
                image_resolution TEXT DEFAULT '1K',
                duration INTEGER DEFAULT 10,
                segments_json TEXT DEFAULT '[]',
                assets_json TEXT DEFAULT '[]',
                phase INTEGER DEFAULT 0,
                results_json TEXT DEFAULT '{}',
                created_at REAL,
                updated_at REAL
            )
        """)
    except Exception:
        pass
    # Migration: add image_resolution to existing projects
    try:
        conn.execute("ALTER TABLE projects ADD COLUMN image_resolution TEXT DEFAULT '1K'")
    except Exception:
        pass
    # Agents table for referral system
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                invite_code TEXT UNIQUE NOT NULL,
                commission_rate REAL DEFAULT 20.0,
                total_referrals INTEGER DEFAULT 0,
                total_commission REAL DEFAULT 0.0,
                settled_commission REAL DEFAULT 0.0,
                created_at REAL
            )
        """)
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN inviter_agent_id INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE orders ADD COLUMN agent_id INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE orders ADD COLUMN commission_amount REAL DEFAULT 0.0")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE orders ADD COLUMN commission_settled INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN llm_settings TEXT DEFAULT ''")
    except Exception:
        pass
    conn.commit()
    conn.close()


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()



def count_registrations_by_ip(ip: str, hours: int = 24) -> int:
    """Count registrations from the same IP in the last N hours"""
    conn = _get_conn()
    cutoff = time.time() - hours * 3600
    row = conn.execute(
        "SELECT COUNT(*) as c FROM users WHERE register_ip=? AND created_at>?",
        (ip, cutoff)
    ).fetchone()
    conn.close()
    return row["c"]

def create_user(email: str, password: str, nickname: str = "", register_ip: str = "", inviter_agent_id: int = 0) -> dict:
    conn = _get_conn()
    now = time.time()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, nickname, points, role, created_at, updated_at, register_ip, inviter_agent_id) VALUES (?,?,?,?,?,?,?,?,?)",
            (email, _hash_password(password), nickname or email.split("@")[0], NEW_USER_BONUS, "user", now, now, register_ip, inviter_agent_id),
        )
        conn.commit()
        uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        if NEW_USER_BONUS > 0:
            conn.execute(
                "INSERT INTO point_logs (user_id, amount, balance_after, reason, created_at) VALUES (?,?,?,?,?)",
                (uid, NEW_USER_BONUS, NEW_USER_BONUS, "新用户注册赠送", now),
            )
            conn.commit()
        return {"id": uid, "email": email, "points": NEW_USER_BONUS, "role": "user"}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def verify_user(email: str, password: str) -> dict:
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, email, password_hash, nickname, points, role FROM users WHERE email=?",
        (email,),
    ).fetchone()
    conn.close()
    if not row or row["password_hash"] != _hash_password(password):
        return None
    return dict(row)


def get_user(uid: int) -> dict:
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, email, nickname, points, role, created_at FROM users WHERE id=?", (uid,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def add_points(uid: int, amount: int, reason: str = "") -> int:
    conn = _get_conn()
    now = time.time()
    conn.execute("UPDATE users SET points=points+?, updated_at=? WHERE id=?", (amount, now, uid))
    row = conn.execute("SELECT points FROM users WHERE id=?", (uid,)).fetchone()
    balance = row["points"] if row else 0
    conn.execute(
        "INSERT INTO point_logs (user_id, amount, balance_after, reason, created_at) VALUES (?,?,?,?,?)",
        (uid, amount, balance, reason, now),
    )
    conn.commit()
    conn.close()
    return balance


def deduct_points(uid: int, amount: int, reason: str = "") -> bool:
    conn = _get_conn()
    row = conn.execute("SELECT points FROM users WHERE id=?", (uid,)).fetchone()
    if not row or row["points"] < amount:
        conn.close()
        return False
    now = time.time()
    conn.execute("UPDATE users SET points=points-?, updated_at=? WHERE id=?", (amount, now, uid))
    row2 = conn.execute("SELECT points FROM users WHERE id=?", (uid,)).fetchone()
    balance = row2["points"] if row2 else 0
    conn.execute(
        "INSERT INTO point_logs (user_id, amount, balance_after, reason, created_at) VALUES (?,?,?,?,?)",
        (uid, -amount, balance, reason, now),
    )
    conn.commit()
    conn.close()
    return True


def create_order(uid: int, plan_id: str, amount: float, points: int) -> int:
    conn = _get_conn()
    now = time.time()
    conn.execute(
        "INSERT INTO orders (user_id, plan_id, amount, points, status, created_at) VALUES (?,?,?,?,?,?)",
        (uid, plan_id, amount, points, "pending", now),
    )
    oid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return oid


def pay_order(oid: int, trade_no: str = "") -> bool:
    conn = _get_conn()
    now = time.time()
    row = conn.execute("SELECT user_id, points, amount, status FROM orders WHERE id=?", (oid,)).fetchone()
    if not row or row["status"] != "pending":
        conn.close()
        return False
    conn.execute("UPDATE orders SET status='paid', trade_no=?, paid_at=? WHERE id=?", (trade_no, now, oid))
    conn.commit()
    add_points(row["user_id"], row["points"], f"购买套餐-订单#{oid}")

    # Calculate agent commission from the order's buyer
    buyer_row = conn.execute("SELECT inviter_agent_id FROM users WHERE id=?", (row["user_id"],)).fetchone()
    if buyer_row and buyer_row["inviter_agent_id"]:
        agent = conn.execute("SELECT id, commission_rate FROM agents WHERE user_id=?", (buyer_row["inviter_agent_id"],)).fetchone()
        if agent:
            commission = round(row["amount"] * agent["commission_rate"] / 100, 2)
            if commission > 0:
                conn.execute("UPDATE orders SET agent_id=?, commission_amount=? WHERE id=?", (agent["id"], commission, oid))
                conn.execute("UPDATE agents SET total_commission=total_commission+?, total_referrals=total_referrals+? WHERE id=?", (commission, 1 if row["user_id"] else 0, agent["id"]))
                conn.commit()

    conn.close()
    return True


def create_task(uid: int, task_type: str, model: str, prompt: str, points_cost: int, oiioii_task_id: int, reference_images: str = "", reference_video: str = "") -> int:
    conn = _get_conn()
    now = time.time()
    conn.execute(
        "INSERT INTO tasks (user_id, task_type, model, prompt, status, points_cost, oiioii_task_id, created_at, reference_images, reference_video) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (uid, task_type, model, prompt, "running", points_cost, oiioii_task_id, now, reference_images, reference_video),
    )
    tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return tid


def update_task(tid: int, status: str, result_url: str = "", error: str = ""):
    conn = _get_conn()
    now = time.time()
    conn.execute("UPDATE tasks SET status=?, result_url=?, finished_at=?, error=? WHERE id=?", (status, result_url, now, error, tid))
    conn.commit()
    conn.close()


def get_user_tasks(uid: int, limit: int = 50) -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (uid, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_task(tid: int, uid: int) -> bool:
    conn = _get_conn()
    row = conn.execute("SELECT status FROM tasks WHERE id=? AND user_id=?", (tid, uid)).fetchone()
    if not row:
        conn.close()
        return False
    if row["status"] == "running":
        conn.close()
        return False
    conn.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (tid, uid))
    conn.commit()
    conn.close()
    return True


def get_all_users(limit: int = 100) -> list:
    conn = _get_conn()
    rows = conn.execute("SELECT id, email, nickname, points, role, created_at FROM users ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==================== Agent System ====================

def create_agent(user_id: int, commission_rate: float = 20.0, invite_code: str = "") -> dict:
    conn = _get_conn()
    now = time.time()
    if not invite_code:
        import random, string
        invite_code = "AG" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    try:
        conn.execute(
            "INSERT INTO agents (user_id, invite_code, commission_rate, created_at) VALUES (?,?,?,?)",
            (user_id, invite_code, commission_rate, now),
        )
        conn.commit()
        aid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        row = conn.execute("SELECT * FROM agents WHERE id=?", (aid,)).fetchone()
        conn.close()
        return dict(row) if row else None
    except sqlite3.IntegrityError:
        conn.close()
        return None


def get_agents() -> list:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT a.*, u.email, u.nickname, u.points
        FROM agents a JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_agent_by_code(code: str) -> dict:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM agents WHERE invite_code=?", (code,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_agent_by_user_id(user_id: int) -> dict:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM agents WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_agent_referrals(agent_id: int) -> list:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT u.id, u.email, u.nickname, u.points, u.created_at,
               COALESCE((SELECT SUM(o.amount) FROM orders o WHERE o.user_id=u.id AND o.status='paid'), 0) as total_spent
        FROM users u WHERE u.inviter_agent_id=?
        ORDER BY u.created_at DESC
    """, (agent_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_agent_orders(agent_id: int) -> list:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT o.*, u.email as user_email
        FROM orders o JOIN users u ON o.user_id=u.id
        WHERE o.agent_id=? AND o.commission_amount>0
        ORDER BY o.created_at DESC
    """, (agent_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def settle_agent_commission(agent_id: int) -> dict:
    conn = _get_conn()
    agent = conn.execute("SELECT * FROM agents WHERE id=?", (agent_id,)).fetchone()
    if not agent:
        conn.close()
        return {"ok": False, "msg": "代理不存在"}
    unsettled = agent["total_commission"] - agent["settled_commission"]
    if unsettled <= 0:
        conn.close()
        return {"ok": False, "msg": "没有可结算的佣金"}
    conn.execute("UPDATE agents SET settled_commission=? WHERE id=?", (agent["total_commission"], agent_id))
    conn.execute("UPDATE orders SET commission_settled=1 WHERE agent_id=? AND commission_settled=0", (agent_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "amount": unsettled}


def redeem_code(code: str, uid: int) -> dict:
    conn = _get_conn()
    row = conn.execute("SELECT id, points, used_by FROM redeem_codes WHERE code=?", (code,)).fetchone()
    if not row:
        conn.close()
        return {"ok": False, "msg": "兑换码不存在"}
    if row["used_by"]:
        conn.close()
        return {"ok": False, "msg": "兑换码已被使用"}
    now = time.time()
    conn.execute("UPDATE redeem_codes SET used_by=?, used_at=? WHERE id=?", (uid, now, row["id"]))
    conn.commit()
    add_points(uid, row["points"], f"兑换码-{code[:8]}")
    conn.close()
    return {"ok": True, "points": row["points"]}


def create_redeem_code(points: int) -> str:
    import random
    import string
    code = "AF" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    conn = _get_conn()
    now = time.time()
    conn.execute("INSERT INTO redeem_codes (code, points, created_at) VALUES (?,?,?)", (code, points, now))
    conn.commit()
    conn.close()
    return code


def cleanup_old_tasks(days: int = 30) -> int:
    cutoff = time.time() - days * 86400
    conn = _get_conn()
    cur = conn.execute("DELETE FROM tasks WHERE status != 'running' AND created_at < ?", (cutoff,))
    deleted = cur.rowcount
    cur2 = conn.execute("DELETE FROM point_logs WHERE created_at < ?", (cutoff,))
    deleted += cur2.rowcount
    cur3 = conn.execute("DELETE FROM redeem_codes WHERE used_by != 0 AND used_at < ?", (cutoff,))
    deleted += cur3.rowcount
    conn.commit()
    conn.close()
    return deleted


def get_stats() -> dict:
    conn = _get_conn()
    users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    tasks = conn.execute("SELECT COUNT(*) as c FROM tasks").fetchone()["c"]
    running = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE status='running'").fetchone()["c"]
    points_total = conn.execute("SELECT COALESCE(SUM(points),0) as s FROM users").fetchone()["s"]
    codes = conn.execute("SELECT COUNT(*) as c FROM redeem_codes WHERE used_by=0").fetchone()["c"]
    conn.close()
    return {"users": users, "tasks": tasks, "running": running, "points_total": points_total, "unused_codes": codes}
