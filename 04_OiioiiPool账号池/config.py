import os
import sys
import configparser
from datetime import datetime

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── 外部配置 config.ini ───
_cfg = configparser.ConfigParser()
_cfg.read(os.path.join(BASE_DIR, "config.ini"), encoding="utf-8")

def _get(section, key, fallback):
    try:
        return _cfg.get(section, key, fallback=fallback)
    except:
        return fallback

def _getint(section, key, fallback):
    try:
        return _cfg.getint(section, key, fallback=fallback)
    except:
        return fallback

def _getbool(section, key, fallback):
    try:
        return _cfg.getboolean(section, key, fallback=fallback)
    except:
        return fallback

# ─── 目录结构 ───
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(DATA_DIR, "output")
REFS_DIR = os.path.join(OUTPUT_DIR, "refs")
BACKUPS_DIR = os.path.join(DATA_DIR, "backups")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(DATA_DIR, "oiioii_pool.db")

# 兼容旧版：如果新路径不存在但有旧数据库，自动迁移
_old_db = os.path.join(BASE_DIR, "oiioii_pool.db")
if not os.path.exists(DB_PATH) and os.path.exists(_old_db):
    os.makedirs(DATA_DIR, exist_ok=True)
    import shutil
    shutil.copy2(_old_db, DB_PATH)
    print(f"[Config] Migrated old DB: {_old_db} -> {DB_PATH}")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REFS_DIR, exist_ok=True)
os.makedirs(BACKUPS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)


def get_date_output_dir(date_str: str = None) -> str:
    today = date_str or datetime.now().strftime("%Y-%m-%d")
    d = os.path.join(OUTPUT_DIR, today)
    os.makedirs(d, exist_ok=True)
    return d


# ─── Oiioii API ───
API_BASE = "https://api.oiioii.ai"
SUPABASE_URL = "https://spb.oiioii.ai"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVndnV6ZXN0eXlwYm1jZnVycmJkIiwicm9sZSI6ImFub24iLC"
    "JpYXQiOjE3NjEyMTU4NTEsImV4cCI6MjA3Njc5MTg1MX0."
    "Z1qdxtK0PLF5NV1yXrI9s_W2Hurdxo143DBzuUuajh0"
)
MAIL_TM_API = "https://api.mail.tm"

# ─── 服务配置 ───
API_PORT = _getint("server", "port", 7861)
API_HOST = _get("server", "host", "0.0.0.0")

# ─── 隧道 ───
TUNNEL_ENABLED = _getbool("tunnel", "enabled", True)

# ─── 数据库备份 ───
DB_BACKUP_ENABLED = _getbool("database", "backup_enabled", True)
DB_BACKUP_RETENTION_DAYS = _getint("database", "backup_retention_days", 30)

# ─── 日志 ───
LOG_LEVEL = _get("logging", "level", "INFO")
LOG_MAX_MB = _getint("logging", "max_mb", 10)
LOG_RETENTION_DAYS = _getint("logging", "retention_days", 7)

# ─── Playwright ───
PW_BROWSER = _get("playwright", "browser", "chromium")
PW_HEADLESS = _getbool("playwright", "headless", True)

# ─── 运行时 ───
MAX_CONCURRENT_GEN = 20
POINTS_WARNING_THRESHOLD = 30
VIDEO_MIN_POINTS = 60
TOKEN_REFRESH_BEFORE_EXPIRY_HOURS = 12
DAILY_CLAIM_ENABLED = True
DAILY_CLAIM_HOUR = 8
DAILY_CLAIM_MIN_POINTS = 200

# ─── 模型 ───
# 每个模型字段说明：
#   method: mcpMethodName
#   version: model 参数（None则不传）
#   cost_base: 5s/720p 的真实积分消耗（实测值）
#   cost_duration_scale: 时长系数 {5: 1.0, 8: 1.6, 10: 2.0, 15: 3.0, ...}
#   cost_resolution_scale: 分辨率系数 {"720p": 1.0, "1080p": 1.6, "2K": 1.6, "4K": 2.5}
#   default_duration: 默认时长（秒）
#   durations: 可选时长列表
#   ratios: 支持的比例
#   ref_max: 最大参考图数量（0=不支持）

RESOLUTION_SCALE = {"720p": 1.0, "1080p": 1.6, "2K": 1.6, "4K": 2.5}

