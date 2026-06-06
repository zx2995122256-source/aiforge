"""
每日签到领积分脚本 —— 为所有 Oiioii 账号领取每日 60 积分

原理：
    1. 从服务器获取账号列表（email, password）
    2. 逐个登录 Supabase → 调用 points/add (type=sign_in)
    3. 已领过的自动跳过（DUPLICATE_BUCKET）
    4. 纯 API 调用，不需要浏览器

使用方法：
    # 从服务器账号池领积分
    python daily_claim_all.py

    # 从本地结果文件领积分（注册脚本输出的 json）
    python daily_claim_all.py --accounts-file register_result_*.json

    # 指定并发数
    python daily_claim_all.py --concurrent 5

环境变量：
    AIFORGE_SERVER - 服务器地址 (默认 http://122.51.205.94)
"""
import os
import sys
import time
import json
import random
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests as http_req

SERVER_URL = os.environ.get("AIFORGE_SERVER", "http://122.51.205.94")

MAIL_TM_API = "https://api.mail.tm"
SUPABASE_URL = "https://spb.oiioii.ai"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLC"
    "JpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0."
    "Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
)
API_BASE = "https://api.oiioii.ai"


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def get_accounts_from_server():
    """从服务器账号池获取账号列表（需要服务器支持返回密码）"""
    try:
        r = http_req.get(f"{SERVER_URL}/api/pool/status", timeout=15)
        if r.status_code == 200:
            data = r.json()
            accounts = data.get("accounts", [])
            log(f"从服务器获取到 {len(accounts)} 个账号")
            return [a for a in accounts if a.get("status") == "active"]
    except Exception as e:
        log(f"获取服务器账号失败: {e}")
    return []


def get_accounts_from_file(file_path):
    """从本地结果文件读取账号"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        accounts = data.get("accounts", [])
        log(f"从文件 {file_path} 读取到 {len(accounts)} 个账号")
        return accounts
    except Exception as e:
        log(f"读取文件失败: {e}")
        return []


def claim_one(email, password):
    """登录并领取每日积分"""
    try:
        r = http_req.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            json={"email": email, "password": password, "gotrue_meta_security": {}},
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            timeout=15,
        )
        if r.status_code != 200:
            return {"email": email, "success": False, "error": "login_failed"}

        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        r_add = http_req.post(
            f"{API_BASE}/points/add",
            json={"data": {"type": "sign_in"}},
            headers=headers,
            timeout=15,
        )

        if r_add.status_code == 200:
            resp = r_add.json()
            code = resp.get("code", "")
            if code == "SUCCESS":
                added = resp.get("data", {}).get("added", 0)
                total = resp.get("data", {}).get("available_limited", 0)
                return {"email": email, "success": True, "added": added, "total": total}
            elif code == "DUPLICATE_BUCKET":
                return {"email": email, "success": True, "added": 0, "total": 0, "duplicate": True}
            else:
                return {"email": email, "success": False, "error": f"code={code}"}
        else:
            return {"email": email, "success": False, "error": f"HTTP {r_add.status_code}"}

    except Exception as e:
        return {"email": email, "success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Oiioii 每日签到领积分")
    parser.add_argument("--accounts-file", help="从本地 JSON 文件读取账号")
    parser.add_argument("--server", help=f"服务器地址 (默认 {SERVER_URL})")
    parser.add_argument("--concurrent", type=int, default=3, help="并发数 (默认 3)")
    parser.add_argument("--limit", type=int, default=0, help="最多领取账号数 (0=全部)")
    args = parser.parse_args()

    global SERVER_URL
    if args.server:
        SERVER_URL = args.server.rstrip("/")

    log("=" * 50)
    log("  Oiioii 每日签到领积分")
    log(f"  服务器: {SERVER_URL}")
    log(f"  并发数: {args.concurrent}")
    log("=" * 50)

    accounts = []
    if args.accounts_file:
        accounts = get_accounts_from_file(args.accounts_file)
    else:
        server_accounts = get_accounts_from_server()
        for a in server_accounts:
            accounts.append({
                "email": a.get("email", ""),
                "password": a.get("password", ""),
            })

    if not accounts:
        log("没有账号需要签到")
        return

    if args.limit > 0:
        accounts = accounts[:args.limit]
        log(f"限制领取 {args.limit} 个账号")

    log(f"开始签到 {len(accounts)} 个账号...")

    results = []
    workers = max(1, min(args.concurrent, 10))
    lock = threading.Lock()
    done = 0
    claimed = 0
    skipped = 0
    failed = 0

    def do_claim(acc):
        nonlocal done, claimed, skipped, failed
        r = claim_one(acc["email"], acc["password"])
        with lock:
            done += 1
            if r["success"]:
                if r.get("added", 0) > 0:
                    claimed += 1
                    log(f"[{done}/{len(accounts)}] ✓ {acc['email']} +{r['added']} (总{r['total']})")
                else:
                    skipped += 1
                    if done % 10 == 0:
                        log(f"[{done}/{len(accounts)}] - {acc['email']} 已领过今天")
            else:
                failed += 1
                log(f"[{done}/{len(accounts)}] ✗ {acc['email']} 失败: {r.get('error')}")
        return r

    if workers <= 1:
        for acc in accounts:
            do_claim(acc)
            time.sleep(random.uniform(0.3, 1))
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(do_claim, acc): i for i, acc in enumerate(accounts)}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    log(f"线程异常: {e}")

    log("\n" + "=" * 50)
    log(f"  签到完成!")
    log(f"  总计: {len(accounts)}")
    log(f"  新领取: {claimed}  (共 +{claimed * 60} 积分)")
    log(f"  已领过: {skipped}")
    log(f"  失败: {failed}")
    log("=" * 50)

    out = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "server": SERVER_URL,
        "total": len(accounts),
        "claimed": claimed,
        "skipped": skipped,
        "failed": failed,
    }
    fname = f"daily_claim_{datetime.now().strftime('%Y%m%d')}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    log(f"结果保存到: {fname}")


if __name__ == "__main__":
    main()