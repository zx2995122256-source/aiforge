#!/usr/bin/env python3
import sqlite3, json
c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
r = c.execute('SELECT id,name,results_json FROM projects ORDER BY id DESC LIMIT 1').fetchone()
if r:
    print(f"Project #{r[0]}: {r[1]}")
    results = json.loads(r[2]) if r[2] else {}
    for k, v in results.items():
        if isinstance(v, list):
            statuses = [item.get('status','?') for item in v]
            print(f"  {k}: {statuses}")
        else:
            print(f"  {k}: {v}")
c.close()
