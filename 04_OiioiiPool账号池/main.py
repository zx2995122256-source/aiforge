import sys
import subprocess
import re
import time
import os
import logging
import threading
from logging.handlers import RotatingFileHandler
from datetime import datetime
import shutil
from api.server import run_api, set_public_url
from config import (
    LOG_LEVEL, LOGS_DIR, LOG_MAX_MB, TUNNEL_ENABLED,
    DB_PATH, BACKUPS_DIR, DAILY_CLAIM_ENABLED, DAILY_CLAIM_HOUR
)


def setup_logging():
    log_file = os.path.join(LOGS_DIR, "app.log")
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    max_bytes = LOG_MAX_MB * 1024 * 1024

    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return logging.getLogger(__name__)


logger = setup_logging()


def backup_db_on_startup():
    today = datetime.now().strftime("%Y-%m-%d")
    backup_path = os.path.join(BACKUPS_DIR, f"db_{today}.db")
    if os.path.exists(backup_path):
        logger.info("DB backup for %s already exists, skipping", today)
        return
    if not os.path.exists(DB_PATH):
        logger.warning("DB file not found at %s, skipping backup", DB_PATH)
        return
    shutil.copy2(DB_PATH, backup_path)
    logger.info("DB backed up to %s", backup_path)


def start_tunnel():
    if not TUNNEL_ENABLED:
        logger.info("Tunnel disabled by config")
        return None
    tunnel_log_path = os.path.join(LOGS_DIR, "tunnel.log")
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", "http://localhost:7861"],
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
                    url = m.group(0)
                    logger.info("Tunnel URL: %s", url)
                    print(f"\n=== Tunnel URL: {url} ===\n")
                    set_public_url(url)
                    return proc

        logger.warning("Failed to get tunnel URL within 30s")
        return proc
    except FileNotFoundError:
        logger.warning("cloudflared not found. Ref images won't work without tunnel.")
        return None
    except Exception as e:
        logger.error("Tunnel error: %s", e)
        return None


def daily_claim_loop():
    if not DAILY_CLAIM_ENABLED:
        logger.info("Daily claim disabled")
        return
    last_claim_date = ""
    while True:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        if today != last_claim_date and now.hour >= DAILY_CLAIM_HOUR:
            logger.info("Running daily claim for %s...", today)
            try:
                from core.pool import AccountPool
                pool = AccountPool()
                result = pool.daily_claim_all()
                logger.info("Daily claim result: %s", result)
                last_claim_date = today
            except Exception as e:
                logger.error("Daily claim failed: %s", e)
        time.sleep(600)


def main():
    logger.info("Starting OiioiiPool...")

    backup_db_on_startup()

    if DAILY_CLAIM_ENABLED:
        claim_thread = threading.Thread(target=daily_claim_loop, daemon=True)
        claim_thread.start()
        logger.info("Daily claim scheduler started (hour=%d)", DAILY_CLAIM_HOUR)

    tunnel_proc = None
    try:
        tunnel_proc = start_tunnel()
    except Exception as e:
        logger.error("Tunnel start failed: %s", e)

    logger.info("API server starting on http://localhost:7861")
    print("Open http://localhost:7861 in your browser")
    run_api()


if __name__ == "__main__":
    main()