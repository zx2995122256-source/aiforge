filepath = '/home/ubuntu/oiioii/core/engine.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add semaphore in __init__
old_init = '''class GenEngine:
    def __init__(self, pool: AccountPool, auto_register: bool = True):
        self.pool = pool
        self.auto_register = auto_register
        self._on_complete_callbacks: list[Callable] = []
        self._claimed_uris = {}
        self._claim_lock = threading.Lock()'''

new_init = '''class GenEngine:
    def __init__(self, pool: AccountPool, auto_register: bool = True):
        self.pool = pool
        self.auto_register = auto_register
        self._on_complete_callbacks: list[Callable] = []
        self._claimed_uris = {}
        self._claim_lock = threading.Lock()
        from config import MAX_CONCURRENT_GEN
        self._concurrency_sem = threading.Semaphore(MAX_CONCURRENT_GEN)'''

content = content.replace(old_init, new_init, 1)

# 2. Add semaphore acquire at start of _run_task
old_run = '''    def _run_task(self, task_db_id: int, task_type: str, model_name: str,
                  prompt: str, ratio: str, resolution: str, duration: int,
                  client: OiioiiClient, points_before: int, cost: int,
                  reference_images: list = None, model_timeout: int = 300,
                  min_points: int = 0, reference_video: str = ""):
        TaskDB.update_status(task_db_id, "processing")
        self._notify(task_db_id, "processing")

        try:'''

new_run = '''    def _run_task(self, task_db_id: int, task_type: str, model_name: str,
                  prompt: str, ratio: str, resolution: str, duration: int,
                  client: OiioiiClient, points_before: int, cost: int,
                  reference_images: list = None, model_timeout: int = 300,
                  min_points: int = 0, reference_video: str = ""):
        self._concurrency_sem.acquire()
        TaskDB.update_status(task_db_id, "processing")
        self._notify(task_db_id, "processing")

        try:'''

content = content.replace(old_run, new_run, 1)

# 3. Add finally block with semaphore release
old_except = '''        except Exception as e:
            print(f"[Engine] Task #{task_db_id}: exception - {e}")
            import traceback
            traceback.print_exc()
            AccountDB.refund_points(client.account_id, cost)
            TaskDB.update_status(task_db_id, "failed", error_message=str(e))
            self._notify(task_db_id, "failed", str(e))

    def get_task'''

new_except = '''        except Exception as e:
            print(f"[Engine] Task #{task_db_id}: exception - {e}")
            import traceback
            traceback.print_exc()
            AccountDB.refund_points(client.account_id, cost)
            TaskDB.update_status(task_db_id, "failed", error_message=str(e))
            self._notify(task_db_id, "failed", str(e))
        finally:
            self._concurrency_sem.release()

    def get_task'''

content = content.replace(old_except, new_except, 1)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK - added concurrency semaphore")
