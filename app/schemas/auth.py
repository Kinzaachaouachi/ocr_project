import re
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, validator, Field


class UserLogin(BaseModel):
    email: str = Field(..., description="Adresse email de l'utilisateur")
    password: str = Field(..., description="Mot de passe de l'utilisateur")

    @validator("email")
    def validate_email(cls, v):
        if not v or v.strip() == "":
            raise ValueError("L'email ne peut pas être vide")

        v = v.strip().lower()

        if len(v) > 254:
            raise ValueError("L'email est trop long (maximum 254 caractères)")

        email_regex = r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.([a-zA-Z]{2,})$"
        if not re.match(email_regex, v):
            raise ValueError("Format d'email invalide")

        forbidden_chars = [" ", "\t", "\n", "\r"]
        if any(char in v for char in forbidden_chars):
            raise ValueError("L'email contient des caractères non autorisés")

        local_part = v.split("@")[0]
        if len(local_part) > 64:
            raise ValueError(
                "La partie locale de l'email est trop longue (maximum 64 caractères)"
            )

        return v

    @validator("password")
    def validate_password(cls, v):
        if not v:
            raise ValueError("Le mot de passe ne peut pas être vide")

        if len(v) < 6:
            raise ValueError("Le mot de passe doit contenir au moins 6 caractères")

        if len(v) > 128:
            raise ValueError("Le mot de passe est trop long (maximum 128 caractères)")

        dangerous_chars = ["\0", "\x01", "\x02", "\x03", "\x04", "\x05"]
        if any(char in v for char in dangerous_chars):
            raise ValueError("Le mot de passe contient des caractères non autorisés")

        return v


