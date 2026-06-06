import sqlite3
conn = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
# Check if raw_script column exists
cols = [r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()]
if 'raw_script' not in cols:
    conn.execute("ALTER TABLE projects ADD COLUMN raw_script TEXT DEFAULT ''")
    conn.commit()
    print("Added raw_script column")
else:
    print("raw_script column already exists")
conn.close()
