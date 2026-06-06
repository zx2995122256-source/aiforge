import sqlite3, hashlib, time

db = "/home/ubuntu/aiforge/backend/data/aiforge.db"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

email = "xiaye@123"
pw_hash = hashlib.sha256("4579561".encode()).hexdigest()
now = time.time()

conn.execute(
    "INSERT OR IGNORE INTO users (email, password_hash, nickname, points, role, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
    (email, pw_hash, "夏爷", 999999, "admin", now, now),
)
conn.commit()

r = conn.execute("SELECT id, email, role, points FROM users WHERE email=?", (email,)).fetchone()
if r:
    print(f"OK ID:{r['id']} {r['email']} role={r['role']} {r['points']}pts")
else:
    print("FAILED")
conn.close()