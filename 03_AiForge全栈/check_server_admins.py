import sqlite3, os

# Check server's db
db_path = "/home/ubuntu/aiforge/backend/data/aiforge.db"
if not os.path.exists(db_path):
    db_path = "/home/ubuntu/aiforge/backend/aiforge.db"

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, email, nickname, role, points FROM users ORDER BY id LIMIT 20").fetchall()
print(f"DB: {db_path}")
for r in rows:
    role_mark = "ADMIN" if r["role"] == "admin" else "user"
    print(f"  {role_mark:5s} | ID:{r['id']:3d} | {r['email']:30s} | {r['points']:>7d}pts | {r['nickname']}")
conn.close()