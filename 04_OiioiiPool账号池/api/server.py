import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
from core.db import init_db, TaskDB, AccountDB
from core.pool import AccountPool
from core.engine import GenEngine
from config import (IMAGE_MODELS, VIDEO_MODELS_DIRECT, VIDEO_MODELS_AGENT_ONLY,
                    API_PORT, API_HOST, BASE_DIR, OUTPUT_DIR, REFS_DIR, LOGS_DIR,
                    VIDEO_MIN_POINTS)
from api.api_db import init_api_tables
from api.api_routes import router as api_router, set_engine as set_api_engine

app = FastAPI(title="夏夜专属API", version="3.0.0")
app.include_router(api_router)

# 静态文件
from fastapi.staticfiles import StaticFiles
import os as _os
_static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "static")
if _os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

pool: Optional[AccountPool] = None
engine: Optional[GenEngine] = None
_reg_jobs: dict = {}
_continuous_reg_running = False
_continuous_reg_thread = None
_public_url = ""


def set_public_url(url: str):
    global _public_url
    _public_url = url
    print(f"[Server] Public URL set to: {url}")


def init():
    global pool, engine
    init_db()
    init_api_tables()
    pool = AccountPool()
    engine = GenEngine(pool)
    engine.cleanup_stale_tasks()
    set_api_engine(engine)


class ImageRequest(BaseModel):
    prompt: str
    model: str = "GPT-Image2"
    ratio: str = "16:9"
    resolution: str = "2K"
    reference_images: list = []


class VideoRequest(BaseModel):
    prompt: str
    model: str = "Vidu Q2"
    ratio: str = "16:9"
    resolution: str = "720p"
    duration: int = 5
    reference_images: list = []
    reference_video: str = ""


class AddAccountRequest(BaseModel):
    email: str
    password: str


@app.on_event("startup")
def startup():
    init()


