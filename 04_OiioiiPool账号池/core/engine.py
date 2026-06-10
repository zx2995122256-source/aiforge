import time
import threading
from typing import Optional, Callable
from core.client import OiioiiClient
from core.pool import AccountPool
from core.db import TaskDB, AccountDB
from config import IMAGE_MODELS, VIDEO_MODELS_DIRECT, POINTS_WARNING_THRESHOLD, get_model_cost, MAX_CONCURRENT_GEN


class GenEngine:
    def __init__(self, pool: AccountPool, auto_register: bool = True):
        self.pool = pool
        self.auto_register = auto_register
        self._on_complete_callbacks: list[Callable] = []
        self._claimed_uris = {}
        self._claim_lock = threading.Lock()

        # 并发控制
        self._submit_semaphore = threading.Semaphore(MAX_CONCURRENT_GEN)
        self._active_tasks = {}  # task_db_id -> {client, remote_task_id, ...}
        self._active_lock = threading.Lock()

        # 轮询线程
        self._poller_running = False
        self._poller_thread = None
        self._poller_heartbeat = 0  # 看门狗用
        self._start_poller()

        # 看门狗线程
        self._watchdog_running = True
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    def _claim_uri(self, account_id: int, uri: str) -> bool:
        with self._claim_lock:
            if account_id not in self._claimed_uris:
                self._claimed_uris[account_id] = set()
            if uri in self._claimed_uris[account_id]:
                return False
            self._claimed_uris[account_id].add(uri)
            return True

    def _cleanup_account_claims(self, account_id: int):
        self._claimed_uris.pop(account_id, None)

    def on_complete(self, callback: Callable):
        self._on_complete_callbacks.append(callback)

    def _notify(self, task_db_id: int, status: str, result: str = ""):
        for cb in self._on_complete_callbacks:
            try:
                cb(task_db_id, status, result)
            except Exception:
                pass

    def _ensure_available_account(self, min_points: int, prefer_lowest: bool = False,
                                   video_pool: bool = False,
                                   fallback_any: bool = False) -> Optional[OiioiiClient]:
        client = self.pool.get_available_client(
            min_points=min_points, prefer_lowest=prefer_lowest,
            video_pool=video_pool, fallback_any=fallback_any
        )
        if client:
            return client
        if not self.auto_register:
            print(f"[Engine] No account with {min_points}+ points, auto-register disabled")
            return None
        print(f"[Engine] No account with {min_points}+ points, auto-registering...")
        reg_result = self.pool.auto_register()
        if not reg_result["success"]:
            print(f"[Engine] Auto-register failed: {reg_result['error']}")
            return None
        print(f"[Engine] Auto-registered #{reg_result['account_id']} pts={reg_result['points']}")
        return self.pool.get_available_client(min_points=min_points)

    def cleanup_stale_tasks(self):
        stale = TaskDB.get_pending()
        for t in stale:
            if t["status"] == "processing":
                elapsed = time.time() - t.get("created_at", 0)
                if elapsed > 600:
                    remote_tid = t.get("task_id", "")
                    if remote_tid:
                        print(f"[Engine] Stale task #{t['id']} has remote_id={remote_tid[:30]}, attempting recovery poll...")
                        try:
                            acct = AccountDB.get_by_id(t["account_id"])
                            if acct:
                                c = OiioiiClient(acct["email"], acct["password"],
                                                 account_id=acct["id"],
                                                 workspace_id=acct.get("workspace_id", ""))
                                if c.login():
                                    skip_uris = c.get_known_uris()
                                    status, uri = c.poll_result(
                                        "video" if t["task_type"] == "video" else "image",
                                        skip_uris, max_wait=30, interval=5,
                                        remote_task_id=remote_tid)
                                    if status == "completed" and uri:
                                        ok_dl, local_path = c.download(uri)
                                        TaskDB.update_status(t["id"], "completed",
                                                             task_id=remote_tid,
                                                             result_uri=uri,
                                                             local_path=local_path if ok_dl else "")
                                        print(f"[Engine] Stale task #{t['id']} RECOVERED: {uri[:60]}")
                                        continue
                        except Exception as e:
                            print(f"[Engine] Stale task #{t['id']} recovery failed: {e}")
                    print(f"[Engine] Cleaning stale task #{t['id']} (processing for {int(elapsed)}s)")
                    TaskDB.update_status(t["id"], "failed", error_message="Process restarted, task lost")

    def submit(self, task_type: str, model_name: str, prompt: str,
               ratio: str = "16:9", resolution: str = "2K",
               duration: int = 5, reference_images: list = None,
               reference_video: str = "", reference_map: dict = None) -> dict:
        model_info = (IMAGE_MODELS if task_type == "image" else VIDEO_MODELS_DIRECT).get(model_name)
        if not model_info:
            return {"success": False, "error": f"Unknown model: {model_name}"}

        cost = get_model_cost(model_name, duration, resolution)

        min_points = cost
        is_video = (task_type == "video")

        for attempt in range(5):
            client = self._ensure_available_account(
                min_points,
                prefer_lowest=(task_type == "image"),
                video_pool=is_video,
                fallback_any=(not is_video)  # 视频任务不 fallback，避免选低积分账号
            )
            if not client:
                return {"success": False, "error": "No available account and auto-register failed"}

            real_pts = client.get_points()
            if real_pts >= min_points:
                break

            print(f"[Engine] Account #{client.account_id} real_pts={real_pts} < min_points={min_points}, marking exhausted")
            AccountDB.update_points(client.account_id, real_pts)
            AccountDB.update_status(client.account_id, "exhausted")
        else:
            return {"success": False, "error": f"All accounts have insufficient points (need {min_points} for {task_type})"}

        if not AccountDB.try_deduct_points(client.account_id, cost):
            print(f"[Engine] Account #{client.account_id} deduct failed, trying next...")
            AccountDB.update_status(client.account_id, "exhausted")
            client = self._ensure_available_account(min_points, prefer_lowest=(task_type == "image"),
                                                     video_pool=False, fallback_any=True)
            if not client:
                return {"success": False, "error": "All accounts exhausted, auto-register failed"}
            if not AccountDB.try_deduct_points(client.account_id, cost):
                return {"success": False, "error": "All accounts exhausted"}

        print(f"[Engine] Submit {task_type} task: model={model_name} dur={duration}s res={resolution} cost={cost} account=#{client.account_id} pts={real_pts}")

        task_db_id = TaskDB.add(
            account_id=client.account_id,
            task_type=task_type,
            model_name=model_name,
            prompt=prompt,
            ratio=ratio,
            resolution=resolution,
            duration=duration,
            points_cost=cost
        )

        # 提交到线程池（受信号量限制并发数）
        t = threading.Thread(
            target=self._submit_task,
            args=(task_db_id, task_type, model_name, prompt, ratio,
                  resolution, duration, client, real_pts, cost,
                  reference_images, model_info.get("timeout", 300), min_points,
                  reference_video, reference_map),
            daemon=True
        )
        t.start()
        return {"success": True, "task_db_id": task_db_id}

    def _submit_task(self, task_db_id: int, task_type: str, model_name: str,
                     prompt: str, ratio: str, resolution: str, duration: int,
                     client: OiioiiClient, points_before: int, cost: int,
                     reference_images: list = None, model_timeout: int = 300,
                     min_points: int = 0, reference_video: str = "",
                     reference_map: dict = None):
        """提交阶段：调 Oiioii API 提交任务，成功后注册到轮询表"""
        with self._submit_semaphore:
            TaskDB.update_status(task_db_id, "processing")
            self._notify(task_db_id, "processing")

            try:
                skip_uris = set()
                known_uris = client.get_known_uris()
                skip_uris.update(known_uris)
                with self._claim_lock:
                    existing = self._claimed_uris.get(client.account_id, set())
                    skip_uris.update(existing)
                print(f"[Engine] Task #{task_db_id}: skip_uris={len(skip_uris)} (known={len(known_uris)} claimed={len(existing)})")

                manual_refresh = False
                if task_type == "image":
                    ok, result, uploaded_refs = client.generate_image(
                        prompt, model_name, ratio, resolution,
                        reference_images=reference_images)
                    skip_uris.update(uploaded_refs)
                else:
                    ok, result, manual_refresh = client.generate_video(
                        prompt, model_name, ratio, duration, resolution,
                        reference_images=reference_images,
                        reference_video=reference_video,
                        reference_map=reference_map)
                    if reference_images:
                        uploaded_img_refs = client._refs_to_data_urls(reference_images, model_name)
                        skip_uris.update(uploaded_img_refs)
                    if reference_video:
                        video_uri = client._resolve_video_ref(reference_video)
                        if video_uri:
                            skip_uris.add(video_uri)

                if not ok:
                    print(f"[Engine] Task #{task_db_id}: submit failed - {result}")
                    AccountDB.refund_points(client.account_id, cost)
                    if result == "INSUFFICIENT_POINTS":
                        AccountDB.update_status(client.account_id, "exhausted")
                        retry_min = min_points if min_points > 0 else cost
                        if self.auto_register:
                            new_client = self._ensure_available_account(retry_min, prefer_lowest=(task_type == "image"),
                                                                         video_pool=False,
                                                                         fallback_any=True)
                            if new_client:
                                if not AccountDB.try_deduct_points(new_client.account_id, cost):
                                    TaskDB.update_status(task_db_id, "failed", error_message="Insufficient points")
                                    self._notify(task_db_id, "failed", "Insufficient points")
                                    return
                                print(f"[Engine] Task #{task_db_id}: retrying with account #{new_client.account_id}")
                                TaskDB.update_status(task_db_id, "pending")
                                self._submit_task(task_db_id, task_type, model_name, prompt,
                                                  ratio, resolution, duration, new_client,
                                                  new_client.get_points(), cost, reference_images,
                                                  model_timeout, min_points, reference_video)
                                return
                        TaskDB.update_status(task_db_id, "failed",
                                             error_message="Insufficient points")
                        self._notify(task_db_id, "failed", "Insufficient points")
                        return
                    TaskDB.update_status(task_db_id, "failed", error_message=result)
                    self._notify(task_db_id, "failed", result)
                    return

                remote_task_id = result
                TaskDB.update_status(task_db_id, "processing", task_id=remote_task_id)
                print(f"[Engine] Task #{task_db_id}: submitted, remote_id={remote_task_id}")

                # 注册到轮询表，交给集中轮询线程
                timeout = model_timeout * 2 if bool(reference_images) else model_timeout
                if bool(reference_video):
                    timeout = max(timeout, 1800)

                with self._active_lock:
                    self._active_tasks[task_db_id] = {
                        "client": client,
                        "remote_task_id": remote_task_id,
                        "task_type": task_type,
                        "points_before": points_before,
                        "cost": cost,
                        "skip_uris": skip_uris,
                        "timeout": timeout,
                        "manual_refresh": manual_refresh,
                        "submitted_at": time.time(),
                        "batch_done": False,  # batch_video 是否已尝试
                        "claim_retries": 0,   # uri 抢占重试次数
                        "fail_count": 0,      # 失败重试次数
                        # 重试所需的参数
                        "model_name": model_name,
                        "min_points": min_points,
                        "duration": duration,
                        "resolution": resolution,
                        "ratio": ratio,
                        "reference_images": reference_images,
                        "reference_video": reference_video,
                    }

            except Exception as e:
                print(f"[Engine] Task #{task_db_id}: submit exception - {e}")
                import traceback
                traceback.print_exc()
                AccountDB.refund_points(client.account_id, cost)
                TaskDB.update_status(task_db_id, "failed", error_message=str(e))
                self._notify(task_db_id, "failed", str(e))

    # ─── 集中轮询 ───

    def _start_poller(self):
        if self._poller_running:
            return
        self._poller_running = True
        self._poller_thread = threading.Thread(target=self._poller_loop, daemon=True)
        self._poller_thread.start()
        print("[Engine] Poller started")

    def _poller_loop(self):
        """单线程轮询所有 processing 任务"""
        while self._poller_running:
            try:
                self._poller_heartbeat = time.time()
                self._poll_once()
            except Exception as e:
                print(f"[Engine] Poller error: {e}")
                import traceback
                traceback.print_exc()
            time.sleep(10)  # 每10秒轮询一轮

    def _poll_once(self):
        with self._active_lock:
            task_ids = list(self._active_tasks.keys())

        if not task_ids:
            return

        completed_ids = []

        for task_db_id in task_ids:
            with self._active_lock:
                info = self._active_tasks.get(task_db_id)
            if not info:
                continue

            client = info["client"]
            remote_task_id = info["remote_task_id"]
            task_type = info["task_type"]
            skip_uris = info["skip_uris"]
            timeout = info["timeout"]
            submitted_at = info["submitted_at"]
            cost = info["cost"]
            points_before = info["points_before"]

            # 超时检查
            elapsed = time.time() - submitted_at
            if elapsed > timeout:
                print(f"[Engine] Task #{task_db_id}: timed out after {int(elapsed)}s")
                AccountDB.refund_points(client.account_id, cost)
                TaskDB.update_status(task_db_id, "failed",
                                     task_id=remote_task_id,
                                     error_message="Generation timed out")
                self._notify(task_db_id, "failed", "Generation timed out")
                completed_ids.append(task_db_id)
                continue

            # manualRefresh 任务：前 45 秒跳过轮询，给 API 留出生成时间
            if info.get("manual_refresh") and elapsed < 45:
                continue

            try:
                # 视频先尝试 batch_video 非阻塞查询
                if task_type == "video" and remote_task_id and not info["batch_done"]:
                    status, uri = client.check_batch_video_once(remote_task_id)
                    if status == "completed" and uri:
                        if self._claim_uri(client.account_id, uri):
                            self._finish_task(task_db_id, client, uri, remote_task_id, cost, points_before)
                            completed_ids.append(task_db_id)
                            continue
                        else:
                            skip_uris.add(uri)
                            info["claim_retries"] += 1
                    elif status == "failed":
                        # 可重试错误：不立即失败，让下面的通用 check_result_once 再确认一次
                        retriable_batch = ("Internal Error" in str(uri) or
                                           "No taskId" in str(uri) or
                                           "Connection aborted" in str(uri))
                        if retriable_batch:
                            info["batch_done"] = True  # 切换到 check_result
                            print(f"[Engine] Task #{task_db_id}: batch_video fail (retriable), switching to check_result")
                            # 不加入 completed_ids，下面 check_result_once 会继续处理
                        else:
                            AccountDB.refund_points(client.account_id, cost)
                            TaskDB.update_status(task_db_id, "failed",
                                                 task_id=remote_task_id, error_message=uri)
                            self._notify(task_db_id, "failed", uri)
                            completed_ids.append(task_db_id)
                            continue
                    else:
                        # batch 还没结果，超过一半超时后切换到 poll_result
                        if elapsed > timeout // 2:
                            info["batch_done"] = True
                            print(f"[Engine] Task #{task_db_id}: batch_video no result, switching to check_result")

                # 通用非阻塞查询
                asset_type = "image" if task_type == "image" else "video"
                status, uri = client.check_result_once(asset_type, skip_uris, remote_task_id=remote_task_id)

                if status == "completed" and uri:
                    if self._claim_uri(client.account_id, uri):
                        self._finish_task(task_db_id, client, uri, remote_task_id, cost, points_before)
                        completed_ids.append(task_db_id)
                        continue
                    else:
                        # URI 被别的任务占了，跳过这个 URI 继续轮询
                        skip_uris.add(uri)
                        info["claim_retries"] += 1
                        if info["claim_retries"] > 3:
                            print(f"[Engine] Task #{task_db_id}: can't claim URI after 3 retries, marking failed")
                            AccountDB.refund_points(client.account_id, cost)
                            TaskDB.update_status(task_db_id, "failed",
                                                 task_id=remote_task_id,
                                                 error_message="URI claim conflict")
                            self._notify(task_db_id, "failed", "URI claim conflict")
                            completed_ids.append(task_db_id)
                elif status == "failed":
                    # 可重试错误：换账号重试
                    retriable = ("Internal Error" in str(uri) or
                                 "No taskId" in str(uri) or
                                 "Connection aborted" in str(uri) or
                                 "Generation job finished with state: FAILED" in str(uri) or
                                 "timed out" in str(uri).lower() or
                                 "timeout" in str(uri).lower())
                    info["fail_count"] = info.get("fail_count", 0) + 1
                    should_retry = retriable and info["fail_count"] <= 2
                    retried = False
                    if should_retry:
                        print(f"[Engine] Task #{task_db_id}: transient fail (#{info['fail_count']}), retrying with different account. error={str(uri)[:80]}")
                        AccountDB.refund_points(client.account_id, cost)
                        # 获取新账号重试
                        retry_min = info.get("min_points", cost)
                        new_client = self._ensure_available_account(retry_min, prefer_lowest=(task_type == "image"),
                                                                     video_pool=False, fallback_any=True)
                        if new_client and new_client.account_id != client.account_id:
                            if AccountDB.try_deduct_points(new_client.account_id, cost):
                                # 重新提交
                                new_remote_id = ""
                                if task_type == "image":
                                    ok, new_remote_id, _ = new_client.generate_image(
                                        prompt=TaskDB.get_by_id(task_db_id)["prompt"],
                                        model_name=info.get("model_name", ""),
                                        ratio=info.get("ratio", "16:9"),
                                        resolution=info.get("resolution", "720p"),
                                        reference_images=info.get("reference_images", []))
                                else:
                                    ok, new_remote_id, _ = new_client.generate_video(
                                        prompt=TaskDB.get_by_id(task_db_id)["prompt"],
                                        model_name=info.get("model_name", ""),
                                        ratio=info.get("ratio", "16:9"),
                                        duration=info.get("duration", 5),
                                        resolution=info.get("resolution", "720p"),
                                        reference_images=info.get("reference_images", []),
                                        reference_video=info.get("reference_video", ""))
                                if ok and new_remote_id:
                                    print(f"[Engine] Task #{task_db_id}: retry submitted, new remote_id={new_remote_id}, account=#{new_client.account_id}")
                                    # 更新轮询表
                                    info["client"] = new_client
                                    info["remote_task_id"] = new_remote_id
                                    info["submitted_at"] = time.time()
                                    info["batch_done"] = False
                                    info["skip_uris"] = new_client.get_known_uris()
                                    info["cost"] = cost
                                    info["points_before"] = new_client.get_points()
                                    TaskDB.update_status(task_db_id, "processing", task_id=new_remote_id)
                                    retried = True  # 继续轮询，不加入 completed_ids
                                else:
                                    AccountDB.refund_points(new_client.account_id, cost)
                                    print(f"[Engine] Task #{task_db_id}: retry submit failed: {new_remote_id}")
                            else:
                                print(f"[Engine] Task #{task_db_id}: retry deduct failed")
                        if info["fail_count"] > 2:
                            print(f"[Engine] Task #{task_db_id}: max retries reached, marking failed")
                    if not retried:
                        AccountDB.refund_points(client.account_id, cost)
                        TaskDB.update_status(task_db_id, "failed",
                                             task_id=remote_task_id, error_message=uri)
                        self._notify(task_db_id, "failed", uri)
                        completed_ids.append(task_db_id)

            except Exception as e:
                print(f"[Engine] Task #{task_db_id}: poll error - {e}")
                # 不立即失败，下一轮继续试

        # 清理已完成的任务
        if completed_ids:
            with self._active_lock:
                for tid in completed_ids:
                    self._active_tasks.pop(tid, None)

    def _finish_task(self, task_db_id: int, client: OiioiiClient,
                     uri: str, remote_task_id: str, cost: int, points_before: int):
        """任务完成：下载 + 更新积分 + 更新状态"""
        print(f"[Engine] Task #{task_db_id}: completed, downloading...")
        ok_dl, local_path = client.download(uri)

        actual_points = client.get_points()
        if actual_points >= 0:
            print(f"[Engine] Task #{task_db_id}: server points={actual_points} (was {points_before})")
            self.pool.update_points_after_use(client.account_id, actual_points, cost)
        else:
            estimated = max(0, points_before - cost)
            print(f"[Engine] Task #{task_db_id}: can't get server points, estimated={estimated}")
            self.pool.update_points_after_use(client.account_id, estimated, cost)

        TaskDB.update_status(
            task_db_id, "completed",
            task_id=remote_task_id,
            result_uri=uri,
            local_path=local_path if ok_dl else ""
        )
        self._notify(task_db_id, "completed", local_path if ok_dl else uri)

    # ─── 看门狗 ───

    def _watchdog_loop(self):
        """监控轮询线程，60秒无心跳则重启"""
        while self._watchdog_running:
            time.sleep(30)
            if not self._poller_running:
                continue
            if self._poller_heartbeat > 0 and time.time() - self._poller_heartbeat > 60:
                print("[Engine] Watchdog: poller heartbeat lost, restarting...")
                self._poller_running = False
                if self._poller_thread and self._poller_thread.is_alive():
                    # 无法强制停止，等它自然退出
                    pass
                self._start_poller()

    # ─── 公共接口 ───

    def get_task(self, task_db_id: int) -> Optional[dict]:
        return TaskDB.get_by_id(task_db_id)

    def get_all_tasks(self, limit: int = 100) -> list:
        return TaskDB.get_all(limit)

    def get_stats(self) -> dict:
        return TaskDB.stats()

    def retry(self, task_db_id: int) -> dict:
        task = TaskDB.get_by_id(task_db_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        if task["status"] not in ("failed", "timeout"):
            return {"success": False, "error": "Can only retry failed tasks"}
        return self.submit(
            task_type=task["task_type"],
            model_name=task["model_name"],
            prompt=task["prompt"],
            ratio=task["ratio"],
            resolution=task["resolution"],
            duration=task["duration"]
        )

    def get_active_count(self) -> int:
        """当前正在轮询的任务数"""
        with self._active_lock:
            return len(self._active_tasks)
