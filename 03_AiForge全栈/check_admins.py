import sqlite3, os

db_path = r"c:\Users\Administrator\Documents\锤子Aicg\03_AiForge全栈\backend\data\aiforge.db"
if not os.path.exists(db_path):
    db_path = r"c:\Users\Administrator\Documents\锤子Aicg\03_AiForge全栈\backend\aiforge.db"
    print(f"Trying: {db_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, email, nickname, role, points FROM users ORDER BY id").fetchall()
for r in rows:
    role_mark = "ADMIN" if r["role"] == "admin" else "user"
    print(f"  {role_mark:5s} | ID:{r['id']:3d} | {r['email']:30s} | {r['points']:>7d}pts | {r['nickname']}")
conn.close()