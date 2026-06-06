import sqlite3, requests

# 1. Clean OiioiiPool stuck tasks
pool_db = r"C:\Users\Administrator\Documents\OiioiiPool\data\oiioii_pool.db"
conn = sqlite3.connect(pool_db)
cnt = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
proc = conn.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('processing','pending','running')").fetchone()[0]
print(f"OiioiiPool: total={cnt} processing={proc}")
conn.execute("DELETE FROM tasks WHERE status IN ('processing','pending','running')")
conn.commit()
conn.close()
print("Cleaned OiioiiPool stuck tasks ✅")

# 2. Clean AiForge stuck tasks
af_db = r"C:\Users\Administrator\Documents\AiForge\backend\data\aiforge.db"
conn2 = sqlite3.connect(af_db)
cnt2 = conn2.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
run2 = conn2.execute("SELECT COUNT(*) FROM tasks WHERE status='running'").fetchone()[0]
print(f"AiForge: total={cnt2} running={run2}")
conn2.execute("DELETE FROM tasks WHERE status='running'")
conn2.commit()
conn2.close()
print("Cleaned AiForge stuck tasks ✅")

# 3. Now restart OiioiiPool (user will see it in the terminal)
print("\n✅ 所有卡住的任务已清除")
print("现在启动 OiioiiPool 和 AiForge 后端...")