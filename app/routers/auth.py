import secrets
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..config.settings import APP_BASE_URL, PROFILES_DIR
from ..models.database import get_db
from ..models.user import User
from ..schemas.auth import (
    OTPLoginResponse,
    OTPVerifyRequest,
    ResendOTPRequest,
    TokenResponse,
    UserLogin,
    UserResponse,
)
from ..services.auth_service import (
    authenticate_user,
    create_access_token,
    create_otp_code,
    create_user,
    get_current_user,
    get_otp_by_token,
    get_user_by_email,
    verify_otp_code,
    hash_password,
)
from ..services.email_service import (
    OTP_EXPIRY_MINUTES,
    send_otp_email,
    send_password_reset_email,
    send_email_verification,
    get_last_smtp_error,
)

router = APIRouter(prefix="/api", tags=["Authentification"])


def _verification_link(token: str) -> str:
    return f"{APP_BASE_URL}/verify-email?token={token}"


def _email_delivery_meta() -> dict:
    err = get_last_smtp_error()
    if err.get("code"):
        return {
            "email_delivered": False,
            "email_delivery": "console_fallback",
            "smtp_error": err.get("message") or err.get("code"),
            "smtp_hint": err.get("hint")
            or (
                "Vérifiez la configuration SMTP dans le fichier .env — pour Gmail utilisez un "
                "Mot de passe d'application (16 caractères)."
            ),
        }
    return {
        "email_delivered": True,
        "email_delivery": "smtp",
    }


def _issue_and_send_otp(db: Session, user: User) -> tuple[str, str, dict]:
    otp_token, plain_code = create_otp_code(db, user.id)
    send_otp_email(
        to_email=user.email,
        otp_code=plain_code,
        user_name=user.first_name or user.email.split("@")[0],
        expires_minutes=OTP_EXPIRY_MINUTES,
    )
    return otp_token, plain_code, _email_delivery_meta()


def _send_verification_to_user(db: Session, user: User) -> tuple[str, dict]:
    verification_token = secrets.token_urlsafe(32)
    user.email_verification_token = verification_token
    user.email_verification_token_expiry = datetime.now() + timedelta(hours=24)
    db.commit()
    link = _verification_link(verification_token)
    send_email_verification(
        to_email=user.email,
        verification_link=link,
        user_name=user.full_name,
    )
    return verification_token, _email_delivery_meta()


