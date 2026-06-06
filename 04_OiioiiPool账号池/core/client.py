import time
import re
import os
import base64
import requests
from typing import Optional, Tuple
from config import API_BASE, SUPABASE_URL, SUPABASE_ANON_KEY, IMAGE_MODELS, VIDEO_MODELS_DIRECT, OUTPUT_DIR, get_date_output_dir, REFS_DIR, DATA_DIR


class OiioiiClient:
    def __init__(self, email: str, password: str, token: str = "",
                 workspace_id: str = "", account_id: int = 0):
        self.email = email
        self.password = password
        self.token = token
        self.workspace_id = workspace_id
        self.account_id = account_id
        self.token_expiry = 0
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    @property
    def _headers(self):
        h = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        if self.workspace_id:
            h["x-workspace-id"] = self.workspace_id
        return h

    def login(self) -> bool:
        r = self._session.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            json={"email": self.email, "password": self.password,
                  "gotrue_meta_security": {}},
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            timeout=15
        )
        if r.status_code != 200:
            print(f"[Client] Login failed: {r.status_code} {r.text[:200]}")
            return False
        data = r.json()
        self.token = data["access_token"]
        self.token_expiry = data.get("expires_at", time.time() + 86400 * 7)
        return True

    def ensure_token(self) -> bool:
        if self.token and time.time() < self.token_expiry - 3600:
            return True
        return self.login()

    def activate_user(self) -> bool:
        if not self.ensure_token():
            return False
        r = self._session.post(
            f"{API_BASE}/points/active_user",
            json={"data": {}}, headers=self._headers, timeout=15
        )
        return r.status_code == 200

    def get_points(self) -> int:
        if not self.ensure_token():
            return -1
        r = self._session.post(
            f"{API_BASE}/points/current_user_points",
            json={"data": {}}, headers=self._headers, timeout=15
        )
        if r.status_code != 200:
            return -1
        return r.json().get("data", {}).get("available_limited", 0)

    def daily_claim(self) -> dict:
        if not self.ensure_token():
            return {"success": False, "error": "No token"}
        r = self._session.post(
            f"{API_BASE}/points/add",
            json={"data": {"type": "sign_in"}}, headers=self._headers, timeout=15
        )
        if r.status_code != 200:
            return {"success": False, "error": f"HTTP {r.status_code}"}
        resp = r.json()
        code = resp.get("code", "")
        if code == "SUCCESS":
            data = resp.get("data", {})
            added = data.get("added", 0)
            total = data.get("available_limited", 0)
            print(f"[Client] daily_claim: +{added} points, total={total}")
            return {"success": True, "added": added, "total": total}
        elif code == "DUPLICATE_BUCKET":
            return {"success": True, "added": 0, "duplicate": True}
        else:
            return {"success": False, "error": resp.get("error", code)}

    def ensure_workspace(self) -> bool:
        if self.workspace_id:
            return True
        if not self.ensure_token():
            return False
        r = self._session.post(
            f"{API_BASE}/workspace/workspace_list",
            json={"data": {"limit": 10}}, headers=self._headers, timeout=15
        )
        if r.status_code == 200:
            workspaces = r.json().get("data", {}).get("workspaces", [])
            if workspaces:
                ws_with_assets = [w for w in workspaces if "assetList" in w.get("workspaceDocument", {})]
                if ws_with_assets:
                    self.workspace_id = ws_with_assets[0].get("workspaceId", "")
                else:
                    self.workspace_id = workspaces[0].get("workspaceId", "")
                if self.workspace_id:
                    return True
        r = self._session.post(
            f"{API_BASE}/workspace/create_workspace",
            json={"data": {"name": "pool"}}, headers=self._headers, timeout=15
        )
        if r.status_code == 200:
            self.workspace_id = r.json().get("data", {}).get("workspaceId", "")
            return bool(self.workspace_id)
        return False

    def _get_asset_list(self) -> tuple:
        r = self._session.post(
            f"{API_BASE}/workspace/workspace_list",
            json={"data": {"limit": 10}}, headers=self._headers, timeout=15
        )
        if r.status_code != 200:
            print(f"[Client] _get_asset_list failed: {r.status_code}")
            return [], False
        workspaces = r.json().get("data", {}).get("workspaces", [])
        if not workspaces:
            return [], False
        current_ws = next((w for w in workspaces if w.get("workspaceId") == self.workspace_id), None)
        if current_ws:
            assets = current_ws.get("workspaceDocument", {}).get("assetList")
            if assets is not None:
                return assets, True
        ws_with_assets = [w for w in workspaces if "assetList" in w.get("workspaceDocument", {})]
        if ws_with_assets:
            new_id = ws_with_assets[0].get("workspaceId", "")
            if new_id != self.workspace_id:
                print(f"[Client] _get_asset_list: switching to workspace {new_id[:20]} (has assetList)")
                self.workspace_id = new_id
                if self.account_id:
                    from core.db import AccountDB
                    AccountDB.update_workspace(self.account_id, new_id)
            return ws_with_assets[0].get("workspaceDocument", {}).get("assetList", []), True
        return [], False

    def generate_image(self, prompt: str, model_name: str = "GPT-Image2",
                       ratio: str = "16:9", resolution: str = "2K",
                       reference_images: list = None) -> Tuple[bool, str, list]:
        if not self.ensure_token() or not self.ensure_workspace():
            return False, "Login or workspace failed", []
        model_info = IMAGE_MODELS.get(model_name)
        if not model_info:
            return False, f"Unknown model: {model_name}", []
        uploaded_refs = self._refs_to_data_urls(reference_images or [], model_name)
        method = model_info["method"]

        # 不同模型接受的toolArgs不同
        if method in ("generate_image_gpt_image2",):
            tool_args = {"aspectRatio": ratio, "resolution": resolution}
        elif method == "generate_image_nano":
            # Nano模型不接受aspectRatio，只接受resolution
            tool_args = {"resolution": resolution}
        elif method == "generate_image_midjourney":
            # MJ/Niji模型不接受aspectRatio和resolution
            tool_args = {}
        elif method == "generate_image_flux":
            # Flux不接受resolution，只接受aspectRatio
            tool_args = {"aspectRatio": ratio}
        elif method in ("generate_image_seedream50", "generate_image_seedream45"):
            # Seedream不接受resolution值"1K"等，只接受aspectRatio
            tool_args = {"aspectRatio": ratio}
        elif method == "generate_image_novelai":
            # NovelAI不接受aspectRatio和resolution
            tool_args = {}
        elif method == "generate_image_gpt4o":
            # GPT-4o不接受aspectRatio和resolution
            tool_args = {}
        else:
            # 其他模型默认传ratio和resolution，失败再调整
            tool_args = {"aspectRatio": ratio, "resolution": resolution}

        body = {
            "workspaceId": self.workspace_id,
            "tasks": [{"prompt": prompt, "images": uploaded_refs, "audios": []}],
            "models": [{
                "mcpMethodName": method,
                "version": model_info.get("version") or "gpt_image2",
                "label": model_name
            }],
            "toolArgs": tool_args
        }
        print(f"[Client] generate_image: model={model_name} ratio={ratio} refs={len(reference_images or [])}")
        r = self._session.post(f"{API_BASE}/media/batch_gen/submit", json=body, headers=self._headers, timeout=30)
        resp = r.json()
        print(f"[Client] generate_image response: success={resp.get('success')} error={resp.get('error','')}")
        if resp.get("success"):
            batch_id = resp.get("batchId", resp.get("taskId", ""))
            return True, batch_id, uploaded_refs
        if resp.get("error") == "INSUFFICIENT_POINTS":
            return False, "INSUFFICIENT_POINTS", uploaded_refs
        return False, resp.get("error", f"HTTP {r.status_code}"), uploaded_refs

    def generate_video(self, prompt: str, model_name: str = "Vidu Q2",
                       ratio: str = "16:9", duration: int = 5,
                       resolution: str = "720p",
                       reference_images: list = None,
                       reference_video: str = "") -> Tuple[bool, str]:
        if not self.ensure_token() or not self.ensure_workspace():
            return False, "Login or workspace failed"
        model_info = VIDEO_MODELS_DIRECT.get(model_name)
        if not model_info:
            return False, f"Unknown or agent-only model: {model_name}"

        body = {
            "workspaceId": self.workspace_id,
            "prompt": prompt,
            "mcpMethodName": model_info["method"],
            "ratio": ratio,
            "aspectRatio": ratio,
            "duration": duration,
            "resolution": resolution
        }
        if model_info.get("version"):
            body["model"] = model_info["version"]
            body["version"] = model_info["version"]
        if reference_images:
            refs = self._refs_to_data_urls(reference_images, model_name)
            if refs:
                body["images"] = refs
        if reference_video and model_info.get("video_ref"):
            video_uri = self._resolve_video_ref(reference_video)
            if video_uri:
                body["videoUrl"] = video_uri
            else:
                print(f"[Client] WARNING: could not resolve video ref: {reference_video[:60]}")
        print(f"[Client] generate_video: model={model_name} duration={duration}s ratio={ratio} refs={len(reference_images or [])} videoRef={bool(reference_video)}")
        r = self._session.post(f"{API_BASE}/media/video_generate/submit", json=body, headers=self._headers, timeout=30)
        resp = r.json()
        ok = resp.get("success", False)
        err = resp.get("error", "")
        tid = resp.get("taskId", "")
        manual_refresh = resp.get("manualRefreshRequired", False)
        print(f"[Client] generate_video response: success={ok} taskId={tid[:40]} error={err[:60]} manualRefresh={manual_refresh}")
        if ok:
            return True, tid, manual_refresh
        if err == "INSUFFICIENT_POINTS":
            return False, "INSUFFICIENT_POINTS", False
        return False, err or f"HTTP {r.status_code}", False

    def _refs_to_data_urls(self, refs: list, model_name: str = "") -> list:
        result = []
        for url in refs:
            data = None
            fname = os.path.basename(url.split("?")[0])
            local_path = os.path.join(REFS_DIR, fname)
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    data = f.read()
            else:
                for rf in os.listdir(REFS_DIR):
                    if fname in rf or rf in url:
                        local_path = os.path.join(REFS_DIR, rf)
                        with open(local_path, "rb") as f:
                            data = f.read()
                        break
            if data is None:
                try:
                    r = requests.get(url, timeout=10)
                    if r.status_code == 200:
                        data = r.content
                except Exception:
                    pass
            if data:
                hogi_uri = self._upload_to_oiioii(data, fname)
                if hogi_uri:
                    result.append(hogi_uri)
                else:
                    ext = os.path.splitext(fname)[1].lower()
                    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                            "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp"}.get(ext.lstrip("."), "image/png")
                    b64 = base64.b64encode(data).decode("ascii")
                    result.append(f"data:{mime};base64,{b64}")
            else:
                result.append(url)
        return result

    def _resolve_video_ref(self, ref: str) -> str:
        if ref.startswith("hogi://"):
            return ref
        if ref.startswith("http://") or ref.startswith("https://"):
            return ref
        fname = os.path.basename(ref.split("?")[0])
        local_path = os.path.join(REFS_DIR, fname)
        data = None
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                data = f.read()
        else:
            for rf in os.listdir(REFS_DIR):
                if fname in rf or rf in ref:
                    local_path = os.path.join(REFS_DIR, rf)
                    with open(local_path, "rb") as f:
                        data = f.read()
                    break
        if data is None:
            try:
                r = requests.get(ref, timeout=30)
                if r.status_code == 200:
                    data = r.content
            except Exception:
                pass
        if data:
            hogi_uri = self.upload_video_file(data, fname)
            if hogi_uri:
                print(f"[Client] _resolve_video_ref: uploaded {fname} -> {hogi_uri[:50]}")
                return hogi_uri
        print(f"[Client] _resolve_video_ref: failed for {ref[:60]}")
        return ""

    def _upload_to_oiioii(self, file_data: bytes, filename: str) -> str:
        if not self.ensure_token():
            return ""
        ext = os.path.splitext(filename)[1].lower()
        file_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                     "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp"}.get(ext.lstrip("."), "image/png")
        b64 = base64.b64encode(file_data).decode("ascii")
        body = {"fileBlob": b64, "fileType": file_type}
        try:
            r = self._session.post(f"{API_BASE}/res/upload_file", json=body, headers=self._headers, timeout=30)
            if r.status_code == 200:
                resp = r.json()
                if resp.get("code") == "SUCCESS":
                    uri = resp.get("data", {}).get("uri", "")
                    if uri:
                        print(f"[Client] _upload_to_oiioii: uploaded {filename} -> {uri[:50]}")
                        return uri
            print(f"[Client] _upload_to_oiioii: failed for {filename}: {r.status_code} {r.text[:100]}")
        except Exception as e:
            print(f"[Client] _upload_to_oiioii: error: {e}")
        return ""

    def upload_video_file(self, file_data: bytes, filename: str) -> str:
        if not self.ensure_token():
            return ""
        ext = os.path.splitext(filename)[1].lower()
        file_type = {"mp4": "video/mp4", "mov": "video/quicktime", "avi": "video/x-msvideo",
                     "webm": "video/webm", "mkv": "video/x-matroska"}.get(ext.lstrip("."), "video/mp4")
        b64 = base64.b64encode(file_data).decode("ascii")
        body = {"fileBlob": b64, "fileType": file_type}
        try:
            r = self._session.post(f"{API_BASE}/res/upload_file", json=body, headers=self._headers, timeout=60)
            if r.status_code == 200:
                resp = r.json()
                if resp.get("code") == "SUCCESS":
                    uri = resp.get("data", {}).get("uri", "")
                    if uri:
                        print(f"[Client] upload_video_file: uploaded {filename} -> {uri[:50]}")
                        return uri
            print(f"[Client] upload_video_file: failed for {filename}: {r.status_code} {r.text[:100]}")
        except Exception as e:
            print(f"[Client] upload_video_file: error: {e}")
        return ""

    def poll_batch_video(self, task_id: str, max_wait: int = 300, interval: int = 10) -> Tuple[str, str]:
        if not self.ensure_token():
            return "failed", "No token"
        print(f"[Client] poll_batch_video: task_id={task_id} max_wait={max_wait}")
        start = time.time()
        poll_count = 0
        while time.time() - start < max_wait:
            time.sleep(interval)
            poll_count += 1
            elapsed = int(time.time() - start)
            try:
                url = f"{API_BASE}/media/canvas_async_tasks/sync?task_id={task_id}"
                r = self._session.get(url, headers=self._headers, timeout=15)
                if r.status_code == 200:
                    tasks = r.json().get("data", {}).get("tasks", r.json().get("tasks", []))
                    for t in tasks:
                        tid = t.get("task_id", "")
                        status = t.get("status", "")
                        if tid == task_id or (task_id in tid):
                            if status == "completed":
                                result = t.get("result_payload", {})
                                uri = result.get("uri", result.get("videoUri", ""))
                                if not uri:
                                    uri = t.get("output_uri", "")
                                if uri:
                                    print(f"[Client] poll_batch_video COMPLETED: uri={uri[:60]}")
                                    return "completed", uri
                                print(f"[Client] poll_batch_video: completed but no uri in result")
                                return "failed", "No result uri"
                            elif status == "failed":
                                err_code = t.get("error_code", "")
                                err_msg = t.get("error_message", "")
                                result_err = t.get("result_payload", {}).get("error", "")
                                err = err_msg or err_code or result_err or "Unknown"
                                print(f"[Client] poll_batch_video FAILED: {err}")
                                return "failed", err
                if not tasks:
                    if poll_count <= 3 or poll_count % 5 == 0:
                        print(f"[Client] poll_batch_video #{poll_count} [{elapsed}s]: no tasks returned")
                elif poll_count <= 3 or poll_count % 5 == 0:
                    matched = [t for t in tasks if task_id in t.get("task_id", "")]
                    print(f"[Client] poll_batch_video #{poll_count} [{elapsed}s]: tasks={len(tasks)} matched={len(matched)}")
            except Exception as e:
                print(f"[Client] poll_batch_video error: {e}")

        print(f"[Client] poll_batch_video TIMEOUT after {poll_count} polls ({max_wait}s)")
        return "timeout", "Polling timed out"

    def check_batch_video_once(self, task_id: str) -> Tuple[str, str]:
        """非阻塞：单次查询 batch_video 状态"""
        if not self.ensure_token():
            return "failed", "No token"
        try:
            url = f"{API_BASE}/media/canvas_async_tasks/sync?task_id={task_id}"
            r = self._session.get(url, headers=self._headers, timeout=15)
            if r.status_code == 200:
                tasks = r.json().get("data", {}).get("tasks", r.json().get("tasks", []))
                for t in tasks:
                    tid = t.get("task_id", "")
                    status = t.get("status", "")
                    if tid == task_id or (task_id in tid):
                        if status == "completed":
                            result = t.get("result_payload", {})
                            uri = result.get("uri", result.get("videoUri", ""))
                            if not uri:
                                uri = t.get("output_uri", "")
                            if uri:
                                return "completed", uri
                            return "failed", "No result uri"
                        elif status == "failed":
                            err_code = t.get("error_code", "")
                            err_msg = t.get("error_message", "")
                            result_err = t.get("result_payload", {}).get("error", "")
                            err = err_msg or err_code or result_err or "Unknown"
                            return "failed", err
                return "pending", ""
            return "pending", ""
        except Exception as e:
            return "pending", str(e)

    def check_result_once(self, task_type: str, skip_uris: set,
                          remote_task_id: str = "") -> Tuple[str, str]:
        """非阻塞：单次查询任务结果。优先用 remote_task_id 精确查询，资产列表做 fallback。"""
        if not self.ensure_token():
            return "failed", "No token"
        try:
            # 优先：用 remote_task_id 精确查询 async_tasks
            if remote_task_id:
                url = f"{API_BASE}/media/canvas_async_tasks/sync?task_id={remote_task_id}"
                r = self._session.get(url, headers=self._headers, timeout=15)
                if r.status_code == 200:
                    tasks = r.json().get("data", {}).get("tasks", r.json().get("tasks", []))
                    for t in tasks:
                        tid = t.get("task_id", "")
                        status = t.get("status", "")
                        if remote_task_id in tid or tid in remote_task_id:
                            if status == "completed":
                                uri = t.get("result_payload", {}).get("uri", t.get("result_payload", {}).get("videoUri", ""))
                                if not uri:
                                    uri = t.get("output_uri", "")
                                if uri:
                                    return "completed", uri
                            elif status == "failed":
                                err_code = t.get("error_code", "")
                                err_msg = t.get("error_message", "")
                                result_err = t.get("result_payload", {}).get("error", "")
                                err = err_msg or err_code or result_err or "Unknown"
                                return "failed", err
                            # status is pending/processing, don't return yet
                            return "pending", ""

            # Fallback：查资产列表（仅在无 remote_task_id 时使用）
            asset_list, has_asset_list = self._get_asset_list()
            if asset_list:
                for asset in reversed(asset_list):
                    uri = asset.get("uri", "")
                    if not uri or uri in skip_uris:
                        continue
                    if asset.get("type") == task_type:
                        return "completed", uri
            return "pending", ""
        except Exception as e:
            return "pending", str(e)

    def get_known_uris(self) -> set:
        assets, _ = self._get_asset_list()
        return {a.get("uri", "") for a in assets if a.get("uri")}

    def poll_result(self, task_type: str, skip_uris: set,
                    max_wait: int = 300, interval: int = 10,
                    remote_task_id: str = "",
                    initial_delay: int = 0) -> Tuple[str, str]:
        if not self.ensure_token():
            return "failed", "No token"
        print(f"[Client] poll_result: type={task_type} skip_refs={len(skip_uris)} max_wait={max_wait} remote_id={remote_task_id[:30] if remote_task_id else 'none'}")
        if initial_delay > 0:
            print(f"[Client] poll_result: waiting {initial_delay}s before first poll (manualRefresh task)...")
            time.sleep(initial_delay)
        start = time.time()
        poll_count = 0
        seen_uris = set(skip_uris)
        while time.time() - start < max_wait:
            time.sleep(interval)
            self.ensure_token()
            poll_count += 1
            elapsed = int(time.time() - start)

            # 优先：用 remote_task_id 精确查询 async_tasks
            if remote_task_id:
                try:
                    url = f"{API_BASE}/media/canvas_async_tasks/sync?task_id={remote_task_id}"
                    r = self._session.get(url, headers=self._headers, timeout=15)
                    if r.status_code == 200:
                        tasks = r.json().get("data", {}).get("tasks", r.json().get("tasks", []))
                        for t in tasks:
                            tid = t.get("task_id", "")
                            status = t.get("status", "")
                            if remote_task_id in tid or tid in remote_task_id:
                                if status == "completed":
                                    uri = t.get("result_payload", {}).get("uri", t.get("result_payload", {}).get("videoUri", ""))
                                    if not uri:
                                        uri = t.get("output_uri", "")
                                    if uri:
                                        print(f"[Client] poll FOUND via async_tasks: uri={uri[:60]}")
                                        return "completed", uri
                                elif status == "failed":
                                    err_code = t.get("error_code", "")
                                    err_msg = t.get("error_message", "")
                                    result_err = t.get("result_payload", {}).get("error", "")
                                    err = err_msg or err_code or result_err or "Unknown"
                                    print(f"[Client] poll FAILED via async_tasks: {err}")
                                    return "failed", err
                                # pending/processing, 继续等
                except Exception as e:
                    print(f"[Client] poll: async_tasks error: {e}")

            # Fallback：查资产列表（无 remote_task_id 或 async_tasks 未返回结果时）
            if poll_count <= 3 or poll_count % 5 == 0:
                print(f"[Client] poll #{poll_count} [{elapsed}s]: async_tasks no result, checking asset list")

            asset_list, has_asset_list = self._get_asset_list()
            if asset_list:
                for asset in reversed(asset_list):
                    uri = asset.get("uri", "")
                    if not uri or uri in seen_uris:
                        continue
                    seen_uris.add(uri)
                    if asset.get("type") == task_type:
                        print(f"[Client] poll FOUND via asset list: type={task_type} uri={uri[:60]}")
                        return "completed", uri

        print(f"[Client] poll TIMEOUT after {poll_count} polls ({max_wait}s)")
        return "timeout", "Polling timed out"

    def download(self, uri: str, filename: str = "") -> Tuple[bool, str]:
        import os
        if not uri:
            return False, "Empty URI"
        if uri.startswith("hogi://"):
            if not self.ensure_token():
                return False, "No token"
            dl_url = f"{API_BASE}/res/read_file"
            dl_params = {"uri": uri}
            dl_headers = {"Authorization": f"Bearer {self.token}"}
        elif uri.startswith("http://") or uri.startswith("https://"):
            dl_url = uri
            dl_params = {}
            dl_headers = {}
        elif uri.startswith("res/"):
            if not self.ensure_token():
                return False, "No token"
            dl_url = f"{API_BASE}/res/read_file"
            dl_params = {"uri": uri}
            dl_headers = {"Authorization": f"Bearer {self.token}"}
        else:
            return False, f"Unsupported URI: {uri[:40]}"

        print(f"[Client] download: {uri[:60]}")
        try:
            r = requests.get(dl_url, params=dl_params, headers=dl_headers, timeout=120)
            if r.status_code == 200 and len(r.content) > 100:
                if not filename:
                    ext = ".mp4" if "video" in uri else ".png"
                    filename = f"{int(time.time())}_{hash(uri) % 10000}{ext}"
                filepath = os.path.join(get_date_output_dir(), filename)
                with open(filepath, "wb") as f:
                    f.write(r.content)
                print(f"[Client] download OK: {filepath} ({len(r.content)} bytes)")
                return True, filepath
            return False, f"Download failed: HTTP {r.status_code} size={len(r.content)}"
        except Exception as e:
            return False, f"Download error: {e}"

    def health_check(self) -> dict:
        result = {"alive": False, "points": -1, "workspace": False}
        if not self.ensure_token():
            result["error"] = "Login failed"
            return result
        result["alive"] = True
        result["points"] = self.get_points()
        result["workspace"] = bool(self.workspace_id) or self.ensure_workspace()
        return result
