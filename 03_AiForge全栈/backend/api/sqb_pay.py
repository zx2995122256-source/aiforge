"""
收钱吧(SQB)支付模块 - 集成到AiForge后端
文档参考: https://shouqianba.com
流程: 用户点充值 → 后端创建订单+唯一金额 → 前端展示聚合码 → 用户扫码 → 收钱吧回调 → 自动加积分
"""
import time
import hashlib
import json
import uuid
import requests
from typing import Optional

# 收钱吧配置 - 通过环境变量设置
SQB_VENDOR_SN = ""    # 商户号
SQB_VENDOR_KEY = ""   # API密钥
SQB_APP_ID = ""       # AppID
SQB_API_BASE = "https://v2.shouqianba.com"

# 聚合码图片URL - 在收钱吧后台获取你的聚合码图片链接
SQB_QR_CODE_URL = ""


def init_sqb(vendor_sn: str, vendor_key: str, app_id: str, qr_code_url: str = ""):
    global SQB_VENDOR_SN, SQB_VENDOR_KEY, SQB_APP_ID, SQB_QR_CODE_URL
    SQB_VENDOR_SN = vendor_sn
    SQB_VENDOR_KEY = vendor_key
    SQB_APP_ID = app_id
    SQB_QR_CODE_URL = qr_code_url


def _generate_sign(params: dict, key: str) -> str:
    """收钱吧签名算法: 按key排序拼接 → MD5"""
    sorted_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None and v != "")
    sign_str = sorted_str + key
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest()


def _make_request(path: str, biz_data: dict) -> dict:
    """收钱吧API通用请求"""
    terminal_sn = str(uuid.uuid4())[:32]
    client_sn = str(int(time.time() * 1000))

    params = {
        "app_id": SQB_APP_ID,
        "timestamp": str(int(time.time())),
        "client_sn": client_sn,
    }
    sign = _generate_sign(params, SQB_VENDOR_KEY)
    params["sign"] = sign

    payload = {
        "terminal_sn": terminal_sn,
        "client_sn": client_sn,
        **biz_data
    }

    try:
        resp = requests.post(
            f"{SQB_API_BASE}{path}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        print(f"[SQB] request error: {e}")
        return {"error": str(e)}


def create_sqb_order(order_id: int, amount: float, plan_name: str) -> dict:
    """
    创建收钱吧支付订单
    使用唯一金额区分订单: 实际金额 + 0.01 * order_id
    例如: 30元套餐 → 订单#1=30.01, 订单#2=30.02
    """
    if not SQB_VENDOR_SN:
        return {"error": "收钱吧未配置"}

    # 唯一金额: 基础价 + 订单号*0.01
    unique_amount = round(amount + order_id * 0.01, 2)

    biz_data = {
        "vendor_sn": SQB_VENDOR_SN,
        "amount": int(unique_amount * 100),  # 收钱吧金额单位是分
        "subject": f"锤子Aicg-{plan_name}",
        "operator": "system",
        "sn": str(order_id),  # 我们的订单号
    }

    result = _make_request("/api/v2/pay/create", biz_data)

    return {
        "order_id": order_id,
        "pay_method": "sqb",
        "qr_url": SQB_QR_CODE_URL,
        "amount": unique_amount,
        "plan_name": plan_name,
        "msg": f"请扫码支付 ¥{unique_amount}（精确金额，勿改）",
        "status": "pending",
        "sqb_result": result,
    }


def verify_sqb_callback(data: dict) -> bool:
    """验证收钱吧回调签名"""
    sign = data.pop("sign", "")
    if not sign or not SQB_VENDOR_KEY:
        return False
    expected = _generate_sign(data, SQB_VENDOR_KEY)
    return sign == expected


def handle_sqb_callback(data: dict) -> dict:
    """
    处理收钱吧回调
    收钱吧会在用户支付成功后POST通知到这里
    """
    if not verify_sqb_callback(data):
        return {"status": "sign_error"}

    order_status = data.get("order_status", "")
    if order_status != "PAID":
        return {"status": "ignored", "order_status": order_status}

    # 从sn字段获取我们的订单号
    sn = data.get("sn", "")
    total_amount = data.get("total_amount", 0)  # 分
    amount_yuan = round(total_amount / 100, 2) if total_amount else 0

    try:
        order_id = int(sn)
    except (ValueError, TypeError):
        return {"status": "invalid_sn"}

    return {
        "status": "paid",
        "order_id": order_id,
        "amount": amount_yuan,
        "trade_no": data.get("transaction_id", f"sqb_{order_id}"),
    }


def query_sqb_order(order_id: int) -> Optional[dict]:
    """
    主动查询收钱吧订单状态
    用于前端轮询确认支付结果
    """
    if not SQB_VENDOR_SN:
        return None

    biz_data = {
        "vendor_sn": SQB_VENDOR_SN,
        "sn": str(order_id),
    }

    result = _make_request("/api/v2/pay/query", biz_data)

    if result.get("biz_response", {}).get("data", {}).get("order_status") == "PAID":
        return {
            "status": "paid",
            "order_id": order_id,
            "trade_no": result["biz_response"]["data"].get("transaction_id", ""),
        }

    return {"status": "pending", "order_id": order_id}
