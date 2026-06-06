import sqlite3, hashlib, time, os
db_path = "/home/ubuntu/aiforge/backend/data/aiforge.db"

# hash matching aiforge backend (SHA256 of email+password)
email = "sci_test@aiforge.ai"
pwd_raw = "sci2025pw"
pw_hash = hashlib.sha256((email + ":" + pwd_raw).encode()).hexdigest()

conn = sqlite3.connect(db_path)
try:
    conn.execute("DELETE FROM users WHERE email=?", (email,))
    conn.execute(
        "INSERT INTO users (email, password, nickname, points, role, created_at) VALUES (?,?,?,?,?,?)",
        (email, pw_hash, "SciFiTester", 500000, "user", time.time())
    )
    conn.commit()
    print(f"OK: {email} / {pwd_raw} (500000 pts)")
except Exception as e:
    print(f"Error: {e}")
conn.close()