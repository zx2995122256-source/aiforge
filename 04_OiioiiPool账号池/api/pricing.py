"""API 定价配置

价格单位：人民币（元）
支持的模型列表 + 对外暴露的模型名 → 内部模型名映射
"""

# 对外暴露的模型名 → 内部模型名 + 定价
# 图片模型
IMAGE_PRICING = {
    "gpt-image-2": {
        "internal": "GPT-Image2",
        "prices": {
            ("1K",): 0.06,
            ("2K",): 0.06,
            ("4K",): 0.09,
        }
    },
}

# 视频模型
VIDEO_PRICING = {
    "grok-imagine": {
        "internal": "Grok Imagine",
        "prices": {
            (6, "720p"): 0.15,
            (10, "720p"): 0.35,
            (15, "720p"): 0.50,
            (20, "720p"): 0.65,
            (30, "720p"): 0.95,
        }
    },
    "gemini-omni": {
        "internal": "Gemini Omni",
        "prices": {
            (4, "720p"): 0.30,
            (6, "720p"): 0.40,
            (8, "720p"): 0.50,
            (10, "720p"): 0.50,
            (4, "1080p"): 0.40,
            (6, "1080p"): 0.55,
            (8, "1080p"): 0.65,
            (10, "1080p"): 0.70,
            (4, "4K"): 0.60,
            (6, "4K"): 0.80,
            (8, "4K"): 1.00,
            (10, "4K"): 1.00,
        }
    },
}

# 合并
ALL_MODELS = {}
ALL_MODELS.update(IMAGE_PRICING)
ALL_MODELS.update(VIDEO_PRICING)


def get_price(model: str, duration: int = 0, resolution: str = "2K") -> float:
    """获取对外模型的价格"""
    info = ALL_MODELS.get(model)
    if not info:
        return -1

    prices = info["prices"]
    if model in IMAGE_PRICING:
        key = (resolution,)
    else:
        key = (duration, resolution)

    price = prices.get(key)
    if price is None:
        # 找最近的时长
        if model in VIDEO_PRICING:
            matching = [(k, v) for k, v in prices.items() if k[1] == resolution]
            if matching:
                matching.sort(key=lambda x: abs(x[0][0] - duration))
                price = matching[0][1]
            else:
                price = -1
        else:
            price = -1
    return price


def get_internal_model(model: str) -> str:
    """对外模型名 → 内部模型名"""
    info = ALL_MODELS.get(model)
    return info["internal"] if info else model


def get_model_type(model: str) -> str:
    """image or video"""
    if model in IMAGE_PRICING:
        return "image"
    elif model in VIDEO_PRICING:
        return "video"
    return "unknown"


def list_models() -> list:
    """列出所有可用模型及价格"""
    result = []
    for name, info in ALL_MODELS.items():
        model_entry = {
            "id": name,
            "internal": info["internal"],
            "type": "image" if name in IMAGE_PRICING else "video",
            "prices": []
        }
        for key, price in info["prices"].items():
            if name in IMAGE_PRICING:
                model_entry["prices"].append({"resolution": key[0], "price": price})
            else:
                model_entry["prices"].append({"duration": key[0], "resolution": key[1], "price": price})
        result.append(model_entry)
    return result
