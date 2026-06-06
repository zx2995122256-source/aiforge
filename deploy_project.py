import sys

# 1. Copy project.py
with open('/home/ubuntu/aiforge/backend/api/project.py', 'w') as f:
    with open('/tmp/project.py', 'r') as f2:
        f.write(f2.read())
print("1. project.py deployed")

# 2. Patch db.py - add projects table
with open('/home/ubuntu/aiforge/backend/models/db.py', 'r') as f:
    content = f.read()

if 'CREATE TABLE IF NOT EXISTS projects' not in content:
    # Just append the CREATE TABLE after the last conn.commit()
    old_commit = "    conn.commit()\n    conn.close()"
    projects_sql = """    # Projects table for 一键成片
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT NOT NULL, script TEXT DEFAULT '', video_model TEXT DEFAULT 'Gemini Omni', image_model TEXT DEFAULT 'GPT-Image2', ratio TEXT DEFAULT '16:9', resolution TEXT DEFAULT '720p', duration INTEGER DEFAULT 10, segments_json TEXT DEFAULT '[]', assets_json TEXT DEFAULT '[]', phase INTEGER DEFAULT 0, results_json TEXT DEFAULT '{}', created_at REAL, updated_at REAL)")
    except Exception:
        pass
    """
    if old_commit in content:
        content = content.replace(old_commit, projects_sql + "    conn.commit()\n    conn.close()")
        with open('/home/ubuntu/aiforge/backend/models/db.py', 'w') as f:
            f.write(content)
        print("2. db.py patched with projects table")
    else:
        print("2. db.py pattern not found")
else:
    print("2. db.py already has projects table")

# 3. Patch main.py - add project router
with open('/home/ubuntu/aiforge/backend/main.py', 'r') as f:
    content = f.read()

if 'project_router' not in content:
    content = content.replace(
        "from api.pool import router as pool_router",
        "from api.pool import router as pool_router\nfrom api.project import router as project_router"
    )
    content = content.replace(
        "app.include_router(pool_router)",
        "app.include_router(pool_router)\napp.include_router(project_router)"
    )
    with open('/home/ubuntu/aiforge/backend/main.py', 'w') as f:
        f.write(content)
    print("3. main.py patched with project router")
else:
    print("3. main.py already has project router")

print("\nAll patches applied!")
