import sqlite3, hashlib, time

db = r"c:\Users\Administrator\Documents\锤子Aicg\03_AiForge全栈\backend\data\aiforge.db"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

email = "xiaye@123"
password = "4579561"
pw_hash = hashlib.sha256(password.encode()).hexdigest()
now = time.time()

conn.execute(
    "INSERT OR IGNORE INTO users (email, password_hash, nickname, points, role, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
    (email, pw_hash, "夏爷", 999999, "admin", now, now),
)
conn.commit()

# Verify
r = conn.execute("SELECT id, email, role, points FROM users WHERE email=?", (email,)).fetchone()
if r:
    print(f"✅ 创建成功！ID:{r['id']}  {r['email']}  role={r['role']}  {r['points']}pts")
else:
    print("❌ 创建失败，可能已存在")

conn.close()