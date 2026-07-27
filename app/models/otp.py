import hashlib
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
)
from sqlalchemy.orm import relationship

from .database import Base


class OTPCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    otp_token = Column(String(128), unique=True, index=True, nullable=False)
    code_hash = Column(String(128), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    attempts = Column(SmallInteger, default=0)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="otp_codes")

    def check_code(self, code: str) -> bool:
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        return self.code_hash == code_hash

    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