IMAGE_MODELS = {
    "GPT-Image2": {"method": "generate_image_gpt_image2", "version": "gpt_image2", "cost_base": 7,
                   "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "3:4", "4:3", "Auto"], "resolutions": ["2K", "4K"], "ref_max": 10,
                   "res_scale": {"2K": 1.0, "4K": 1.857}},
    "Nano Pro": {"method": "generate_image_nano", "version": "nanopro", "cost_base": 7,
                 "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "Auto"], "resolutions": ["2K", "4K"], "ref_max": 9},
    "Nano 2": {"method": "generate_image_nano", "version": "nano2", "cost_base": 7,
               "ratios": ["16:9", "9:16", "4:3", "3:4", "1:1", "Auto"], "resolutions": ["2K", "4K"], "ref_max": 9},
    "Niji7": {"method": "generate_image_midjourney", "version": "niji7", "cost_base": 7,
              "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "resolutions": ["1K", "2K"], "ref_max": 9},
    "Niji6": {"method": "generate_image_midjourney", "version": "niji6", "cost_base": 7,
              "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"], "resolutions": ["1K", "2K"], "ref_max": 9},
    "Seedream 5.0": {"method": "generate_image_seedream50", "version": "seedream50", "cost_base": 7,
                     "ratios": ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "21:9", "Auto"], "resolutions": ["2K", "3K", "4K"], "ref_max": 9},
    "Seedream 4.5": {"method": "generate_image_seedream45", "version": "seedream45", "cost_base": 7,
                     "ratios": ["1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "21:9", "Auto"], "resolutions": ["2K", "4K"], "ref_max": 9},
    "NovelAI": {"method": "generate_image_novelai", "version": None, "cost_base": 7,
                "ratios": ["9:16", "16:9", "1:1", "2:3", "3:2"], "resolutions": ["1K"], "ref_max": 9},
    "Gpt 4o": {"method": "generate_image_gpt4o", "version": None, "cost_base": 7,
               "ratios": ["1:1", "3:2", "2:3"], "resolutions": ["1K"], "ref_max": 0},
}

VIDEO_MODELS_DIRECT = {
    "Vidu Q2": {
        "method": "generate_video_vidu", "version": "viduQ2", "cost_base": 25,
        "cost_duration_scale": {5: 1.0, 8: 1.6},
        "default_duration": 5, "durations": [5, 6, 7, 8], "ratios": ["16:9", "9:16", "1:1"],
        "resolutions": ["720p", "1080p"],
        "ref_max": 9, "timeout": 300,
    },
    "Kling 2.6": {
        "method": "generate_video_kling", "version": "2.6", "cost_base": 25,
        "cost_duration_scale": {5: 1.0, 10: 2.0},
        "default_duration": 5, "durations": [5, 10], "ratios": ["16:9", "9:16", "1:1"],
        "resolutions": ["720p", "1080p"],
        "ref_max": 9, "timeout": 420,
    },
    "Kling O1": {
        "method": "generate_video_kling_o1", "version": None, "cost_base": 40,
        "cost_duration_scale": {5: 1.0, 10: 2.0},
        "default_duration": 5, "durations": [5, 10], "ratios": ["16:9", "9:16", "1:1"],
        "resolutions": ["720p", "1080p"],
        "ref_max": 9, "timeout": 600,
    },
    "Hailuo 2.3 Std": {
        "method": "generate_video_hailuo02", "version": "hailuo23standard", "cost_base": 25,
        "cost_duration_scale": {6: 1.0, 10: 1.7},
        "default_duration": 6, "durations": [6, 10], "ratios": ["16:9", "9:16"],
        "resolutions": ["720p", "1080p"],
        "ref_max": 9, "timeout": 420,
    },
    "Hailuo 2.3 Pro": {
        "method": "generate_video_hailuo02", "version": "hailuo23pro", "cost_base": 40,
        "cost_duration_scale": {6: 1.0},
        "default_duration": 6, "durations": [6], "ratios": ["16:9", "9:16"],
        "resolutions": ["720p", "1080p"],
        "ref_max": 9, "timeout": 420,
    },
    "Wan2.7": {
        "method": "generate_video_wan27", "version": None, "cost_base": 25,
        "cost_duration_scale": {5: 1.0, 10: 2.0, 15: 3.0},
        "default_duration": 5, "durations": [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], "ratios": ["16:9", "9:16", "1:1"],
        "resolutions": ["720p", "1080p"],
        "ref_max": 20, "video_ref": True, "timeout": 600,
    },
    "Gemini Omni": {
        "method": "generate_video_gemini_omni", "version": None, "cost_base": 54,
        "cost_duration_scale": {4: 0.8, 6: 1.2, 8: 1.6, 10: 2.0},
        "default_duration": 6, "durations": [4, 6, 8, 10], "ratios": ["16:9", "9:16"],
        "resolutions": ["720p", "1080p", "4K"],
        "res_scale": {"720p": 1.0, "1080p": 1.4, "4K": 2.4},
        "ref_max": 7, "video_ref": True, "timeout": 900,
    },
    "Grok Imagine": {
        "method": "generate_video_grok_imagine", "version": None, "cost_base": 24,
        "cost_duration_scale": {6: 1.0, 10: 1.667, 15: 2.5, 20: 3.333, 30: 5.0},
        "default_duration": 6, "durations": [6, 8, 10, 12, 15, 20, 25, 30], "ratios": ["16:9", "9:16", "1:1", "2:3", "3:2"],
        "resolutions": ["480p", "720p"],
        "ref_max": 1, "timeout": 600,
    },
    "Seedance 1.5 Pro": {
        "method": "generate_video_seedance10_pro", "version": "Seedance1-5Pro", "cost_base": 40,
        "cost_duration_scale": {5: 0.7, 8: 1.0, 10: 1.2, 12: 1.5},
        "default_duration": 10, "durations": [10, 4, 5, 6, 7, 8, 9, 11, 12], "ratios": ["16:9", "9:16", "1:1"],
        "resolutions": ["720p", "1080p"],
        "ref_max": 9, "timeout": 600,
    },
}

def get_video_model(name):
    return VIDEO_MODELS_DIRECT.get(name)

def calc_video_cost(model_name: str, duration: int = 5, resolution: str = "720p") -> int:
    m = get_video_model(model_name)
    if not m:
        return 50
    base = m.get("cost_base", 25)
    dur_scale = m.get("cost_duration_scale", {})
    dur_factor = dur_scale.get(duration, round(duration / 5, 1))
    # 优先用模型自己的 res_scale，没有就用全局的
    model_res = m.get("res_scale", {})
    res_factor = model_res.get(resolution, RESOLUTION_SCALE.get(resolution, 1.0))
    return int(base * dur_factor * res_factor)

def get_model_cost(name, duration: int = 5, resolution: str = "720p") -> int:
    m = get_video_model(name)
    if m:
        return calc_video_cost(name, duration, resolution)
    im = IMAGE_MODELS.get(name)
    if im:
        model_res = im.get("res_scale", {})
        res_factor = model_res.get(resolution, RESOLUTION_SCALE.get(resolution, 1.0))
        return int(im.get("cost_base", 7) * res_factor)
    return 50