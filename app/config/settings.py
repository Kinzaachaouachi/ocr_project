import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).parent.parent.parent / ".env"

    load_dotenv(_env_path, override=True)
except ImportError:
    pass

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ocr_intelligence")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

BASE_DIR = Path(__file__).parent.parent.parent
APP_DIR = Path(__file__).parent.parent
SQLITE_URL = f"sqlite:///{BASE_DIR / 'ocr_database.db'}"

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "J7POd8jGPHDRfNBUoqVt5eYELwKk342s_LVHvWzRykE")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))
)

SMTP_HOST = os.getenv("SMTP_HOST", "")
_smtp_port = os.getenv("SMTP_PORT", "")
SMTP_PORT = int(_smtp_port) if _smtp_port else 587
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "OCR Intelligence")

OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "3"))

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")

STATIC_DIR = APP_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"
AVATARS_DIR = UPLOADS_DIR / "avatars"
PROFILES_DIR = STATIC_DIR / "uploads" / "profiles"

for _d in (UPLOADS_DIR, AVATARS_DIR, PROFILES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))

ALLOWED_EXTENSIONS = {
    "image": [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"],
    "pdf": [".pdf"],
    "txt": [".txt"],
    "docx": [".docx", ".doc"],
    "xlsx": [".xlsx", ".xls"],
}
ALLOWED_AVATAR_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024
