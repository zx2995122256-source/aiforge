import sqlite3
c = sqlite3.connect('/home/ubuntu/oiioii/data/oiioii_pool.db')
r = c.execute("SELECT video_used, COUNT(*), SUM(points_remaining) FROM accounts WHERE status='active' GROUP BY video_used").fetchall()
print("video_used | count | total_points")
for row in r:
    print(f"  {row[0]}       | {row[1]:>5} | {row[2]:>10}")
r2 = c.execute("SELECT COUNT(*) FROM tasks WHERE status='processing'").fetchone()
print(f"\nProcessing tasks: {r2[0]}")
r3 = c.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()
print(f"Pending tasks: {r3[0]}")
r4 = c.execute("SELECT COUNT(*) FROM tasks WHERE status='completed'").fetchone()
print(f"Completed tasks: {r4[0]}")
r5 = c.execute("SELECT COUNT(*) FROM tasks WHERE status='failed'").fetchone()
print(f"Failed tasks: {r5[0]}")
