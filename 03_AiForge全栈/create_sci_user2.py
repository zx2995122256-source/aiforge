import sqlite3, hashlib, time

db_path = "/home/ubuntu/aiforge/backend/data/aiforge.db"
pwd = "sci2025pw"
pw_hash = hashlib.sha256(pwd.encode()).hexdigest()
email = "sci_test@aiforge.ai"

conn = sqlite3.connect(db_path)
conn.execute("DELETE FROM users WHERE email=?", (email,))
conn.execute(
    "INSERT INTO users (email, password_hash, nickname, points, role, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
    (email, pw_hash, "SciFiTester", 500000, "user", time.time(), time.time())
)
conn.commit()
# Add point log
uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
conn.execute(
    "INSERT INTO point_logs (user_id, amount, balance_after, reason, created_at) VALUES (?,?,?,?,?)",
    (uid, 500000, 500000, "测试专用", time.time())
)
conn.commit()
conn.close()
print(f"OK: {email} / {pwd} (UID={uid}, 500000 pts)")