import sqlite3
db_path = "/home/ubuntu/aiforge/backend/data/aiforge.db"
conn = sqlite3.connect(db_path)
cols = conn.execute("PRAGMA table_info(users)").fetchall()
for c in cols:
    print(c)
conn.close()