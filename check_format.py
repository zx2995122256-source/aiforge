import sqlite3, json
conn = sqlite3.connect('backend/data/aiforge.db')
c = conn.cursor()
c.execute("PRAGMA table_info(users)")
print("Users columns:", [r[1] for r in c.fetchall()])
