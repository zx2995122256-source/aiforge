import sqlite3
conn = sqlite3.connect("/home/ubuntu/oiioii/data/oiioii_pool.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT id,task_type,model_name,status,error_message,created_at FROM tasks WHERE task_type='image' ORDER BY id DESC LIMIT 15").fetchall()
for r in rows:
    d = dict(r)
    print(f"#{d['id']} {d['model_name']} {d['status']} err={d.get('error_message','')[:80]}")
conn.close()
