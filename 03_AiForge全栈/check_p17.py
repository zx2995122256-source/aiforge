import sqlite3, json
db = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
db.row_factory = sqlite3.Row
row = db.execute("SELECT id, name, results_json FROM projects WHERE id=17").fetchone()
if row:
    results = json.loads(row['results_json'] or '{}')
    print("=== Phase2 (assets) ===")
    for i, r in enumerate(results.get('phase2', [])):
        print(f"  Asset {i}: name={r.get('name','')}, status={r.get('status')}, has_result={bool(r.get('result_url'))}")
    print("\n=== Phase3 (storyboards) ===")
    for i, r in enumerate(results.get('phase3', [])):
        print(f"  Seg {i}: title={r.get('title','')}, status={r.get('status')}, error={r.get('error','')[:200] if r.get('error') else ''}")
        print(f"          prompt={r.get('prompt','')[:150]}")
        print(f"          ref_images={r.get('reference_images','')[:100]}")
    print("\n=== Phase4 (videos) ===")
    for i, r in enumerate(results.get('phase4', [])):
        print(f"  Seg {i}: status={r.get('status')}, error={r.get('error','')[:100] if r.get('error') else ''}")
db.close()