@app.get("/")
def index():
    html_path = os.path.join(BASE_DIR, "frontend", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>Frontend not found</h1>")


@app.get("/output/{file_path:path}")
def serve_output(file_path: str):
    full_path = os.path.join(OUTPUT_DIR, file_path)
    if os.path.exists(full_path):
        return FileResponse(full_path)
    if os.path.isdir(OUTPUT_DIR):
        for entry in sorted(os.listdir(OUTPUT_DIR), reverse=True):
            sub = os.path.join(OUTPUT_DIR, entry, file_path)
            if os.path.exists(sub):
                return FileResponse(sub)
    raise HTTPException(404, "File not found")


@app.post("/api/upload_ref")
async def upload_reference(file: UploadFile = File(...)):
    os.makedirs(REFS_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "img.png")[1] or ".png"
    fname = f"ref_{int(time.time())}_{hash(file.filename) % 10000}{ext}"
    fpath = os.path.join(REFS_DIR, fname)
    content = await file.read()
    with open(fpath, "wb") as f:
        f.write(content)
    if _public_url:
        url = f"{_public_url}/output/refs/{fname}"
    else:
        url = f"/output/refs/{fname}"
    return {"url": url, "filename": fname}


@app.post("/api/upload_video_ref")
async def upload_video_reference(file: UploadFile = File(...)):
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(400, "Video file too large (max 100MB)")
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    fname = f"vidref_{int(time.time())}_{hash(file.filename) % 10000}{ext}"
    fpath = os.path.join(REFS_DIR, fname)
    os.makedirs(REFS_DIR, exist_ok=True)
    with open(fpath, "wb") as f:
        f.write(content)
    if _public_url:
        url = f"{_public_url}/output/refs/{fname}"
    else:
        url = f"/output/refs/{fname}"
    print(f"[Upload] video ref saved: {fpath} ({len(content)} bytes) -> {url}")
    return {"uri": url, "filename": fname}


@app.post("/api/generate_image")
def generate_image(req: ImageRequest):
    if req.model not in IMAGE_MODELS:
        raise HTTPException(400, f"Unknown model. Available: {list(IMAGE_MODELS.keys())}")
    result = engine.submit("image", req.model, req.prompt, req.ratio, req.resolution,
                           reference_images=req.reference_images)
    if not result["success"]:
        raise HTTPException(500, result["error"])
    return {"task_id": result["task_db_id"], "status": "submitted"}


@app.post("/api/generate_video")
def generate_video(req: VideoRequest):
    if req.model not in VIDEO_MODELS_DIRECT:
        raise HTTPException(400, f"Model not available. Available: {list(VIDEO_MODELS_DIRECT.keys())}")
    result = engine.submit(
        "video", req.model, req.prompt, req.ratio, req.resolution, req.duration,
        reference_images=req.reference_images,
        reference_video=req.reference_video)
    if not result["success"]:
        raise HTTPException(500, result["error"])
    return {"task_id": result["task_db_id"], "status": "submitted"}


@app.get("/api/task/{task_id}")
def get_task(task_id: int):
    task = TaskDB.get_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return {
        "task_id": task["id"],
        "type": task["task_type"],
        "model": task["model_name"],
        "prompt": task["prompt"],
        "status": task["status"],
        "result_uri": task["result_uri"],
        "local_path": task["local_path"],
        "points_cost": task["points_cost"],
        "error": task["error_message"],
        "created_at": task["created_at"],
        "completed_at": task["completed_at"],
    }


@app.get("/api/task/{task_id}/download")
def download_task(task_id: int):
    task = TaskDB.get_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task["status"] != "completed":
        raise HTTPException(400, f"Task status is {task['status']}, not completed")
    if task["local_path"] and os.path.exists(task["local_path"]):
        return FileResponse(task["local_path"], filename=os.path.basename(task["local_path"]))
    if task["result_uri"] and task["result_uri"].startswith("hogi://"):
        from core.pool import AccountPool
        _pool = AccountPool()
        client = _pool.get_available_client(min_points=0)
        if client:
            ok, local_path = client.download(task["result_uri"])
            if ok and local_path:
                TaskDB.update_status(task_id, "completed", result_uri=task["result_uri"], local_path=local_path)
                return FileResponse(local_path, filename=os.path.basename(local_path))
    raise HTTPException(404, "File not found on disk")


@app.post("/api/task/{task_id}/retry")
def retry_task(task_id: int):
    result = engine.retry(task_id)
    if not result["success"]:
        raise HTTPException(500, result["error"])
    return {"task_id": result["task_db_id"], "status": "submitted"}


@app.get("/api/pool/status")
def pool_status():
    accounts = AccountDB.get_all()
    return {
        "total_accounts": len(accounts),
        "active_accounts": AccountDB.active_count(),
        "total_points": AccountDB.total_points(),
        "continuous_reg_running": _continuous_reg_running,
        "accounts": [
            {
                "id": a["id"],
                "email": a["email"],
                "points": a["points_remaining"],
                "status": a["status"],
            }
            for a in accounts
        ],
    }


@app.get("/api/models")
def list_models():
    video_all = {}
    for k, v in VIDEO_MODELS_DIRECT.items():
        video_all[k] = {"method": v["method"], "cost_base": v["cost_base"],
                        "cost_duration_scale": v.get("cost_duration_scale", {}),
                        "default_duration": v["default_duration"],
                        "durations": v["durations"],
                        "ratios": v["ratios"],
                        "resolutions": v.get("resolutions", ["720p", "1080p"]),
                        "ref_max": v["ref_max"],
                        "video_ref": v.get("video_ref", False)}
    for k, v in VIDEO_MODELS_AGENT_ONLY.items():
        video_all[k] = {"method": v["method"], "cost_base": v["cost_base"],
                        "agent_only": True}
    return {
        "image": {k: {"method": v["method"], "cost_base": v["cost_base"],
                      "ratios": v.get("ratios", ["1:1", "16:9", "9:16"]),
                      "resolutions": v.get("resolutions", ["1K", "2K"]),
                      "ref_max": v.get("ref_max", 0)}
                  for k, v in IMAGE_MODELS.items()},
        "video": video_all,
        "video_min_points": VIDEO_MIN_POINTS,
    }


@app.get("/api/tasks")
def list_tasks(limit: int = 50):
    tasks = TaskDB.get_all(limit)
    return {
        "tasks": [
            {
                "id": t["id"],
                "type": t["task_type"],
                "model": t["model_name"],
                "prompt": t["prompt"],
                "status": t["status"],
                "ratio": t["ratio"],
                "resolution": t["resolution"],
                "duration": t["duration"],
                "points_cost": t["points_cost"],
                "result_uri": t["result_uri"],
                "local_path": t["local_path"],
                "error": t["error_message"],
                "account_email": t.get("account_email", ""),
                "created_at": t["created_at"],
                "completed_at": t["completed_at"],
            }
            for t in tasks
        ]
    }


@app.post("/api/pool/add")
def add_account(req: AddAccountRequest):
    result = pool.add_account(req.email, req.password)
    if not result["success"]:
        raise HTTPException(500, result["error"])
    return {"success": True, "account_id": result["account_id"], "points": result["points"]}


class BulkImportAccounts(BaseModel):
    accounts: list  # [{"email": "...", "password": "..."}]


@app.post("/api/pool/bulk_add")
def bulk_add_accounts(req: BulkImportAccounts):
    """批量导入账号（从本地注册结果文件直接导入）"""
    results = []
    ok = 0
    fail = 0
    for acc in req.accounts:
        try:
            result = pool.add_account(acc.get("email", ""), acc.get("password", ""))
            if result["success"]:
                ok += 1
                results.append({"email": acc.get("email"), "success": True, "account_id": result["account_id"], "points": result["points"]})
            else:
                fail += 1
                results.append({"email": acc.get("email"), "success": False, "error": result.get("error", "")})
        except Exception as e:
            fail += 1
            results.append({"email": acc.get("email"), "success": False, "error": str(e)})
        if len(req.accounts) > 1:
            import time as _t
            _t.sleep(0.5)  # 避免触发限流
    return {"success": ok, "failed": fail, "total": len(req.accounts), "details": results}


@app.post("/api/pool/register")
def register_account(count: int = 1, concurrent: int = 1):
    job_id = str(int(time.time() * 1000))
    workers = max(1, min(concurrent, 10))  # 最多10个并发
    _reg_jobs[job_id] = {"status": "running", "result": None, "progress": [0, count], "details": []}

    def _do_one(idx):
        try:
            result = pool.auto_register()
            return {"index": idx, "success": result["success"], "email": result.get("email", ""), "points": result.get("points", 0), "error": result.get("error", "")}
        except Exception as e:
            return {"index": idx, "success": False, "email": "", "points": 0, "error": str(e)}

    def _do():
        ok_count = 0
        fail_count = 0
        details = []
        if workers <= 1 or count <= 1:
            # 串行模式
            for i in range(count):
                r = _do_one(i)
                details.append(r)
                if r["success"]:
                    ok_count += 1
                else:
                    fail_count += 1
                _reg_jobs[job_id]["progress"] = [i + 1, count]
                if i < count - 1:
                    time.sleep(2)
        else:
            # 并发模式
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(_do_one, i): i for i in range(count)}
                done_count = 0
                for future in as_completed(futures):
                    r = future.result()
                    details.append(r)
                    if r["success"]:
                        ok_count += 1
                    else:
                        fail_count += 1
                    done_count += 1
                    _reg_jobs[job_id]["progress"] = [done_count, count]
        # 按index排序
        details.sort(key=lambda x: x["index"])
        _reg_jobs[job_id] = {
            "status": "done",
            "result": {"success": True, "registered": ok_count, "failed": fail_count},
            "progress": [count, count],
            "details": details
        }

    threading.Thread(target=_do, daemon=True).start()
    return {"job_id": job_id, "status": "running", "count": count, "concurrent": workers}


