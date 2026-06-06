filepath = '/home/ubuntu/oiioii/core/engine.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add finally block - find the exact text
old = '''            self._notify(task_db_id, "failed", str(e))
    def get_task(self, task_db_id: int) -> Optional[dict]:'''

new = '''            self._notify(task_db_id, "failed", str(e))
        finally:
            self._concurrency_sem.release()

    def get_task(self, task_db_id: int) -> Optional[dict]:'''

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK - added finally block")
else:
    print("ERROR - pattern not found")
    # Show what's around line 313
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'failed", str(e)' in line:
            print(f"Line {i+1}: {line}")
        if 'def get_task' in line:
            print(f"Line {i+1}: {line}")
