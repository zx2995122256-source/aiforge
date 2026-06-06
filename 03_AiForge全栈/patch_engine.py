import re

filepath = '/home/ubuntu/oiioii/core/engine.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add _is_video_task flag after "self._notify(task_db_id, "processing")"
# Find the second occurrence of 'self._notify(task_db_id, "processing")'
old = '''        TaskDB.update_status(task_db_id, "processing")
        self._notify(task_db_id, "processing")

        try:'''

new = '''        TaskDB.update_status(task_db_id, "processing")
        self._notify(task_db_id, "processing")

        # Track if this is a video task so we can reset video_used when done
        _is_video_task = (task_type == "video")

        try:'''

content = content.replace(old, new, 1)

# 2. Add finally block to reset video_used
old_end = '''        except Exception as e:
            print(f"[Engine] Task #{task_db_id}: exception - {e}")
            import traceback
            traceback.print_exc()
            AccountDB.refund_points(client.account_id, cost)
            TaskDB.update_status(task_db_id, "failed", error_message=str(e))
            self._notify(task_db_id, "failed", str(e))

    def get_task(self, task_db_id: int) -> Optional[dict]:'''

new_end = '''        except Exception as e:
            print(f"[Engine] Task #{task_db_id}: exception - {e}")
            import traceback
            traceback.print_exc()
            AccountDB.refund_points(client.account_id, cost)
            TaskDB.update_status(task_db_id, "failed", error_message=str(e))
            self._notify(task_db_id, "failed", str(e))
        finally:
            # Reset video_used so this account can be reused for future video tasks
            if _is_video_task:
                AccountDB.reset_video_used(client.account_id)

    def get_task(self, task_db_id: int) -> Optional[dict]:'''

content = content.replace(old_end, new_end, 1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK - patched engine.py")
