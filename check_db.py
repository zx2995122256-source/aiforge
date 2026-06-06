import sqlite3, json
conn = sqlite3.connect('backend/data/aiforge.db')
c = conn.cursor()
c.execute("SELECT id, email, nickname, points, role FROM users LIMIT 30")
for row in c.fetchall():
    print(row)
