import sqlite3, json
db_path = "/home/ubuntu/aiforge/backend/data/aiforge.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id,email,nickname,points,role FROM users ORDER BY id LIMIT 10").fetchall()
print(json.dumps([dict(r) for r in rows], indent=2))
conn.close()
