import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..config.settings import AVATARS_DIR, ALLOWED_AVATAR_EXTENSIONS, MAX_AVATAR_SIZE
from ..models.user import User


def update_user_profile(
    db: Session,
    user: User,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    current_password: Optional[str] = None,
    new_password: Optional[str] = None,
) -> User:
    """Update user profile fields."""
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if email is not None and email != user.email:

        existing = (
            db.query(User).filter(User.email == email, User.id != user.id).first()
        )
        if existing:
            raise ValueError("Un compte avec cet email existe déjà")
        user.email = email

    if new_password:
        if not current_password or not user.check_password(current_password):
            raise ValueError("Mot de passe actuel incorrect")
        user.set_password(new_password)

    db.commit()
    db.refresh(user)
    return user


async def save_avatar(user: User, file: UploadFile, db: Session) -> str:
    """Save an avatar image file and update user profile_image."""
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise ValueError(
            f"Format d'image non supporté. Formats acceptés: {', '.join(ALLOWED_AVATAR_EXTENSIONS)}"
        )

    content = await file.read()
    if len(content) > MAX_AVATAR_SIZE:
        raise ValueError(
            f"Image trop grande. Maximum: {MAX_AVATAR_SIZE // (1024*1024)} MB"
        )

    AVATARS_DIR.mkdir(parents=True, exist_ok=True)

    if user.profile_image:
        old = str(user.profile_image)
        old_name = Path(old).name
        candidates = [
            AVATARS_DIR / old_name,
            AVATARS_DIR / old.lstrip("/"),
        ]

        if "avatars" in old.replace("\\", "/"):
            candidates.append(AVATARS_DIR / old_name)
        for old_path in candidates:
            if old_path.exists() and old_path.is_file():
                try:
                    os.remove(old_path)
                except Exception:
                    pass
                break

    filename = f"avatar_{user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = AVATARS_DIR / filename

    with open(filepath, "wb") as f:
        f.write(content)

    web_path = f"/uploads/avatars/{filename}"
    user.profile_image = web_path
    db.commit()
    db.refresh(user)

    return web_path
