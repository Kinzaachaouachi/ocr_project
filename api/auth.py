
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Union

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session

from .database import User, get_db, get_user_by_email

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "J7POd8jGPHDRfNBUoqVt5eYELwKk342s_LVHvWzRykE")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  


security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserLogin(BaseModel):
    email: str
    password: str

    @validator("email")
    def validate_email(cls, v):
        if not v or v.strip() == "":
            raise ValueError("L'email ne peut pas être vide")

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, v):
            raise ValueError("Format d'email invalide")

        return v.lower().strip()

    @validator("password")
    def validate_password(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Le mot de passe ne peut pas être vide")

        if len(v) < 6:
            raise ValueError("Le mot de passe doit contenir au moins 6 caractères")

        return v


class UserRegister(BaseModel):
    email: str
    password: str
    confirm_password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @validator("email")
    def validate_email(cls, v):
        if not v or v.strip() == "":
            raise ValueError("L'email ne peut pas être vide")

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, v):
            raise ValueError("Format d'email invalide")

        return v.lower().strip()

    @validator("password")
    def validate_password(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Le mot de passe ne peut pas être vide")

        if len(v) < 6:
            raise ValueError("Le mot de passe doit contenir au moins 6 caractères")

        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Le mot de passe doit contenir au moins une lettre")

        if not re.search(r"\d", v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")

        return v

    @validator("confirm_password")
    def validate_confirm_password(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Les mots de passe ne correspondent pas")
        return v

    @validator("first_name")
    def validate_first_name(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError("Le prénom doit contenir au moins 2 caractères")
        return v.strip() if v else None

    @validator("last_name")
    def validate_last_name(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError("Le nom doit contenir au moins 2 caractères")
        return v.strip() if v else None


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        return None


def authenticate_user(db: Session, email: str, password: str) -> Union[User, bool]:

    user = get_user_by_email(db, email)
    if not user:
        return False
    if not user.check_password(password):
        return False
    if not user.is_active:
        return False
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:

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
            status_code=status.HTTP_403_FORBIDDEN, detail="Compte utilisateur désactivé"
        )

    return user


def create_user_response(user: User) -> UserResponse:

    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
    )
