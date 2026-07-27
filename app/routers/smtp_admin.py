import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.email_service import (
    test_smtp_connection,
    set_smtp_config,
    get_smtp_config_current,
    detect_smtp_preset,
    _SMTP_PRESETS,
)
from ..config.settings import BASE_DIR

router = APIRouter(prefix="/api/admin/smtp", tags=["Admin SMTP"])

_ENV_PATH = BASE_DIR / ".env"


class SMTPConfig(BaseModel):
    host: str
    port: int = 587
    user: str
    password: str
    from_email: str = ""
    from_name: str = "OCR Intelligence"
    use_ssl: bool = False


class SMTPTestRequest(BaseModel):
    host: str
    port: int = 587
    user: str
    password: str
    use_ssl: bool = False
    test_recipient: str = ""


class SMTPPresetRequest(BaseModel):
    email: str


def _update_env_file(updates: dict) -> bool:
    """Update key=value pairs in .env file. Creates file if missing."""
    try:
        env_path = _ENV_PATH
        lines = []
        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8").splitlines()

        updated_keys = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                new_lines.append(line)
                continue
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
            else:
                new_lines.append(line)

        for key, value in updates.items():
            if key not in updated_keys:
                new_lines.append(f"{key}={value}")

        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        return True
    except Exception as e:
        print(f" Impossible de mettre à jour .env : {e}")
        return False


def _mask_password(pwd: str) -> str:
    if not pwd or pwd in ("votre_mot_de_passe_application", ""):
        return ""
    if len(pwd) <= 4:
        return "****"
    return pwd[:2] + "****" + pwd[-2:]


def _is_placeholder(value: str) -> bool:
    placeholders = {
        "votre.email@gmail.com",
        "votre_mot_de_passe_application",
        "",
    }
    return value.strip() in placeholders


@router.get("/config")
async def get_smtp_config():
    """Return current SMTP configuration (password masked)."""
    cfg = get_smtp_config_current()
    user = cfg.get("user", "")
    from_email = cfg.get("from_email", "")

    preset_info = None
    sender = from_email or user
    if sender and "@" in sender:
        preset = detect_smtp_preset(sender)
        if preset:
            domain = sender.split("@")[-1].lower()
            preset_info = {
                "domain": domain,
                "host": preset["host"],
                "port": preset["port"],
                "ssl": preset["ssl"],
            }

    is_configured = (
        bool(cfg.get("host"))
        and not _is_placeholder(cfg.get("user", ""))
        and not _is_placeholder(cfg.get("password", ""))
    )

    return {
        "host": cfg.get("host", ""),
        "port": cfg.get("port", 587),
        "user": user if not _is_placeholder(user) else "",
        "from_email": from_email if not _is_placeholder(from_email) else "",
        "from_name": cfg.get("from_name", "OCR Intelligence"),
        "use_ssl": cfg.get("use_ssl", False),
        "password_set": bool(cfg.get("password"))
        and not _is_placeholder(cfg.get("password", "")),
        "password_masked": _mask_password(cfg.get("password", "")),
        "is_configured": is_configured,
        "preset_detected": preset_info,
        "available_presets": [
            {"domain": k, "host": v["host"], "port": v["port"], "ssl": v["ssl"]}
            for k, v in _SMTP_PRESETS.items()
        ],
    }


@router.post("/detect-preset")
async def detect_preset(req: SMTPPresetRequest):
    """Auto-detect SMTP settings from email address."""
    preset = detect_smtp_preset(req.email)
    if not preset:
        return {
            "detected": False,
            "message": "Aucun preset connu pour ce domaine. Configurez manuellement.",
        }
    return {
        "detected": True,
        "host": preset["host"],
        "port": preset["port"],
        "use_ssl": preset["ssl"],
        "message": f"Paramètres SMTP détectés pour {req.email.split('@')[-1]}",
    }


@router.post("/test")
async def test_smtp(req: SMTPTestRequest):
    """Test SMTP connection with provided credentials."""
    if not req.host or not req.user or not req.password:
        raise HTTPException(
            status_code=400, detail="Hôte, utilisateur et mot de passe sont requis"
        )

    result = test_smtp_connection(
        host=req.host,
        port=req.port,
        user=req.user,
        password=req.password,
        use_ssl=req.use_ssl,
        test_recipient=req.test_recipient or req.user,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": result["message"],
                "details": result["details"],
                "step": result["step"],
            },
        )

    return {
        "success": True,
        "message": result["message"],
        "details": result["details"],
        "test_email_sent_to": req.test_recipient or req.user,
    }


@router.post("/save")
async def save_smtp_config(cfg: SMTPConfig):
    """Save SMTP configuration to .env and apply at runtime."""
    if not cfg.host or not cfg.user:
        raise HTTPException(status_code=400, detail="Hôte et utilisateur SMTP requis")

    from_email = cfg.from_email or cfg.user

    from ..services.email_service import _normalize_smtp_password, _gmail_password_hint

    password = _normalize_smtp_password(cfg.password)

    hint = _gmail_password_hint(cfg.user, password)
    if hint and "longueur actuelle" in hint:
        raise HTTPException(
            status_code=400,
            detail=(
                "Pour Gmail, SMTP_PASSWORD doit être un Mot de passe d'application "
                "de 16 caractères (pas le mot de passe du compte). "
                "Créez-en un ici: https://myaccount.google.com/apppasswords"
            ),
        )

    set_smtp_config(
        {
            "host": cfg.host,
            "port": cfg.port,
            "user": cfg.user,
            "password": password,
            "from_email": from_email,
            "from_name": cfg.from_name,
            "use_ssl": cfg.use_ssl,
        }
    )

    env_updates = {
        "SMTP_HOST": cfg.host,
        "SMTP_PORT": str(cfg.port),
        "SMTP_USER": cfg.user,
        "SMTP_PASSWORD": password,
        "SMTP_FROM": from_email,
        "SMTP_FROM_NAME": cfg.from_name,
    }
    saved = _update_env_file(env_updates)

    return {
        "success": True,
        "message": "Configuration SMTP sauvegardée et appliquée.",
        "env_updated": saved,
        "config": {
            "host": cfg.host,
            "port": cfg.port,
            "user": cfg.user,
            "from_email": from_email,
            "from_name": cfg.from_name,
            "use_ssl": cfg.use_ssl,
        },
    }


@router.get("/status")
async def smtp_status():
    """Quick SMTP readiness check with last error details."""
    from ..services.email_service import get_last_smtp_error, _gmail_password_hint

    cfg = get_smtp_config_current()
    user = cfg.get("user", "")
    host = cfg.get("host", "")
    password = cfg.get("password", "")
    last_err = get_last_smtp_error()
    hint = _gmail_password_hint(user, password)

    is_ready = (
        bool(host)
        and bool(user)
        and bool(password)
        and not _is_placeholder(user)
        and not _is_placeholder(password)
    )

    looks_like_gmail_app_password = len((password or "").replace(" ", "")) == 16

    return {
        "ready": is_ready,
        "host": host if is_ready else "",
        "user": user if is_ready else "",
        "gmail_app_password_ok": (
            looks_like_gmail_app_password if "gmail" in (user or "").lower() else None
        ),
        "hint": hint,
        "last_error": last_err if last_err.get("code") else None,
        "message": (
            "SMTP configuré et prêt"
            if is_ready and (not hint or "longueur actuelle" not in hint)
            else (
                hint
                or "SMTP non configuré / identifiants invalides — les emails s'affichent dans la console"
            )
        ),
    }