class UserRegister(BaseModel):
    email: str = Field(
        ..., description="Adresse email (sera utilisée comme identifiant)"
    )
    password: str = Field(..., min_length=8, description="Mot de passe sécurisé")
    confirm_password: str = Field(..., description="Confirmation du mot de passe")
    first_name: str = Field(..., min_length=2, max_length=50, description="Prénom")
    last_name: str = Field(
        ..., min_length=2, max_length=50, description="Nom de famille"
    )

    @validator("email")
    def validate_email(cls, v):
        if not v or v.strip() == "":
            raise ValueError("L'email est obligatoire")

        v = v.strip().lower()

        if len(v) > 254:
            raise ValueError("L'email est trop long (maximum 254 caractères)")

        email_regex = r"^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.([a-zA-Z]{2,})$"
        if not re.match(email_regex, v):
            raise ValueError("Format d'email invalide")

        forbidden_chars = [" ", "\t", "\n", "\r", "+", "="]
        if any(char in v for char in forbidden_chars):
            raise ValueError("L'email contient des caractères non autorisés")

        parts = v.split("@")
        if len(parts) != 2:
            raise ValueError("Format d'email invalide")

        local_part, domain = parts
        if len(local_part) < 1 or len(local_part) > 64:
            raise ValueError(
                "La partie locale de l'email doit contenir entre 1 et 64 caractères"
            )

        if len(domain) < 4 or len(domain) > 253:
            raise ValueError("Le domaine de l'email est invalide")

        domain_regex = r"^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.([a-zA-Z]{2,})$"
        if not re.match(domain_regex, domain):
            raise ValueError("Le domaine de l'email est invalide")

        return v

    @validator("password")
    def validate_password(cls, v):
        if not v:
            raise ValueError("Le mot de passe est obligatoire")

        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")

        if len(v) > 128:
            raise ValueError("Le mot de passe est trop long (maximum 128 caractères)")

        errors = []

        if not re.search(r"[a-z]", v):
            errors.append("au moins une lettre minuscule")

        if not re.search(r"[A-Z]", v):
            errors.append("au moins une lettre majuscule")

        if not re.search(r"\d", v):
            errors.append("au moins un chiffre")

        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            errors.append("au moins un caractère spécial (!@#$%^&*...)")

        if errors:
            raise ValueError(f"Le mot de passe doit contenir {', '.join(errors)}")

        weak_passwords = [
            "password",
            "123456",
            "123456789",
            "qwerty",
            "abc123",
            "password123",
            "admin",
            "letmein",
            "welcome",
            "monkey",
            "1234567890",
            "password1",
            "123123",
            "admin123",
        ]

        if v.lower() in weak_passwords:
            raise ValueError(
                "Ce mot de passe est trop commun. Choisissez un mot de passe plus sécurisé"
            )

        sequences = ["123456", "abcdef", "qwerty", "azerty", "654321"]
        if any(seq in v.lower() for seq in sequences):
            raise ValueError(
                "Le mot de passe ne doit pas contenir de séquences évidentes"
            )

        dangerous_chars = ["\0", "\x01", "\x02", "\x03", "\x04", "\x05"]
        if any(char in v for char in dangerous_chars):
            raise ValueError("Le mot de passe contient des caractères non autorisés")

        return v

    @validator("confirm_password")
    def validate_confirm_password(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Les mots de passe ne correspondent pas")
        return v

    @validator("first_name")
    def validate_first_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Le prénom est obligatoire")

        v = v.strip()

        if len(v) < 2:
            raise ValueError("Le prénom doit contenir au moins 2 caractères")

        if len(v) > 50:
            raise ValueError("Le prénom est trop long (maximum 50 caractères)")

        if not re.match(r"^[a-zA-ZàâäéèêëîïôöùûüÿñçÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÑÇ\s\-']+$", v):
            raise ValueError(
                "Le prénom ne peut contenir que des lettres, espaces, tirets et apostrophes"
            )

        if not re.search(r"[a-zA-ZàâäéèêëîïôöùûüÿñçÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÑÇ]", v):
            raise ValueError("Le prénom doit contenir au moins une lettre")

        return " ".join(word.capitalize() for word in v.split())

    @validator("last_name")
    def validate_last_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Le nom de famille est obligatoire")

        v = v.strip()

        if len(v) < 2:
            raise ValueError("Le nom de famille doit contenir au moins 2 caractères")

        if len(v) > 50:
            raise ValueError("Le nom de famille est trop long (maximum 50 caractères)")

        if not re.match(r"^[a-zA-ZàâäéèêëîïôöùûüÿñçÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÑÇ\s\-']+$", v):
            raise ValueError(
                "Le nom de famille ne peut contenir que des lettres, espaces, tirets et apostrophes"
            )

        if not re.search(r"[a-zA-ZàâäéèêëîïôöùûüÿñçÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÑÇ]", v):
            raise ValueError("Le nom de famille doit contenir au moins une lettre")

        return " ".join(word.capitalize() for word in v.split())


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    profile_image: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class OTPLoginResponse(BaseModel):
    otp_token: str
    email_hint: str
    expires_in: int
    message: str
    email_delivered: Optional[bool] = True
    email_delivery: Optional[str] = "smtp"
    smtp_error: Optional[str] = None
    smtp_hint: Optional[str] = None


class OTPVerifyRequest(BaseModel):
    otp_token: str = Field(..., description="Token OTP reçu lors du login")
    otp_code: str = Field(..., description="Code à 6 chiffres reçu par email")

    @validator("otp_token")
    def validate_otp_token(cls, v):
        if not v or not v.strip():
            raise ValueError("Le token OTP est requis")

        v = v.strip()

        if len(v) < 20:
            raise ValueError("Token OTP invalide (trop court)")

        if len(v) > 128:
            raise ValueError("Token OTP invalide (trop long)")

        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Token OTP invalide (caractères non autorisés)")

        return v

    @validator("otp_code")
    def validate_otp_code(cls, v):
        if not v:
            raise ValueError("Le code OTP est requis")

        v = v.strip().replace(" ", "").replace("-", "")

        if not v.isdigit():
            raise ValueError("Le code OTP doit contenir uniquement des chiffres")

        if len(v) != 6:
            raise ValueError("Le code OTP doit contenir exactement 6 chiffres")

        return v


class ResendOTPRequest(BaseModel):
    otp_token: str = Field(..., description="Token OTP pour lequel renvoyer le code")

    @validator("otp_token")
    def validate_otp_token(cls, v):
        if not v or not v.strip():
            raise ValueError("Le token OTP est requis")

        v = v.strip()

        if len(v) < 20 or len(v) > 128:
            raise ValueError("Token OTP invalide")

        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Token OTP invalide")

        return v
