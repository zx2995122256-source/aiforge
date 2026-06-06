import re

filepath = '/home/ubuntu/oiioii/core/engine.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Revert: remove _is_video_task flag
content = content.replace(
    '''        # Track if this is a video task so we can reset video_used when done
        _is_video_task = (task_type == "video")

        try:''',
    '''        try:''',
    1
)

# Revert: remove finally block
content = content.replace(
    '''        finally:
            # Reset video_used so this account can be reused for future video tasks
            if _is_video_task:
                AccountDB.reset_video_used(client.account_id)

    def get_task''',
    '''    def get_task''',
    1
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK - reverted engine.py")
