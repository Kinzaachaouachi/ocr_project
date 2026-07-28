import smtplib
import ssl
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from ..config.settings import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM,
    SMTP_FROM_NAME,
    OTP_EXPIRY_MINUTES,
)

_runtime_config: dict = {}
_last_smtp_error: dict = {"code": "", "message": "", "hint": ""}


def _safe_print(*args, **kwargs) -> None:
    """Print that never crashes on Windows consoles without UTF-8."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        text = " ".join(str(a) for a in args)
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(
            text.encode(encoding, errors="replace").decode(encoding, errors="replace"),
            **kwargs,
        )


def _normalize_smtp_password(password: str) -> str:
    """Gmail app passwords are often copied with spaces — strip them."""
    if not password:
        return ""

    stripped = password.strip()

    no_spaces = stripped.replace(" ", "")
    if len(no_spaces) == 16 and no_spaces.isalnum():
        return no_spaces
    return stripped


def _gmail_password_hint(user: str, password: str) -> str:
    """Message d'aide si les identifiants Gmail semblent incorrects."""
    domain = (user or "").split("@")[-1].lower()
    if (
        domain not in ("gmail.com", "googlemail.com")
        and "gmail" not in (user or "").lower()
    ):
        return ""
    clean = (password or "").replace(" ", "")
    if not clean:
        return "SMTP_PASSWORD est vide."
    if len(clean) != 16:
        return (
            f"Gmail refuse souvent un mot de passe normal (longueur actuelle: {len(clean)}). "
            "Créez un 'Mot de passe d'application' de 16 caractères : "
            "https://myaccount.google.com/apppasswords "
            "(la validation en 2 étapes Google doit être activée)."
        )
    return (
        "Mot de passe d'application détecté (16 car.). "
        "Si l'auth échoue encore: régénérez-le et vérifiez SMTP_USER."
    )


def get_last_smtp_error() -> dict:
    return _last_smtp_error.copy()


def set_smtp_config(config: dict) -> None:
    """Override SMTP config at runtime (from admin panel)."""
    global _runtime_config
    cfg = dict(config or {})
    if "password" in cfg:
        cfg["password"] = _normalize_smtp_password(cfg.get("password") or "")
    _runtime_config = cfg


def get_smtp_config_current() -> dict:
    """Return current effective SMTP config (runtime override or .env values)."""
    if _runtime_config:
        return _runtime_config.copy()
    return {
        "host": SMTP_HOST or "",
        "port": SMTP_PORT or 587,
        "user": SMTP_USER or "",
        "password": SMTP_PASSWORD or "",
        "from_email": SMTP_FROM or SMTP_USER or "",
        "from_name": SMTP_FROM_NAME or "OCR Intelligence",
        "use_ssl": (SMTP_PORT == 465),
    }


