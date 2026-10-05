import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан! Добавьте его в .env или в переменные Railway.")

DATABASE_URL: str = os.getenv("DATABASE_URL", "")


def _parse_admin_ids(raw: str) -> list[int]:
    result = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


ADMIN_IDS: list[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
if not ADMIN_IDS:
    raise ValueError("ADMIN_IDS не задан! Укажите ID администраторов через запятую.")

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ---------- Камера наблюдения ----------
# 0 = веб-камера устройства; или RTSP-адрес IP-камеры
CAMERA_SOURCE = int(os.getenv("CAMERA_SOURCE", "0"))
CAMERA_MIN_AREA = int(os.getenv("CAMERA_MIN_AREA", "2500"))
CAMERA_SENSITIVITY = int(os.getenv("CAMERA_SENSITIVITY", "30"))
CAMERA_COOLDOWN = int(os.getenv("CAMERA_COOLDOWN", "30"))
CAMERA_CLIP_SECONDS = int(os.getenv("CAMERA_CLIP_SECONDS", "15"))