@app.get("/api/pool/register/{job_id}")
def register_status(job_id: str):
    job = _reg_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] == "running":
        return {"status": "running", "progress": job.get("progress", [0, 0])}
    result = job["result"]
    details = job.get("details", [])
    if result and result.get("success"):
        return {"status": "done", "registered": result.get("registered", 0), "failed": result.get("failed", 0), "details": details}
    return {"status": "failed", "error": (result or {}).get("error", "Unknown"), "details": details}


@app.post("/api/pool/continuous_reg")
def toggle_continuous_reg(enable: bool = True, target_count: int = 10):
    global _continuous_reg_running, _continuous_reg_thread

    if not enable:
        _continuous_reg_running = False
        return {"status": "stopped"}

    if _continuous_reg_running:
        return {"status": "already_running"}

    _continuous_reg_running = True

    def _continuous_loop():
        global _continuous_reg_running
        registered = 0
        while _continuous_reg_running and registered < target_count:
            try:
                result = pool.auto_register()
                if result["success"]:
                    registered += 1
                    print(f"[ContinuousReg] #{registered}/{target_count} ok")
                else:
                    print(f"[ContinuousReg] failed: {result.get('error', 'unknown')}")
            except Exception as e:
                print(f"[ContinuousReg] error: {e}")
            if _continuous_reg_running and registered < target_count:
                time.sleep(3)
        _continuous_reg_running = False
        print(f"[ContinuousReg] finished: {registered}/{target_count}")

    _continuous_reg_thread = threading.Thread(target=_continuous_loop, daemon=True)
    _continuous_reg_thread.start()
    return {"status": "running", "target": target_count}


@app.get("/api/pool/continuous_reg/status")
def continuous_reg_status():
    return {"running": _continuous_reg_running}


@app.post("/api/pool/refresh")
def refresh_all():
    results = pool.refresh_all()
    ok = sum(1 for r in results if r.get("alive"))
    return {"success": True, "alive": ok, "total": len(results)}


@app.delete("/api/pool/{account_id}")
def remove_account(account_id: int):
    pool.remove_account(account_id)
    return {"success": True}


@app.get("/api/file/{task_id}")
def serve_task_file(task_id: int):
    """下载生成结果文件（API 客户用）"""
    task = TaskDB.get_by_id(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    local_path = task.get("local_path", "")
    if not local_path or not os.path.exists(local_path):
        result_uri = task.get("result_uri", "")
        if result_uri:
            return {"url": result_uri}
        raise HTTPException(404, "File not found")
    return FileResponse(local_path)


def run_api():
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    run_api()
