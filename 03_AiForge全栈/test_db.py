import sqlite3
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
rows = conn.execute('SELECT id, email FROM users LIMIT 5').fetchall()
for r in rows:
    print(r)
print("---")
rows = conn.execute('SELECT id, name FROM projects LIMIT 5').fetchall()
for r in rows:
    print(r)
