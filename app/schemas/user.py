import re
from typing import Optional

from pydantic import BaseModel, validator


class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

    @validator("first_name")
    def validate_first_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError("Le prénom doit contenir au moins 2 caractères")
        return v.strip() if v else None

    @validator("last_name")
    def validate_last_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError("Le nom doit contenir au moins 2 caractères")
        return v.strip() if v else None

    @validator("email")
    def validate_email(cls, v):
        if v is not None:
            v = v.strip().lower()
            email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_regex, v):
                raise ValueError("Format d'email invalide")
        return v

    @validator("new_password")
    def validate_new_password(cls, v, values):
        if v is not None:
            if len(v) < 6:
                raise ValueError(
                    "Le nouveau mot de passe doit contenir au moins 6 caractères"
                )
            if not re.search(r"[A-Za-z]", v):
                raise ValueError("Le mot de passe doit contenir au moins une lettre")
            if not re.search(r"\d", v):
                raise ValueError("Le mot de passe doit contenir au moins un chiffre")
            if not values.get("current_password"):
                raise ValueError(
                    "Le mot de passe actuel est requis pour changer le mot de passe"
                )
        return v
