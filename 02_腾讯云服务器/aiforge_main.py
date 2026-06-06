import os
import sys
import re
import subprocess
import threading
import time
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from config import API_HOST, API_PORT, DATA_DIR, OIIOII_API, POOL_AUTO_REPLENISH, POOL_MIN_ACTIVE, POOL_MIN_TOTAL_POINTS, POOL_CHECK_INTERVAL, PAY_URL, PAY_PID, PAY_KEY, PAY_TYPE
from models.db import init_db, cleanup_old_tasks

PUBLIC_URL = ""

app = FastAPI(title="AiForge", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _pool_watcher():
    if not POOL_AUTO_REPLENISH:
        return
    while True:
        time.sleep(POOL_CHECK_INTERVAL)
        try:
            r = requests.get(f"{OIIOII_API}/api/pool/status", timeout=5)
            if r.status_code != 200:
                continue
            data = r.json()
            active = data.get("active_accounts", 0)
            total_pts = data.get("total_points", 0)
            need_register = False
            reasons = []
            if active < POOL_MIN_ACTIVE:
                need_register = True
                reasons.append(f"活跃账号{active}<{POOL_MIN_ACTIVE}")
            if total_pts < POOL_MIN_TOTAL_POINTS:
                need_register = True
                reasons.append(f"总积分{total_pts}<{POOL_MIN_TOTAL_POINTS}")
            if need_register:
                print(f"[PoolWatcher] 触发自动补充: {', '.join(reasons)}")
                try:
                    rr = requests.post(f"{OIIOII_API}/api/pool/register?count=1", timeout=30)
                    if rr.status_code == 200:
                        print(f"[PoolWatcher] 自动注册成功: {rr.json()}")
                    else:
                        print(f"[PoolWatcher] 自动注册失败: {rr.status_code}")
                except Exception as e:
                    print(f"[PoolWatcher] 自动注册异常: {e}")
        except Exception as e:
            pass


def _auto_cleanup():
    while True:
        time.sleep(86400)
        try:
            deleted = cleanup_old_tasks(30)
            if deleted > 0:
                print(f"[AutoCleanup] Cleaned {deleted} old records")
        except Exception as e:
            print(f"[AutoCleanup] Error: {e}")


@app.on_event("startup")
def startup():
    global PUBLIC_URL
    init_db()
    print(f"[AiForge] DB initialized at {DATA_DIR}")
    if PAY_URL and PAY_PID and PAY_KEY:
        init_payment(PAY_URL, PAY_PID, PAY_KEY, PAY_TYPE)
        print(f"[AiForge] Payment initialized: {PAY_TYPE} @ {PAY_URL}")
    else:
        print("[AiForge] Payment not configured (test mode: auto-credit)")
    t = threading.Thread(target=_pool_watcher, daemon=True)
    t.start()
    print(f"[AiForge] Pool watcher started (interval={POOL_CHECK_INTERVAL}s, min_active={POOL_MIN_ACTIVE}, min_points={POOL_MIN_TOTAL_POINTS})")
    tc = threading.Thread(target=_auto_cleanup, daemon=True)
    tc.start()
    print("[AiForge] Auto cleanup started (daily, 30 days retention)")
    tunnel_proc = _start_tunnel()
    if tunnel_proc:
        print(f"[AiForge] Tunnel started, public URL: {PUBLIC_URL}")
    else:
        print("[AiForge] Tunnel not available (cloudflared not found)")


def _start_tunnel():
    global PUBLIC_URL
    tunnel_log_path = os.path.join(DATA_DIR, "tunnel.log")
    cpolar_exe = r"C:\Program Files\cpolar\cpolar.exe"
    if os.path.exists(cpolar_exe):
        try:
            proc = subprocess.Popen(
                [cpolar_exe, "http", str(API_PORT), "-log=stdout"],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+\.cpolar\.(cn|top|io|com)')
            start_time = time.time()
            with open(tunnel_log_path, "a", encoding="utf-8") as log_fh:
                while time.time() - start_time < 30:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    line = line.strip()
                    log_fh.write(line + "\n")
                    log_fh.flush()
                    m = url_pattern.search(line)
                    if m:
                        PUBLIC_URL = m.group(0)
                        print(f"\n=== 公网地址(cpolar): {PUBLIC_URL} ===\n")
                        return proc
            print("[AiForge] cpolar: failed to get URL within 30s")
        except Exception as e:
            print(f"[AiForge] cpolar error: {e}")
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{API_PORT}"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        url_pattern = re.compile(r'https://[a-zA-Z0-9]+(-[a-zA-Z0-9]+)+\.trycloudflare\.com')
        start_time = time.time()
        with open(tunnel_log_path, "a", encoding="utf-8") as log_fh:
            while time.time() - start_time < 30:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                log_fh.write(line + "\n")
                log_fh.flush()
                m = url_pattern.search(line)
                if m:
                    PUBLIC_URL = m.group(0)
                    print(f"\n=== 公网地址(cloudflared): {PUBLIC_URL} ===\n")
                    return proc
        print("[AiForge] cloudflared: failed to get URL within 30s")
        return proc
    except FileNotFoundError:
        print("[AiForge] No tunnel available (cpolar and cloudflared not found)")
        return None
    except Exception as e:
        print(f"[AiForge] Tunnel error: {e}")
        return None


from api.auth import router as auth_router
from api.generate import router as gen_router
from api.user import router as user_router
from api.payment import router as pay_router, init_payment
from api.pool import router as pool_router

app.include_router(auth_router)
app.include_router(gen_router)
app.include_router(user_router)
app.include_router(pay_router)
app.include_router(pool_router)


FRONTEND_DIR = os.environ.get(
    "AIFORGE_FRONTEND_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist"),
)


@app.get("/")
def serve_index():
    idx = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return {"name": "AiForge API", "version": "1.0.0", "docs": "/docs"}


@app.get("/{path:path}")
def serve_static(path: str):
    fpath = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(fpath):
        return FileResponse(fpath)
    idx = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(idx):
        return FileResponse(idx)
    return {"error": "not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
