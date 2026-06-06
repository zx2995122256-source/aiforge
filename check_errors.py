#!/usr/bin/env python3
import sqlite3, json
c = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
r = c.execute('SELECT results_json FROM projects WHERE id=26').fetchone()
results = json.loads(r[0]) if r and r[0] else {}
for phase_key in ['phase4', 'phase2']:
    phase_results = results.get(phase_key, [])
    if phase_results:
        print(f"\n=== {phase_key} ({len(phase_results)} items) ===")
        for i, item in enumerate(phase_results):
            status = item.get('status', '?')
            error = item.get('error', '')
            if status == 'failed' or error:
                print(f"  [{i}] status={status} error={error[:200]}")
            else:
                print(f"  [{i}] status={status}")
c.close()
