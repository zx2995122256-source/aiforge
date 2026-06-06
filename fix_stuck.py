import sqlite3, time

db_path = '/home/ubuntu/aiforge/backend/data/aiforge.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

now = time.time()

rows = conn.execute("""
    SELECT id, user_id, task_type, model, status, points_cost, 
           oiioii_task_id, created_at
    FROM tasks 
    WHERE status IN ('running', 'pending')
""").fetchall()

if not rows:
    print("No stuck tasks to fix")
else:
    print(f"Fixing {len(rows)} stuck tasks:")
    for r in rows:
        elapsed = int(now - r['created_at']) if r['created_at'] else 0
        cost = r['points_cost']
        uid = r['user_id']
        tid = r['id']
        
        conn.execute("UPDATE tasks SET status='timeout', error='任务超时，积分已退还' WHERE id=?", (tid,))
        
        if cost and cost > 0:
            conn.execute("UPDATE users SET points = points + ? WHERE id=?", (cost, uid))
        
        print(f"  #{tid} model={r['model']} cost={cost} elapsed={elapsed//60}min -> timeout + refund")

    conn.commit()
    print("Done!")

conn.close()