@router.post("/register", response_model=dict)
async def register(
    email: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    profile_image: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    try:

        if password != confirm_password:
            raise HTTPException(
                status_code=400, detail="Les mots de passe ne correspondent pas"
            )
        if not first_name.strip():
            raise HTTPException(status_code=400, detail="Le prénom est obligatoire")
        if not last_name.strip():
            raise HTTPException(
                status_code=400, detail="Le nom de famille est obligatoire"
            )
        if get_user_by_email(db, email):
            raise HTTPException(
                status_code=400, detail="Un compte avec cet email existe déjà"
            )

        profile_image_path = None
        if profile_image and profile_image.filename:
            allowed = {"image/jpeg", "image/png", "image/gif", "image/webp"}
            if profile_image.content_type not in allowed:
                raise HTTPException(
                    status_code=400,
                    detail="Format d'image non supporté (JPEG/PNG/GIF/WebP)",
                )
            contents = await profile_image.read()
            if len(contents) > 5 * 1024 * 1024:
                raise HTTPException(
                    status_code=400, detail="Image trop volumineuse (max 5 MB)"
                )
            ext = Path(profile_image.filename).suffix.lower()
            filename = f"{secrets.token_hex(16)}{ext}"
            (PROFILES_DIR).mkdir(parents=True, exist_ok=True)
            (PROFILES_DIR / filename).write_bytes(contents)
            profile_image_path = f"/static/uploads/profiles/{filename}"

        user = create_user(
            db=db,
            email=email,
            password=password,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            profile_image=profile_image_path,
        )

        user.is_active = False
        user.is_email_verified = False
        _, delivery = _send_verification_to_user(db, user)

        msg = (
            "Compte créé ! Un email de vérification a été envoyé. "
            "Activez votre compte via le lien reçu, puis un code OTP "
            "sera envoyé pour finaliser la connexion."
        )
        if not delivery.get("email_delivered"):
            msg = (
                "Compte créé, mais l'email de vérification n'a pas pu être envoyé "
                "(erreur SMTP). Vérifiez la configuration et renvoyez l'email."
            )

        return {
            "message": msg,
            "email": user.email,
            "verification_sent": True,
            "requires_email_verification": True,
            **delivery,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {e}")


@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email_verification_token == token).first()
        if not user:
            raise HTTPException(
                status_code=400, detail="Token de vérification invalide ou expiré"
            )

        if (
            user.email_verification_token_expiry
            and user.email_verification_token_expiry < datetime.now()
        ):
            raise HTTPException(
                status_code=400, detail="Ce lien a expiré. Demandez un nouveau lien."
            )

        user.is_email_verified = True
        user.is_active = True
        user.email_verification_token = None
        user.email_verification_token_expiry = None
        db.commit()

        otp_token, _, delivery = _issue_and_send_otp(db, user)
        email_hint = user.email
        expires_in = OTP_EXPIRY_MINUTES * 60

        message = (
            "Email vérifié ! Votre compte est activé. "
            f"Un code OTP a été envoyé à {email_hint}."
        )
        if not delivery.get("email_delivered"):
            message = (
                "Compte activé, mais l'email OTP n'a pas pu être envoyé (SMTP). "
                "Reconnectez-vous après correction SMTP, ou renvoyez le code."
            )

        return {
            "success": True,
            "message": message,
            "otp_token": otp_token,
            "email_hint": email_hint,
            "expires_in": expires_in,
            "otp_sent": True,
            **delivery,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {e}")


@router.post("/resend-verification")
async def resend_verification(email: str = Form(...), db: Session = Depends(get_db)):
    try:
        user = get_user_by_email(db, email)
        if not user:
            return {
                "message": "Si un compte existe avec cet email, un lien a été envoyé.",
                "success": True,
            }

        if user.is_email_verified:
            raise HTTPException(
                status_code=400,
                detail="Ce compte est déjà vérifié. Connectez-vous pour recevoir un OTP.",
            )

        _, delivery = _send_verification_to_user(db, user)

        msg = "Un nouveau lien de vérification a été envoyé. Après activation, un code OTP suivra."
        if not delivery.get("email_delivered"):
            msg = "Échec d'envoi SMTP. Vérifiez la config email puis renvoyez le lien."

        return {
            "message": msg,
            "success": True,
            "verification_sent": True,
            **delivery,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {e}")


@router.post("/login")
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=401, detail="Email ou mot de passe incorrect"
            )

        if not user.is_email_verified:
            _, delivery = _send_verification_to_user(db, user)
            detail = (
                "Compte non vérifié. Un email de vérification vient d'être "
                "envoyé à votre adresse. Cliquez sur le lien pour activer "
                "votre compte — un code OTP sera ensuite envoyé."
            )
            if not delivery.get("email_delivered"):
                detail = (
                    "Compte non vérifié. L'email de vérification n'a pas pu être envoyé "
                    "(erreur SMTP). Cliquez sur « Renvoyer » après correction SMTP."
                )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": detail,
                    "code": "EMAIL_NOT_VERIFIED",
                    "verification_sent": True,
                    "email": user.email,
                    "email_hint": user.email,
                    "requires_email_verification": True,
                    **delivery,
                },
            )

        if not user.is_active:
            raise HTTPException(
                status_code=403,
                detail="Compte désactivé. Contactez le support.",
            )

        otp_token, _, delivery = _issue_and_send_otp(db, user)
        message = f"Un code de vérification a été envoyé à {user.email}"
        if not delivery.get("email_delivered"):
            message = (
                "Échec d'envoi du code OTP (SMTP). "
                "Vérifiez la configuration email puis renvoyez le code."
            )

        return OTPLoginResponse(
            otp_token=otp_token,
            email_hint=user.email,
            expires_in=OTP_EXPIRY_MINUTES * 60,
            message=message,
            email_delivered=delivery.get("email_delivered"),
            email_delivery=delivery.get("email_delivery"),
            smtp_error=delivery.get("smtp_error"),
            smtp_hint=delivery.get("smtp_hint"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {e}")


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(verify_data: OTPVerifyRequest, db: Session = Depends(get_db)):
    try:
        user_id, error = verify_otp_code(
            db, verify_data.otp_token, verify_data.otp_code
        )
        if error:
            raise HTTPException(status_code=401, detail=error)

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=401, detail="Compte introuvable ou désactivé"
            )

        user.last_login = datetime.now()
        db.commit()

        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 60 * 60,
            user=UserResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                profile_image=user.profile_image,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {e}")


@router.post("/resend-otp", response_model=OTPLoginResponse)
async def resend_otp(resend_data: ResendOTPRequest, db: Session = Depends(get_db)):
    try:
        otp = get_otp_by_token(db, resend_data.otp_token)
        if not otp:
            raise HTTPException(
                status_code=404,
                detail="Session OTP introuvable. Veuillez vous reconnecter.",
            )

        elapsed = (datetime.now() - otp.created_at).total_seconds()
        if elapsed < 60:
            wait = int(60 - elapsed)
            raise HTTPException(
                status_code=429, detail=f"Patientez {wait}s avant de renvoyer le code."
            )

        user = db.query(User).filter(User.id == otp.user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=401, detail="Compte introuvable ou désactivé"
            )

        new_otp_token, _, delivery = _issue_and_send_otp(db, user)

        return OTPLoginResponse(
            otp_token=new_otp_token,
            email_hint=user.email,
            expires_in=OTP_EXPIRY_MINUTES * 60,
            message=f"Nouveau code envoyé à {user.email}",
            email_delivered=delivery.get("email_delivered"),
            email_delivery=delivery.get("email_delivery"),
            smtp_error=delivery.get("smtp_error"),
            smtp_hint=delivery.get("smtp_hint"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {e}")


@router.post("/forgot-password")
async def forgot_password(data: dict, db: Session = Depends(get_db)):
    try:
        email = data.get("email", "").strip()
        if not email:
            raise HTTPException(status_code=400, detail="L'email est requis")

        user = get_user_by_email(db, email)
        if not user:
            return {
                "message": "Si un compte existe avec cet email, un lien a été envoyé.",
                "success": True,
            }

        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expiry = datetime.now() + timedelta(hours=1)
        db.commit()

        reset_link = f"{APP_BASE_URL}/reset-password?token={reset_token}"
        send_password_reset_email(
            to_email=user.email,
            reset_link=reset_link,
            user_name=user.first_name or user.email.split("@")[0],
        )

        return {
            "message": "Un lien de réinitialisation a été envoyé à votre email.",
            "success": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {e}")


@router.post("/reset-password")
async def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        if new_password != confirm_password:
            raise HTTPException(
                status_code=400, detail="Les mots de passe ne correspondent pas"
            )

        user = db.query(User).filter(User.reset_token == token).first()
        if not user:
            raise HTTPException(status_code=400, detail="Token invalide ou expiré")

        if user.reset_token_expiry and user.reset_token_expiry < datetime.now():
            raise HTTPException(
                status_code=400, detail="Ce lien a expiré. Faites une nouvelle demande."
            )

        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.commit()

        return {"message": "Mot de passe réinitialisé avec succès", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {e}")


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Déconnexion réussie", "user": current_user.email}
