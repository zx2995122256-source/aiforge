import sqlite3, json

db_path = '/home/ubuntu/aiforge/backend/data/aiforge.db'
conn = sqlite3.connect(db_path)

rows = conn.execute('SELECT id, results_json FROM projects').fetchall()
for r in rows:
    pid = r[0]
    if not r[1]:
        continue
    d = json.loads(r[1])
    changed = False

    # Migrate phase1 -> phase2 (old asset generation key)
    if 'phase1' in d and 'phase2' not in d:
        d['phase2'] = d.pop('phase1')
        changed = True
        print(f"  Project #{pid}: phase1 -> phase2 migrated")

    if changed:
        conn.execute('UPDATE projects SET results_json=? WHERE id=?',
                     (json.dumps(d, ensure_ascii=False), pid))

conn.commit()
conn.close()
print("Migration done!")
