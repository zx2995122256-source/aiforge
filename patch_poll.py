import sys

with open('/home/ubuntu/aiforge/backend/api/generate.py', 'r') as f:
    content = f.read()

# Check if already patched
if 'CRASHED with exception' in content:
    print("Already patched with poll robustness fix")
    sys.exit(0)

# Find and replace _poll_oiioii function
old_func_start = 'def _poll_oiioii(task_id: int, aiforge_task_id: int, uid: int, cost: int):'
old_func_end = '@router.get("/models")'

start_idx = content.find(old_func_start)
if start_idx == -1:
    print("ERROR: Could not find _poll_oiioii function")
    sys.exit(1)

end_idx = content.find(old_func_end, start_idx)
if end_idx == -1:
    print("ERROR: Could not find end of _poll_oiioii function")
    sys.exit(1)

new_func = '''def _poll_oiioii(task_id: int, aiforge_task_id: int, uid: int, cost: int):
    from models.db import add_points
    start = time.time()
    max_wait = 1800  # 30 min timeout
    print(f"[Poll] #{aiforge_task_id} OiioiiPool #{task_id}: started, max_wait={max_wait}s")
    try:
        while time.time() - start < max_wait:
            try:
                result = proxy.get_task(task_id)
            except Exception as e:
                print(f"[Poll] #{aiforge_task_id}: proxy.get_task exception: {e}, retrying...")
                time.sleep(10)
                continue

            if result.get("error"):
                print(f"[Poll] #{aiforge_task_id}: error={result['error'][:50]}, retrying...")
                time.sleep(5)
                continue
            status = result.get("status", "")
            elapsed = int(time.time() - start)
            if status == "completed":
                file_url = f"/api/gen/file/{task_id}"
                update_task(aiforge_task_id, "completed", file_url)
                print(f"[Poll] #{aiforge_task_id}: completed after {elapsed}s")
                return
            elif status == "failed":
                error_msg = result.get("error", result.get("message", ""))
                update_task(aiforge_task_id, "failed", "", error=error_msg)
                add_points(uid, cost, f"\\u4efb\\u52a1\\u5931\\u8d25\\u9000\\u8fd8-#{aiforge_task_id}")
                print(f"[Poll] #{aiforge_task_id}: failed after {elapsed}s, error={error_msg[:80]}")
                return
            if elapsed % 60 == 0:
                print(f"[Poll] #{aiforge_task_id}: still {status} after {elapsed}s")
            time.sleep(5)
        # Timeout
        print(f"[Poll] #{aiforge_task_id}: timeout after {max_wait}s")
        update_task(aiforge_task_id, "timeout", "", error=f"\\u4efb\\u52a1\\u8d85\\u65f6({max_wait}s)\\uff0c\\u79ef\\u5206\\u5df2\\u9000\\u8fd8")
        add_points(uid, cost, f"\\u4efb\\u52a1\\u8d85\\u65f6\\u9000\\u8fd8-#{aiforge_task_id}")
    except Exception as e:
        # Catch-all: if poll thread crashes, still mark as failed and refund
        print(f"[Poll] #{aiforge_task_id}: CRASHED with exception: {e}")
        try:
            update_task(aiforge_task_id, "failed", "", error="\\u5185\\u90e8\\u9519\\u8bef\\uff0c\\u79ef\\u5206\\u5df2\\u9000\\u8fd8")
            add_points(uid, cost, f"\\u5185\\u90e8\\u9519\\u8bef\\u9000\\u8fd8-#{aiforge_task_id}")
        except:
            print(f"[Poll] #{aiforge_task_id}: CRITICAL - failed to refund after crash!")


'''

content = content[:start_idx] + new_func + content[end_idx:]

with open('/home/ubuntu/aiforge/backend/api/generate.py', 'w') as f:
    f.write(content)

print("PATCHED: generate.py with poll robustness fix")
