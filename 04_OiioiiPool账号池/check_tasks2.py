import sqlite3, json
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
conn.row_factory = sqlite3.Row
for tid in [1569, 1570, 1571]:
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone()
    if row:
        d = dict(row)
        print(f"#{tid}:", json.dumps({k: str(v)[:100] for k,v in d.items()}, indent=2))
conn.close()
