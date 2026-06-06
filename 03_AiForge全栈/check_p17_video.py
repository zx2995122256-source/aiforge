import sqlite3, json
db = sqlite3.connect('/home/ubuntu/aiforge/backend/data/aiforge.db')
db.row_factory = sqlite3.Row
row = db.execute("SELECT id, name, results_json, video_model, ratio, resolution, duration FROM projects WHERE id=17").fetchone()
if row:
    print(f"Model: {row['video_model']}, Ratio: {row['ratio']}, Resolution: {row['resolution']}, Duration: {row['duration']}")
    results = json.loads(row['results_json'] or '{}')
    print("\n=== Phase4 (videos) - actual submitted prompts ===")
    for i, r in enumerate(results.get('phase4', [])):
        print(f"\n--- Seg {i}: {r.get('title','')} ---")
        print(f"Status: {r.get('status')}")
        print(f"Error: {r.get('error','')[:200]}")
        print(f"Prompt: {r.get('prompt','')[:500]}")
        print(f"Ref images: {r.get('reference_images','')[:200]}")
        print(f"Oiioii task ID: {r.get('oiioii_task_id')}")
db.close()
