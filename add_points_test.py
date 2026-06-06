import sqlite3
conn = sqlite3.connect('backend/data/aiforge.db')
c = conn.cursor()
c.execute("UPDATE users SET points = 500000 WHERE email = 'test@test.com'")
conn.commit()
c.execute("SELECT email, points FROM users WHERE email = 'test@test.com'")
print("Updated:", c.fetchone())
