import hashlib
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "ocr_database")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SQLITE_URL = "sqlite:///ocr_database.db"

engine = None
SessionLocal = None

try:
    
    engine = create_engine(
        DATABASE_URL, pool_pre_ping=True, echo=False, pool_size=10, max_overflow=20
    )
   
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print(" Connecté à MySQL")
except Exception as mysql_error:
    print(f"MySQL non disponible ({mysql_error}), utilisation de SQLite")
    try:
        
        engine = create_engine(SQLITE_URL, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print(" Connecté à SQLite")
    except Exception as sqlite_error:
        print(f" Erreur de connexion SQLite: {sqlite_error}")
        engine = None
        SessionLocal = None

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)

   
    ocr_history = relationship("OCRHistory", back_populates="user")

    def set_password(self, password: str):
      
        salt = os.urandom(32)  
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 100000
        )
        self.password_hash = salt.hex() + password_hash.hex()

    def check_password(self, password: str) -> bool:
        
        try:
            salt = bytes.fromhex(self.password_hash[:64])
            stored_hash = bytes.fromhex(self.password_hash[64:])
            password_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, 100000
            )
            return stored_hash == password_hash
        except (ValueError, TypeError, AttributeError):
            return False


class OCRHistory(Base):
    __tablename__ = "ocr_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    model_id = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    extracted_text = Column(Text, nullable=True)
    char_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    ocr_time_s = Column(Float, default=0.0)
    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, default=datetime.now)
    client_ip = Column(String(50), nullable=True)

    
    user = relationship("User", back_populates="ocr_history")


def _run_migrations():
    inspector = inspect(engine)
    if "ocr_history" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("ocr_history")}
    is_sqlite = engine.url.get_backend_name() == "sqlite"

    with engine.begin() as conn:
        if "user_id" not in existing_columns:
            print(
                "Migration: ajout de la colonne 'user_id' manquante sur 'ocr_history'"
            )
            conn.execute(
                text("ALTER TABLE ocr_history ADD COLUMN user_id INTEGER NULL")
            )
            if not is_sqlite:
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE ocr_history "
                            "ADD CONSTRAINT fk_ocr_history_user "
                            "FOREIGN KEY (user_id) REFERENCES users(id)"
                        )
                    )
                except Exception as fk_error:
                    print(
                        f" Contrainte de clé étrangère non ajoutée (non bloquant) : {fk_error}"
                    )


def init_db():
    global engine, SessionLocal

    if not engine:
        print(" Moteur de base de données non disponible")
        return False

    try:
        
        Base.metadata.create_all(bind=engine)

       
        _run_migrations()

        db = SessionLocal()

        db.close()

        print(" Base de données initialisée")
        print(f"  Host: {DB_HOST}:{DB_PORT}")
        print(f"  Database: {DB_NAME}")
        print(f"  User: {DB_USER}")
        return True

    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False


def get_db() -> Session:
    
    if not SessionLocal:
        raise Exception("Base de données non configurée")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    first_name: str = None,
    last_name: str = None,
) -> User:
    
    user = User(email=email, first_name=first_name, last_name=last_name, is_active=True)
    user.set_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
