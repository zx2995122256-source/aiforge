import sqlite3, time

db_path = '/home/ubuntu/aiforge/backend/data/aiforge.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

now = time.time()
rows = conn.execute("""
    SELECT id, user_id, task_type, model, status, points_cost, 
           oiioii_task_id, created_at, error
    FROM tasks 
    WHERE status IN ('running', 'pending')
    ORDER BY id DESC
    LIMIT 20
""").fetchall()

if not rows:
    print("No stuck tasks found")
else:
    print(f"Found {len(rows)} stuck tasks:")
    for r in rows:
        elapsed = int(now - r['created_at']) if r['created_at'] else 0
        print(f"  #{r['id']} status={r['status']} model={r['model']} oiioii_id={r['oiioii_task_id']} "
              f"cost={r['points_cost']} elapsed={elapsed}s ({elapsed//60}min) "
              f"error={r['error'][:50] if r['error'] else 'none'}")

conn.close()
