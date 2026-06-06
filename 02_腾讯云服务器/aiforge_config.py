import os

SECRET_KEY = os.environ.get("AIFORGE_SECRET", "sk-d49fd787b24f915681aba953d1be0f29b4e30868b84436d4cf0f329c810416c6")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 72

API_HOST = "0.0.0.0"
API_PORT = 7862

OIIOII_API = "http://localhost:7861"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "aiforge.db")

POINTS_PER_YUAN = 100

PLANS = [
    {"id": "trial", "name": "体验版", "price": 9.9, "points": 900, "days": 30},
    {"id": "basic", "name": "基础版", "price": 29.9, "points": 3000, "days": 30},
    {"id": "pro", "name": "专业版", "price": 99, "points": 11000, "days": 30},
    {"id": "ultimate", "name": "至尊版", "price": 299, "points": 38000, "days": 30},
]

NEW_USER_BONUS = 50

POOL_AUTO_REPLENISH = True
POOL_MIN_ACTIVE = 3
POOL_MIN_TOTAL_POINTS = 50000
POOL_CHECK_INTERVAL = 300

PAY_URL = os.environ.get("AIFORGE_PAY_URL", "")
PAY_PID = os.environ.get("AIFORGE_PAY_PID", "")
PAY_KEY = os.environ.get("AIFORGE_PAY_KEY", "")
PAY_TYPE = os.environ.get("AIFORGE_PAY_TYPE", "epay")
