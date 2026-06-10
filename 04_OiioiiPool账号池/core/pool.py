import time
import random
import string
import re
import requests
from typing import Optional, Tuple
from config import SUPABASE_URL, SUPABASE_ANON_KEY, MAIL_TM_API
from core.client import OiioiiClient
from core.db import AccountDB


class AccountPool:
    def __init__(self):
        self._clients: dict[int, OiioiiClient] = {}
        self._max_cached_clients = 30  # 最多缓存30个client，避免内存膨胀

    def _get_client(self, account_id: int, email: str, password: str,
                    token: str = "", workspace_id: str = "") -> OiioiiClient:
        if account_id not in self._clients:
            # 如果缓存满了，清理最久未用的
            if len(self._clients) >= self._max_cached_clients:
                self._evict_clients()
            self._clients[account_id] = OiioiiClient(
                email=email, password=password, token=token,
                workspace_id=workspace_id, account_id=account_id
            )
        return self._clients[account_id]

    def _evict_clients(self):
        """清理一半的缓存client，释放Session连接"""
        evict_count = len(self._clients) // 2
        to_remove = list(self._clients.keys())[:evict_count]
        for aid in to_remove:
            client = self._clients.pop(aid, None)
            if client and hasattr(client, '_session'):
                try:
                    client._session.close()
                except Exception:
                    pass

    def add_account(self, email: str, password: str) -> dict:
        client = OiioiiClient(email=email, password=password)
        if not client.login():
            return {"success": False, "error": "Login failed"}

        client.activate_user()
        points = client.get_points()
        client.ensure_workspace()

        account_id = AccountDB.add(
            email=email, password=password, token=client.token,
            workspace_id=client.workspace_id, points=points
        )
        self._clients[account_id] = client
        return {"success": True, "account_id": account_id, "points": points}

    def get_available_client(self, min_points: int = 10, prefer_lowest: bool = False,
                             video_pool: bool = False,
                             fallback_any: bool = False) -> Optional[OiioiiClient]:
        account = AccountDB.get_available(min_points, prefer_lowest, video_pool)
        if not account and fallback_any:
            account = AccountDB.get_any_active(min_points, prefer_lowest)
        if not account:
            return None

        client = self._get_client(
            account["id"], account["email"], account["password"],
            account["token"], account["workspace_id"]
        )
        client.ensure_token()
        client.ensure_workspace()
        AccountDB.update_last_used(account["id"])
        return client

    def refresh_account(self, account_id: int) -> dict:
        account = AccountDB.get_by_id(account_id)
        if not account:
            return {"success": False, "error": "Account not found"}

        client = self._get_client(
            account_id, account["email"], account["password"],
            account["token"], account["workspace_id"]
        )
        health = client.health_check()
        if health["alive"]:
            AccountDB.update_token(account_id, client.token, client.token_expiry)
            AccountDB.update_points(account_id, health["points"])
            AccountDB.update_workspace(account_id, client.workspace_id)
            AccountDB.update_status(account_id, "active")
        else:
            AccountDB.update_status(account_id, "error")

        return health

    def refresh_all(self) -> list:
        accounts = AccountDB.get_all()
        results = []
        for acc in accounts:
            health = self.refresh_account(acc["id"])
            health["email"] = acc["email"]
            health["account_id"] = acc["id"]
            results.append(health)
        return results

    def remove_account(self, account_id: int):
        self._clients.pop(account_id, None)
        AccountDB.delete(account_id)

    def get_all_accounts(self) -> list:
        return AccountDB.get_all()

    def total_points(self) -> int:
        return AccountDB.total_points()

    def active_count(self) -> int:
        return AccountDB.active_count()

    def update_points_after_use(self, account_id: int, actual_points: int, cost: int):
        AccountDB.update_points(account_id, actual_points, cost)
        if actual_points < 10:
            AccountDB.update_status(account_id, "exhausted")
            AccountDB.mark_video_used(account_id)
            print(f"[Pool] Account #{account_id} marked exhausted+video_used ({actual_points} pts remaining)")

    def daily_claim_all(self) -> dict:
        from config import DAILY_CLAIM_MIN_POINTS
        accounts = AccountDB.get_all()
        claimed = 0
        failed = 0
        skipped = 0
        reactivated = 0
        synced = 0
        now_ts = time.time()
        for acc in accounts:
            if acc.get("status") not in ("active", "exhausted"):
                skipped += 1
                continue
            client = self._get_client(
                acc["id"], acc["email"], acc["password"],
                acc.get("token", ""), acc.get("workspace_id", "")
            )
            result = client.daily_claim()
            # 签到后同步实际积分到DB
            actual_pts = client.get_points()
            if actual_pts >= 0:
                AccountDB.update_points_with_sync(acc["id"], actual_pts, now_ts)
                synced += 1
                # 根据实际积分更新状态
                if actual_pts < 10 and acc.get("status") == "active":
                    AccountDB.update_status(acc["id"], "exhausted")
                elif actual_pts >= 30 and acc.get("status") == "exhausted":
                    AccountDB.update_status(acc["id"], "active")
                if actual_pts >= DAILY_CLAIM_MIN_POINTS and acc.get("video_used") == 1:
                    AccountDB.reset_video_used(acc["id"])
                    reactivated += 1
            if result.get("success"):
                added = result.get("added", 0)
                if added > 0:
                    claimed += 1
                else:
                    skipped += 1
            else:
                failed += 1
                print(f"[Pool] daily_claim #{acc['id']} failed: {result.get('error','')[:50]}")
            time.sleep(0.5)
        print(f"[Pool] daily_claim_all: claimed={claimed} synced={synced} reactivated={reactivated} skipped={skipped} failed={failed}")
        return {"claimed": claimed, "synced": synced, "reactivated": reactivated, "skipped": skipped, "failed": failed}

    def auto_register(self) -> dict:
        from core.registrar import auto_register_sync
        result = auto_register_sync()
        if not result["success"]:
            return result
        account_id = AccountDB.add(
            email=result["email"], password=result["password"],
            token=result["token"], workspace_id=result.get("workspace_id", ""),
            points=result.get("points", 0)
        )
        self._clients.pop(account_id, None)
        return {"success": True, "account_id": account_id, "points": result.get("points", 0)}

    def auto_register_batch(self, count: int = 5) -> list:
        results = []
        for i in range(count):
            result = self.auto_register()
            results.append(result)
            if not result["success"]:
                break
            time.sleep(2)
        return results
