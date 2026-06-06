import sqlite3, json
for path in ['/home/ubuntu/aiforge/backend/aiforge.db', '/home/ubuntu/aiforge/backend/data/aiforge.db']:
    print(f"\n=== {path} ===")
    try:
        conn = sqlite3.connect(path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print("Tables:", [t[0] for t in tables])
        if 'projects' in [t[0] for t in tables]:
            rows = conn.execute('SELECT id, name, phase, results_json FROM projects ORDER BY id DESC LIMIT 3').fetchall()
            for r in rows:
                d = json.loads(r[3]) if r[3] else {}
                keys = list(d.keys())
                summary = {}
                for k, v in d.items():
                    if isinstance(v, list):
                        done = sum(1 for x in v if x.get('status') == 'completed')
                        summary[k] = f"{done}/{len(v)} done"
                print(f"  Project #{r[0]} '{r[1]}' phase={r[2]}: keys={keys}, {summary}")
        conn.close()
    except Exception as e:
        print(f"  Error: {e}")
