import hashlib
import os
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    profile_image = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)

    email_verification_token = Column(String(255), nullable=True, index=True)
    email_verification_token_expiry = Column(DateTime, nullable=True)

    reset_token = Column(String(255), nullable=True, index=True)
    reset_token_expiry = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)

    ocr_history = relationship(
        "OCRHistory", back_populates="user", cascade="all, delete-orphan"
    )
    otp_codes = relationship(
        "OTPCode", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """Hash password with PBKDF2-HMAC-SHA256 + random 32-byte salt."""
        salt = os.urandom(32)
        pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        self.password_hash = salt.hex() + pw_hash.hex()

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        try:
            salt = bytes.fromhex(self.password_hash[:64])
            stored = bytes.fromhex(self.password_hash[64:])
            candidate = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, 100_000
            )
            return stored == candidate
        except (ValueError, TypeError, AttributeError):
            return False

    @property
    def full_name(self) -> str:
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(p for p in parts if p).strip() or self.email.split("@")[0]

    @property
    def display_name(self) -> str:
        return self.full_name

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "profile_image": self.profile_image,
            "is_active": self.is_active,
            "is_email_verified": self.is_email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