_SMTP_PRESETS: dict[str, dict] = {
    "gmail.com": {"host": "smtp.gmail.com", "port": 587, "ssl": False},
    "googlemail.com": {"host": "smtp.gmail.com", "port": 587, "ssl": False},
    "outlook.com": {"host": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "hotmail.com": {"host": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "live.com": {"host": "smtp-mail.outlook.com", "port": 587, "ssl": False},
    "yahoo.com": {"host": "smtp.mail.yahoo.com", "port": 587, "ssl": False},
    "yahoo.fr": {"host": "smtp.mail.yahoo.com", "port": 587, "ssl": False},
    "ovh.net": {"host": "ssl0.ovh.net", "port": 465, "ssl": True},
    "ovh.com": {"host": "ssl0.ovh.net", "port": 465, "ssl": True},
    "ionos.com": {"host": "smtp.ionos.com", "port": 587, "ssl": False},
    "ionos.fr": {"host": "smtp.ionos.fr", "port": 587, "ssl": False},
    "sendgrid.net": {"host": "smtp.sendgrid.net", "port": 587, "ssl": False},
    "mailgun.org": {"host": "smtp.mailgun.org", "port": 587, "ssl": False},
    "zoho.com": {"host": "smtp.zoho.com", "port": 587, "ssl": False},
    "zoho.eu": {"host": "smtp.zoho.eu", "port": 587, "ssl": False},
    "protonmail.com": {"host": "127.0.0.1", "port": 1025, "ssl": False},
    "icloud.com": {"host": "smtp.mail.me.com", "port": 587, "ssl": False},
}


def detect_smtp_preset(email: str) -> Optional[dict]:
    """Return SMTP preset for a given email address, or None."""
    if "@" not in email:
        return None
    domain = email.split("@")[-1].lower()
    return _SMTP_PRESETS.get(domain)


def _resolve_smtp_config(sender_email: str) -> dict:
    """
    Resolve final SMTP config priority:
    1. Runtime override (_runtime_config)
    2. Auto-preset from sender domain
    3. .env values
    """
    if _runtime_config:
        return {
            "host": _runtime_config.get("host", SMTP_HOST),
            "port": int(_runtime_config.get("port", SMTP_PORT or 587)),
            "use_ssl": _runtime_config.get("use_ssl", False),
            "user": _runtime_config.get("user", SMTP_USER),
            "password": _normalize_smtp_password(
                _runtime_config.get("password", SMTP_PASSWORD) or ""
            ),
            "sender": _runtime_config.get("from_email", sender_email),
            "from_name": _runtime_config.get(
                "from_name", SMTP_FROM_NAME or "OCR Intelligence"
            ),
        }

    preset = detect_smtp_preset(sender_email)
    if preset:
        return {
            "host": preset["host"],
            "port": preset["port"],
            "use_ssl": preset["ssl"],
            "user": SMTP_USER or sender_email,
            "password": _normalize_smtp_password(SMTP_PASSWORD or ""),
            "sender": sender_email,
            "from_name": SMTP_FROM_NAME or "OCR Intelligence",
        }

    return {
        "host": SMTP_HOST or "",
        "port": int(SMTP_PORT or 587),
        "use_ssl": (SMTP_PORT == 465),
        "user": SMTP_USER or "",
        "password": _normalize_smtp_password(SMTP_PASSWORD or ""),
        "sender": SMTP_FROM or SMTP_USER or sender_email,
        "from_name": SMTP_FROM_NAME or "OCR Intelligence",
    }


def _set_smtp_error(code: str, message: str, hint: str = "") -> None:
    global _last_smtp_error
    _last_smtp_error = {"code": code, "message": message, "hint": hint}


def _send_smtp(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    """
    Attempt to send via SMTP with automatic fallback:
      1) mode configuré (STARTTLS 587 ou SSL 465)
      2) si échec STARTTLS → réessai SSL sur 465 (Gmail)
    Returns True on success, False on any failure.
    """
    sender = SMTP_FROM or SMTP_USER
    if _runtime_config:
        sender = (
            _runtime_config.get("from_email")
            or _runtime_config.get("user", "")
            or sender
        )

    if not sender:
        msg = "Aucun email expéditeur configuré (SMTP_FROM vide)"
        _safe_print(f"❌* SMTP : {msg}")
        _set_smtp_error("NO_SENDER", msg)
        return False

    cfg = _resolve_smtp_config(sender)

    port = int(cfg.get("port") or 587)
    use_ssl = bool(cfg.get("use_ssl")) or port == 465
    cfg["port"] = port
    cfg["use_ssl"] = use_ssl

    if not cfg["host"]:
        msg = "SMTP_HOST non configuré dans .env ou admin panel"
        _safe_print(f"❌ SMTP : {msg}")
        _set_smtp_error("NO_HOST", msg)
        return False
    if not cfg["password"]:
        msg = "SMTP_PASSWORD non configuré"
        _safe_print(f"❌ SMTP : {msg}")
        _set_smtp_error(
            "NO_PASSWORD", msg, _gmail_password_hint(cfg.get("user", ""), "")
        )
        return False
    if not cfg["user"]:
        msg = "SMTP_USER non configuré"
        _safe_print(f"❌ SMTP : {msg}")
        _set_smtp_error("NO_USER", msg)
        return False

    gmail_hint = _gmail_password_hint(cfg.get("user", ""), cfg.get("password", ""))
    if gmail_hint and "longueur actuelle" in gmail_hint:
        _safe_print(f"⚠️  SMTP Gmail : {gmail_hint}")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{cfg['from_name']} <{cfg['sender']}>"
    msg["To"] = to_email
    msg["X-Mailer"] = "OCR Intelligence Mailer v2"
    msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()

    attempts = []
    if cfg["use_ssl"]:
        attempts.append({"host": cfg["host"], "port": cfg["port"] or 465, "ssl": True})
        if cfg["host"] == "smtp.gmail.com":
            attempts.append({"host": "smtp.gmail.com", "port": 587, "ssl": False})
    else:
        attempts.append({"host": cfg["host"], "port": cfg["port"] or 587, "ssl": False})

        attempts.append({"host": cfg["host"], "port": 465, "ssl": True})

    last_error = None
    for attempt in attempts:
        try:
            if attempt["ssl"]:
                _safe_print(
                    f"📤 Connexion SMTP SSL vers {attempt['host']}:{attempt['port']}..."
                )
                with smtplib.SMTP_SSL(
                    attempt["host"], attempt["port"], context=context, timeout=25
                ) as server:

                    server.ehlo("localhost")
                    server.login(cfg["user"], cfg["password"])
                    server.sendmail(cfg["sender"], [to_email], msg.as_string())
            else:
                _safe_print(
                    f"📤 Connexion SMTP STARTTLS vers {attempt['host']}:{attempt['port']}..."
                )
                with smtplib.SMTP(
                    attempt["host"], attempt["port"], timeout=25
                ) as server:

                    code, _ = server.ehlo("localhost")
                    if code >= 400:
                        raise smtplib.SMTPException(f"EHLO refusé ({code})")
                    if not server.has_extn("starttls"):
                        raise smtplib.SMTPException(
                            "STARTTLS extension not supported by server."
                        )
                    server.starttls(context=context)
                    server.ehlo("localhost")
                    server.login(cfg["user"], cfg["password"])
                    server.sendmail(cfg["sender"], [to_email], msg.as_string())

            _safe_print(
                f"✅ Email envoyé via SMTP ({attempt['host']}:{attempt['port']}) → {to_email}"
            )
            _set_smtp_error("", "", "")
            return True

        except smtplib.SMTPAuthenticationError as e:
            _safe_print(f"❌ SMTP Auth Error: {e}")
            _safe_print(
                "   → Pour Gmail: Mot de passe d'application (16 car.), PAS le mot de passe du compte"
            )
            if gmail_hint:
                _safe_print(f"   → {gmail_hint}")
            _set_smtp_error(
                "AUTH_FAILED",
                "Identifiants SMTP refusés (535 BadCredentials).",
                gmail_hint or "Vérifiez SMTP_USER / SMTP_PASSWORD.",
            )
            return False
        except Exception as e:
            last_error = e
            _safe_print(
                f"⚠️  Échec {attempt['host']}:{attempt['port']} → {type(e).__name__}: {e}"
            )
            continue

    _safe_print(f"❌ Envoi email échoué après tous les essais: {last_error}")
    _set_smtp_error(
        "SMTP_ERROR",
        str(last_error) if last_error else "Échec SMTP",
        "Vérifiez le réseau/antivirus (port 587/465) et la config SMTP.",
    )
    return False


def test_smtp_connection(
    host: str,
    port: int,
    user: str,
    password: str,
    use_ssl: bool = False,
    test_recipient: str = "",
) -> dict:
    """
    Test SMTP connection and optionally send a test email.
    Returns a dict with success, message, and details.
    """
    password = _normalize_smtp_password(password)
    result = {
        "success": False,
        "step": "",
        "message": "",
        "details": "",
        "hint": _gmail_password_hint(user, password),
    }

    context = ssl.create_default_context()

    try:
        result["step"] = "connection"
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, context=context, timeout=15)
            server.ehlo("localhost")
        else:
            server = smtplib.SMTP(host, port, timeout=15)
            server.ehlo("localhost")
            result["step"] = "starttls"
            server.starttls(context=context)
            server.ehlo("localhost")

        result["step"] = "authentication"
        server.login(user, password)

        if test_recipient:
            result["step"] = "send_test"
            html, text = _test_html(user, host)
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "✅ Test SMTP — OCR Intelligence"
            msg["From"] = f"OCR Intelligence <{user}>"
            msg["To"] = test_recipient
            msg.attach(MIMEText(text, "plain", "utf-8"))
            msg.attach(MIMEText(html, "html", "utf-8"))
            server.sendmail(user, [test_recipient], msg.as_string())
            result["details"] = f"Email de test envoyé à {test_recipient}"

        server.quit()
        result["success"] = True
        result["message"] = f"Connexion SMTP réussie vers {host}:{port}"
        if test_recipient:
            result["message"] += f" | Email de test envoyé à {test_recipient}"
        _set_smtp_error("", "", "")
        return result

    except smtplib.SMTPAuthenticationError as e:
        result["message"] = "Erreur d'authentification SMTP (identifiants refusés)"
        result["details"] = (
            "Pour Gmail : utilisez un Mot de passe d'application (16 caractères), "
            "pas le mot de passe du compte Google.\n"
            "1) Activez la validation en 2 étapes\n"
            "2) Créez un MDP d'app : https://myaccount.google.com/apppasswords\n"
            f"Erreur serveur: {e}"
        )
        if result["hint"]:
            result["details"] = result["hint"] + "\n\n" + result["details"]
        _set_smtp_error("AUTH_FAILED", result["message"], result["hint"])
        return result
    except smtplib.SMTPConnectError as e:
        result["message"] = f"Impossible de se connecter à {host}:{port}"
        result["details"] = str(e)
        return result
    except ConnectionRefusedError:
        result["message"] = f"Connexion refusée par {host}:{port}"
        result["details"] = "Vérifiez le serveur SMTP et le port"
        return result
    except TimeoutError:
        result["message"] = f"Timeout lors de la connexion à {host}:{port}"
        result["details"] = "Le serveur ne répond pas dans les délais"
        return result
    except ssl.SSLError as e:
        result["message"] = "Erreur SSL/TLS"
        result["details"] = str(e)
        return result
    except Exception as e:
        result["message"] = f"Erreur: {type(e).__name__}"
        result["details"] = str(e)
        return result


def _console_fallback(label: str, to_email: str, content: str) -> None:
    """Print email content to console when SMTP is unavailable."""
    sep = "═" * 70
    _safe_print(f"\n{sep}")
    _safe_print(f"📧 {label}")
    _safe_print(f"   Destinataire : {to_email}")
    _safe_print(f"   Contenu      :")
    for line in content.strip().splitlines():
        _safe_print(f"   {line}")
    _safe_print(f"{sep}\n")
    _safe_print(
        "SMTP non configuré. Renseignez SMTP_* dans le fichier .env"
    )


def _base_html(title: str, content: str) -> str:
    """Wrap content in branded HTML email layout."""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    body {{ margin:0; padding:0; background:#0f172a; font-family:'Segoe UI',Arial,sans-serif; }}
    .wrapper {{ max-width:600px; margin:0 auto; padding:40px 20px; }}
    .card {{ background:#1e293b; border-radius:16px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.5); }}
    .header {{ background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#06b6d4 100%); padding:40px 40px 32px; text-align:center; }}
    .header-icon {{ font-size:48px; margin-bottom:12px; }}
    .header h1 {{ color:#fff; margin:0; font-size:24px; font-weight:700; letter-spacing:-0.5px; }}
    .header p {{ color:rgba(255,255,255,0.8); margin:8px 0 0; font-size:14px; }}
    .body {{ padding:40px; }}
    .greeting {{ color:#94a3b8; font-size:15px; margin-bottom:24px; }}
    .greeting strong {{ color:#e2e8f0; }}
    .message {{ color:#cbd5e1; font-size:15px; line-height:1.7; margin-bottom:28px; }}
    .btn {{ display:inline-block; background:linear-gradient(135deg,#6366f1,#8b5cf6); color:#fff !important;
            text-decoration:none; padding:14px 36px; border-radius:10px; font-size:15px;
            font-weight:600; letter-spacing:0.3px; margin:8px 0 28px; }}
    .btn:hover {{ background:linear-gradient(135deg,#4f46e5,#7c3aed); }}
    .otp-box {{ background:#0f172a; border:2px solid #6366f1; border-radius:12px; padding:20px;
                text-align:center; margin:24px 0; }}
    .otp-code {{ font-size:42px; font-weight:800; letter-spacing:12px; color:#6366f1;
                 font-family:'Courier New',monospace; }}
    .otp-expires {{ color:#64748b; font-size:13px; margin-top:8px; }}
    .divider {{ border:none; border-top:1px solid #334155; margin:28px 0; }}
    .note {{ background:#0f172a; border-left:3px solid #6366f1; border-radius:4px;
             padding:14px 18px; color:#94a3b8; font-size:13px; line-height:1.6; margin-bottom:24px; }}
    .link-fallback {{ word-break:break-all; color:#6366f1; font-size:13px; }}
    .footer {{ background:#0f172a; padding:24px 40px; text-align:center; }}
    .footer p {{ color:#475569; font-size:12px; margin:4px 0; }}
    .footer a {{ color:#6366f1; text-decoration:none; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="card">
      <div class="header">
        <div class="header-icon">📄</div>
        <h1>OCR Intelligence</h1>
        <p>Plateforme d'extraction de texte par IA</p>
      </div>
      <div class="body">
        {content}
      </div>
      <div class="footer">
        <p>© {datetime.now().year} OCR Intelligence — Tous droits réservés</p>
        <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
      </div>
    </div>
  </div>
</body>
</html>"""


def _verification_html(user_name: str, verification_link: str) -> tuple[str, str]:
    """Generate HTML + plain text for account activation email."""
    content = f"""
<p class="greeting">Bonjour <strong>{user_name}</strong> 👋</p>
<p class="message">
  Bienvenue sur <strong>OCR Intelligence</strong> ! Votre compte a bien été créé.<br>
  Pour activer votre compte, confirmez votre adresse email en cliquant sur le bouton ci-dessous.
</p>
<div style="text-align:center; margin:32px 0;">
  <a href="{verification_link}" class="btn">✅ Activer mon compte</a>
</div>
<div class="note">
  ⏰ Ce lien est valable <strong>24 heures</strong>.<br>
  🔐 Après activation, un <strong>code OTP</strong> sera automatiquement envoyé
  à cette même adresse pour valider votre connexion au dashboard.
</div>
<p class="message" style="font-size:13px; color:#64748b;">
  Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :
</p>
<p class="link-fallback">{verification_link}</p>
<hr class="divider">
<p class="message" style="font-size:13px; color:#64748b;">
  Si vous n'avez pas créé de compte sur OCR Intelligence, vous pouvez ignorer cet email en toute sécurité.
</p>"""
    html = _base_html("Activez votre compte — OCR Intelligence", content)
    text = (
        f"Bonjour {user_name},\n\n"
        f"Bienvenue sur OCR Intelligence !\n\n"
        f"Cliquez sur ce lien pour activer votre compte (valable 24h) :\n{verification_link}\n\n"
        f"Après activation, un code OTP sera envoyé pour valider votre connexion.\n\n"
        f"Si vous n'avez pas créé de compte, ignorez cet email."
    )
    return html, text


def _otp_html(user_name: str, otp_code: str, expires_minutes: int) -> tuple[str, str]:
    """Generate HTML + plain text for OTP login email."""
    content = f"""
<p class="greeting">Bonjour <strong>{user_name}</strong> 👋</p>
<p class="message">
  Vous tentez de vous connecter à <strong>OCR Intelligence</strong>.<br>
  Voici votre code de vérification à usage unique :
</p>
<div class="otp-box">
  <div class="otp-code">{otp_code}</div>
  <div class="otp-expires">⏱ Expire dans <strong>{expires_minutes} minutes</strong></div>
</div>
<div class="note">
  🔒 Ce code est <strong>strictement personnel</strong>. Ne le partagez jamais.<br>
  Vous disposez de <strong>3 tentatives</strong> maximum pour saisir ce code correctement.
</div>
<hr class="divider">
<p class="message" style="font-size:13px; color:#64748b;">
  Si vous n'avez pas initié cette connexion, votre mot de passe est peut-être compromis.
  Changez-le immédiatement depuis la page de réinitialisation.
</p>"""
    html = _base_html("Votre code de connexion — OCR Intelligence", content)
    text = (
        f"Bonjour {user_name},\n\n"
        f"Votre code de connexion OCR Intelligence :\n\n"
        f"  {otp_code}\n\n"
        f"Ce code expire dans {expires_minutes} minutes.\n"
        f"Ne le partagez jamais.\n\n"
        f"Si vous n'avez pas demandé ce code, ignorez cet email."
    )
    return html, text


def _reset_html(user_name: str, reset_link: str) -> tuple[str, str]:
    """Generate HTML + plain text for password reset email."""
    content = f"""
<p class="greeting">Bonjour <strong>{user_name}</strong> 👋</p>
<p class="message">
  Nous avons reçu une demande de réinitialisation de mot de passe pour votre compte
  <strong>OCR Intelligence</strong>.
</p>
<div style="text-align:center; margin:32px 0;">
  <a href="{reset_link}" class="btn">🔑 Réinitialiser mon mot de passe</a>
</div>
<div class="note">
  ⏰ Ce lien est valable <strong>1 heure</strong> seulement. Passé ce délai,
  vous devrez faire une nouvelle demande.
</div>
<p class="message" style="font-size:13px; color:#64748b;">
  Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :
</p>
<p class="link-fallback">{reset_link}</p>
<hr class="divider">
<p class="message" style="font-size:13px; color:#64748b;">
  Si vous n'avez pas demandé de réinitialisation de mot de passe, ignorez cet email.
  Votre mot de passe reste inchangé.
</p>"""
    html = _base_html("Réinitialisation de mot de passe — OCR Intelligence", content)
    text = (
        f"Bonjour {user_name},\n\n"
        f"Cliquez sur ce lien pour réinitialiser votre mot de passe (valable 1h) :\n{reset_link}\n\n"
        f"Si vous n'avez pas fait cette demande, ignorez cet email."
    )
    return html, text


def _test_html(user_email: str, smtp_host: str) -> tuple[str, str]:
    """Generate HTML + plain text for SMTP test email."""
    now = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    content = f"""
<p class="greeting">Configuration SMTP validée ✅</p>
<p class="message">
  Cet email de test confirme que votre configuration SMTP fonctionne correctement.<br>
  Tous les emails de vérification et codes OTP seront désormais envoyés depuis votre serveur.
</p>
<div class="otp-box">
  <div style="font-size:16px; color:#10b981; font-weight:700;">✅ SMTP Opérationnel</div>
  <div class="otp-expires">Serveur : <strong>{smtp_host}</strong></div>
  <div class="otp-expires">Expéditeur : <strong>{user_email}</strong></div>
  <div class="otp-expires">Date du test : {now}</div>
</div>
<div class="note">
  🚀 Votre plateforme OCR Intelligence est maintenant configurée pour envoyer :<br>
  • Les emails d'activation de compte<br>
  • Les codes OTP de connexion<br>
  • Les emails de réinitialisation de mot de passe
</div>"""
    html = _base_html("Test SMTP réussi — OCR Intelligence", content)
    text = (
        f"Configuration SMTP validée !\n\n"
        f"Serveur : {smtp_host}\n"
        f"Expéditeur : {user_email}\n"
        f"Date : {now}\n\n"
        f"Votre OCR Intelligence peut maintenant envoyer des emails."
    )
    return html, text


def send_email_verification(
    to_email: str,
    verification_link: str,
    user_name: str = "Utilisateur",
) -> bool:
    """Send account activation email. Returns True only if SMTP succeeded."""
    subject = "✅ Activez votre compte OCR Intelligence"
    html_body, text_body = _verification_html(user_name, verification_link)

    sent = _send_smtp(to_email, subject, html_body, text_body)
    if not sent:
        _console_fallback(
            "EMAIL DE VÉRIFICATION (SMTP non disponible)",
            to_email,
            f"Lien d'activation : {verification_link}",
        )
        return False
    return True


def send_otp_email(
    to_email: str,
    otp_code: str,
    user_name: str = "Utilisateur",
    expires_minutes: int = OTP_EXPIRY_MINUTES,
) -> bool:
    """Send OTP code email. Returns True only if SMTP succeeded."""
    subject = f"🔐 Votre code de connexion : {otp_code}"
    html_body, text_body = _otp_html(user_name, otp_code, expires_minutes)

    sent = _send_smtp(to_email, subject, html_body, text_body)
    if not sent:
        _console_fallback(
            "CODE OTP (SMTP non disponible)",
            to_email,
            f"Code OTP : {otp_code}  |  Expire dans {expires_minutes} min",
        )
        return False
    return True


def send_password_reset_email(
    to_email: str,
    reset_link: str,
    user_name: str = "Utilisateur",
) -> bool:
    """Send password reset email. Returns True on success."""
    subject = "🔑 Réinitialisez votre mot de passe OCR Intelligence"
    html_body, text_body = _reset_html(user_name, reset_link)

    sent = _send_smtp(to_email, subject, html_body, text_body)
    if not sent:
        _console_fallback(
            "EMAIL RÉINITIALISATION MDP (SMTP non disponible)",
            to_email,
            f"Lien de réinitialisation : {reset_link}",
        )
        return True
    return True


EMAIL_PROVIDERS = _SMTP_PRESETS
