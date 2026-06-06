#!/usr/bin/env python3
import sqlite3
c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
# Give video_gen user 500000 points
c.execute("UPDATE users SET points=500000 WHERE email='video_gen@aiforge.local'")
c.commit()
r = c.execute("SELECT id,email,points FROM users WHERE email='video_gen@aiforge.local'").fetchone()
print(f"Updated: {r}")
c.close()
