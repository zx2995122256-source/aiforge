"""本地注册 Oiioii 账号 → 自动推送到服务器账号池

使用方法：
    python local_register_and_sync.py --count 10
    python local_register_and_sync.py --count 50 --concurrent 3
    python local_register_and_sync.py --continuous --target 100

原理：
    1. 本地用 Playwright 注册 mail.tm 临时邮箱 + Oiioii 账号
    2. 注册成功后自动 POST 到服务器的 /pool/api/pool/add
    3. 服务器收到 email+password 后自行登录验证并加入账号池
    4. 服务器不跑浏览器，只收 HTTP 请求
"""
import os
import sys
import time
import json
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 复用 OiioiiPool 的注册逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.registrar import auto_register_sync

# ─── 服务器地址 ───
SERVER_URL = os.environ.get("AIFORGE_SERVER", "http://122.51.205.94")


def push_account_to_server(email: str, password: str) -> bool:
    """注册成功后，把账号推送到服务器的 OiioiiPool"""
    import requests
    try:
        r = requests.post(
            f"{SERVER_URL}/pool/api/pool/add",
            json={"email": email, "password": password},
            timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            print(f"  ✓ 推送到服务器成功: account_id={data.get('account_id')}, points={data.get('points')}")
            return True
        else:
            error = r.json().get("detail", r.text[:100])
            print(f"  ✗ 推送失败 (HTTP {r.status_code}): {error}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ✗ 无法连接到服务器 {SERVER_URL}/api/pool/add")
        return False
    except Exception as e:
        print(f"  ✗ 推送异常: {e}")
        return False


def register_one(index: int, total: int) -> dict:
    """注册单个账号并推送到服务器"""
    tag = f"[{index+1}/{total}]"
    print(f"\n{tag} 开始注册...")

    start = time.time()
    result = auto_register_sync()
    elapsed = time.time() - start

    if not result["success"]:
        print(f"{tag} 注册失败 ({elapsed:.0f}s): {result.get('error', '未知错误')}")
        return {"index": index, "success": False, "error": result.get("error", "")}

    email = result.get("email", "")
    password = result.get("password", "")
    points = result.get("points", 0)
    print(f"{tag} 注册成功! email={email} points={points} ({elapsed:.0f}s)")

    push_ok = push_account_to_server(email, password)

    return {
        "index": index,
        "success": True,
        "email": email,
        "password": password,
        "points": points,
        "pushed": push_ok,
    }


def main():
    parser = argparse.ArgumentParser(description="本地注册 Oiioii 账号并同步到服务器")
    parser.add_argument("--count", type=int, default=5, help="注册数量")
    parser.add_argument("--concurrent", type=int, default=1, help="并发注册数（1-3）")
    parser.add_argument("--continuous", action="store_true", help="持续注册模式（达到 target 后停止）")
    parser.add_argument("--target", type=int, default=50, help="连续模式目标数量")
    parser.add_argument("--server", default=None, help="服务器地址")
    args = parser.parse_args()

    global SERVER_URL
    if args.server:
        SERVER_URL = args.server.rstrip("/")

    print("=" * 60)
    print("  Oiioii 账号注册 + 推送服务器")
    print("=" * 60)
    print(f"  服务器地址: {SERVER_URL}")
    print(f"  注册模式: {'连续注册' if args.continuous else '批量注册'}")
    if args.continuous:
        print(f"  目标数量: {args.target}")
    else:
        print(f"  注册数量: {args.count}")
    print(f"  并发数: {args.concurrent}")
    print("=" * 60)

    if args.continuous:
        _run_continuous(args.target, args.concurrent)
    else:
        _run_batch(args.count, args.concurrent)


def _run_batch(count: int, concurrent: int):
    """批量注册模式"""

    if concurrent <= 1 or count <= 1:
        # 串行
        results = []
        for i in range(count):
            r = register_one(i, count)
            results.append(r)
            if i < count - 1:
                print("  等待 3 秒后继续...")
                time.sleep(3)
    else:
        # 并发
        workers = min(concurrent, 3)  # 最多3并发
        results = [None] * count
        print(f"\n并发注册: workers={workers}")
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_idx = {}
            for i in range(count):
                future_to_idx[executor.submit(register_one, i, count)] = i
                time.sleep(2)  # 错开提交防止同时触验证码
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    print(f"[{idx+1}/{count}] 线程异常: {e}")
                    results[idx] = {"index": idx, "success": False, "error": str(e)}

    _print_summary(results)


def _run_continuous(target: int, concurrent: int):
    """持续注册模式"""
    success_count = 0
    fail_count = 0
    results = []

    print(f"\n开始连续注册，目标 {target} 个...")
    while success_count < target:
        r = register_one(success_count + fail_count, target)
        results.append(r)
        if r["success"]:
            success_count += 1
            print(f"  进度: {success_count}/{target}")
        else:
            fail_count += 1
            print(f"  失败: {fail_count} 次")

        if success_count >= target:
            break

        wait = 5 if r["success"] else 10
        print(f"  等待 {wait} 秒...")
        time.sleep(wait)

    _print_summary(results)


def _print_summary(results: list):
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    pushed = [r for r in successful if r.get("pushed")]

    print("\n" + "=" * 60)
    print("  注册完成！")
    print(f"  总计: {len(results)}")
    print(f"  成功: {len(successful)}")
    print(f"  失败: {len(failed)}")
    print(f"  已推送到服务器: {len(pushed)}")
    if failed:
        print("\n  失败原因:")
        for f in failed[:5]:
            print(f"    - {f.get('error', '未知')}")
    print("=" * 60)

    # 保存结果到文件
    output = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(results),
        "success": len(successful),
        "failed": len(failed),
        "pushed": len(pushed),
        "accounts": [
            {"email": r["email"], "password": r.get("password", ""), "points": r.get("points", 0)}
            for r in successful
        ],
    }
    fname = f"register_result_{int(time.time())}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到: {fname}")

    if not pushed and successful and failed:
        print("\n⚠ 部分注册成功但推送失败，账号信息如下（可手动添加到服务器管理后台）:")
        for r in successful[:3]:
            if not r.get("pushed"):
                print(f"  email: {r.get('email')}  password: {r.get('password', '')}")


if __name__ == "__main__":
    main()