import hashlib
import random
import secrets
from datetime import datetime, timedelta
from typing import Optional, Union

try:
    import jwt
except ImportError:
    import PyJWT as jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..config.settings import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    OTP_EXPIRY_MINUTES,
    OTP_MAX_ATTEMPTS,
)
from ..models.database import get_db
from ..models.user import User
from ..models.otp import OTPCode

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[int]:
    """Decode JWT and return user_id, or None on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.PyJWTError, Exception):
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate current user from Authorization: Bearer <token>."""
    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur désactivé",
        )

    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Union[User, bool]:
    """
    Verify credentials only (active/verified checks happen in the endpoint).
    Returns User or False.
    """
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not user.check_password(password):
        return False
    return user


def create_user(
    db: Session,
    email: str,
    password: str,
    first_name: str = None,
    last_name: str = None,
    profile_image: str = None,
) -> User:
    """Create a new inactive user (email verification required)."""
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        profile_image=profile_image,
        is_active=False,
        is_email_verified=False,
    )
    user.set_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def hash_password(password: str) -> str:
    """Hash a password (mirrors User.set_password for direct updates)."""
    salt = secrets.token_bytes(32)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + pw_hash.hex()


def create_otp_code(db: Session, user_id: int) -> tuple[str, str]:
    """
    Invalidate previous unused OTPs, generate a new 6-digit OTP.
    Returns (otp_token, plain_code).
    """

    db.query(OTPCode).filter(
        OTPCode.user_id == user_id,
        OTPCode.is_used == False,
    ).update({"is_used": True})

    plain_code = f"{random.SystemRandom().randint(0, 999_999):06d}"
    code_hash = hashlib.sha256(plain_code.encode()).hexdigest()
    otp_token = secrets.token_urlsafe(32)

    otp = OTPCode(
        user_id=user_id,
        otp_token=otp_token,
        code_hash=code_hash,
        expires_at=datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        is_used=False,
        attempts=0,
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)
    return otp_token, plain_code


def verify_otp_code(
    db: Session, otp_token: str, plain_code: str
) -> tuple[Optional[int], Optional[str]]:
    """
    Verify OTP. Returns (user_id, None) on success, (None, error_message) on failure.
    """
    otp = (
        db.query(OTPCode)
        .filter(
            OTPCode.otp_token == otp_token,
            OTPCode.is_used == False,
        )
        .first()
    )

    if not otp:
        return None, "Token OTP invalide ou déjà utilisé"
    if otp.is_expired:
        return None, "Code OTP expiré. Veuillez vous reconnecter."
    if otp.attempts >= OTP_MAX_ATTEMPTS:
        return None, "Trop de tentatives. Veuillez vous reconnecter."

    otp.attempts += 1
    db.commit()

    if not otp.check_code(plain_code):
        remaining = OTP_MAX_ATTEMPTS - otp.attempts
        if remaining <= 0:
            return None, "Code incorrect. Nombre maximum de tentatives atteint."
        return None, f"Code incorrect. {remaining} tentative(s) restante(s)."

    otp.is_used = True
    db.commit()
    return otp.user_id, None


def get_otp_by_token(db: Session, otp_token: str) -> Optional[OTPCode]:
    return (
        db.query(OTPCode)
        .filter(
            OTPCode.otp_token == otp_token,
            OTPCode.is_used == False,
        )
        .first()
    )
