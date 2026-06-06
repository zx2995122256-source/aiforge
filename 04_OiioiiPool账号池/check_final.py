import sqlite3
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id, model_name, status, error_message FROM tasks WHERE id >= 1587 ORDER BY id").fetchall()
for r in rows:
    d = dict(r)
    err = str(d.get("error_message",""))[:80]
    icon = "OK" if d["status"] == "completed" else ("..." if d["status"] in ("submitted","processing") else "FAIL")
    print(f"#{d['id']} {d['model_name']}: {d['status']} {icon} {('err='+err) if err else ''}")
conn.close()
