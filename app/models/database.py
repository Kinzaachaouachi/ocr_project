from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from ..config.settings import (
    DATABASE_URL,
    SQLITE_URL,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
)

engine = None
SessionLocal = None
Base = declarative_base()


def _connect() -> bool:
    """Try MySQL first, fallback to SQLite. Returns True if connected."""
    global engine, SessionLocal

    try:
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            echo=False,
            pool_size=10,
            max_overflow=20,
        )
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine = _engine
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print(f"[DB] Connected to MySQL -- {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
        return True
    except Exception as mysql_err:
        print(f"[DB] MySQL unavailable ({mysql_err}), switching to SQLite")

    try:
        sqlite_path = Path(SQLITE_URL.replace("sqlite:///", ""))
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            SQLITE_URL,
            echo=False,
            connect_args={"check_same_thread": False, "timeout": 20},
        )
        engine = _engine
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print(f"[DB] Connected to SQLite -- {SQLITE_URL}")
        return True
    except Exception as sqlite_err:
        print(f"[DB] SQLite error: {sqlite_err}")
        engine = None
        SessionLocal = None
        return False


def _run_migrations():
    """Lightweight schema migrations — adds missing columns only."""
    if not engine:
        return

    inspector = inspect(engine)
    is_sqlite = engine.url.get_backend_name() == "sqlite"
    existing_tables = set(inspector.get_table_names())

    if "ocr_history" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("ocr_history")}
        new_cols = {
            "user_id": "ALTER TABLE ocr_history ADD COLUMN user_id INTEGER NULL",
            "precision_score": "ALTER TABLE ocr_history ADD COLUMN precision_score FLOAT NULL",
            "init_time_s": "ALTER TABLE ocr_history ADD COLUMN init_time_s FLOAT DEFAULT 0.0",
            "robustness": "ALTER TABLE ocr_history ADD COLUMN robustness FLOAT NULL",
            "global_score": "ALTER TABLE ocr_history ADD COLUMN global_score FLOAT NULL",
            "file_path": "ALTER TABLE ocr_history ADD COLUMN file_path VARCHAR(1000) NULL",
            "file_type": "ALTER TABLE ocr_history ADD COLUMN file_type VARCHAR(50) NULL",
            "client_ip": "ALTER TABLE ocr_history ADD COLUMN client_ip VARCHAR(50) NULL",
            "execution_time": "ALTER TABLE ocr_history ADD COLUMN execution_time FLOAT DEFAULT 0",
            "confidence_score": "ALTER TABLE ocr_history ADD COLUMN confidence_score FLOAT DEFAULT 0",
            "detected_language": "ALTER TABLE ocr_history ADD COLUMN detected_language VARCHAR(10) DEFAULT 'auto'",
        }
        with engine.begin() as conn:
            for col, sql in new_cols.items():
                if col not in existing_cols:
                    print(f"[DB] Migration ocr_history: add column '{col}'")
                    conn.execute(text(sql))

            if "user_id" not in existing_cols and not is_sqlite:
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE ocr_history "
                            "ADD CONSTRAINT fk_ocr_history_user "
                            "FOREIGN KEY (user_id) REFERENCES users(id)"
                        )
                    )
                except Exception:
                    pass

    if "users" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("users")}
        new_cols = {
            "profile_image": "ALTER TABLE users ADD COLUMN profile_image VARCHAR(500) NULL",
            "first_name": "ALTER TABLE users ADD COLUMN first_name VARCHAR(100) NULL",
            "last_name": "ALTER TABLE users ADD COLUMN last_name VARCHAR(100) NULL",
            "is_email_verified": "ALTER TABLE users ADD COLUMN is_email_verified BOOLEAN DEFAULT 0",
            "email_verification_token": "ALTER TABLE users ADD COLUMN email_verification_token VARCHAR(255) NULL",
            "email_verification_token_expiry": "ALTER TABLE users ADD COLUMN email_verification_token_expiry DATETIME NULL",
            "reset_token": "ALTER TABLE users ADD COLUMN reset_token VARCHAR(255) NULL",
            "reset_token_expiry": "ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME NULL",
        }
        with engine.begin() as conn:
            for col, sql in new_cols.items():
                if col not in existing_cols:
                    print(f"[DB] Migration users: add column '{col}'")
                    conn.execute(text(sql))

    if "otp_codes" in existing_tables:
        existing_cols = {c["name"] for c in inspector.get_columns("otp_codes")}
        otp_new_cols = {
            "otp_token": "ALTER TABLE otp_codes ADD COLUMN otp_token VARCHAR(128) NULL",
            "code_hash": "ALTER TABLE otp_codes ADD COLUMN code_hash VARCHAR(128) NULL",
            "attempts": "ALTER TABLE otp_codes ADD COLUMN attempts SMALLINT DEFAULT 0",
        }
        with engine.begin() as conn:
            for col, sql in otp_new_cols.items():
                if col not in existing_cols:
                    print(f"[DB] Migration otp_codes: add column '{col}'")
                    conn.execute(text(sql))

            if "otp_token" not in existing_cols or "otp_token" in existing_cols:
                try:
                    indexes = {ix["name"] for ix in inspector.get_indexes("otp_codes")}
                    if "idx_otp_token" not in indexes and "otp_token" in (
                        existing_cols | {"otp_token"}
                    ):
                        conn.execute(
                            text(
                                "CREATE UNIQUE INDEX idx_otp_token ON otp_codes (otp_token)"
                            )
                        )
                except Exception:
                    pass


def init_db() -> bool:
    """Create all tables and run migrations. Returns True on success."""
    global engine, SessionLocal

    if not engine:
        print("[DB] ERROR: Database engine not available")
        return False

    try:

        from . import user, otp, ocr_history

        Base.metadata.create_all(bind=engine)
        _run_migrations()
        print("[DB] Database initialized successfully")
        return True
    except Exception as e:
        print(f"[DB] ERROR init: {e}")
        return False


def get_db():
    """FastAPI dependency — yield a scoped database session."""
    if not SessionLocal:
        raise RuntimeError("Database not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_connect()
