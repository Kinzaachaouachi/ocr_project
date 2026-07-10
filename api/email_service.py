import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple, Optional
from pathlib import Path


try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    print("⚠️ python-dotenv not installed. Environment variables must be set manually.")



SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT_ENV = os.getenv("SMTP_PORT", "")
SMTP_PORT = int(SMTP_PORT_ENV) if SMTP_PORT_ENV else 0
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "OCR Intelligence")


OTP_EXPIRY_MINUTES = 10


EMAIL_PROVIDERS = {
    "gmail": {
        "domains": ["gmail.com", "googlemail.com"],
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "name": "Gmail"
    },
    "outlook": {
        "domains": ["outlook.com", "outlook.fr", "outlook.de", "outlook.es", "hotmail.com", "hotmail.fr", "hotmail.de"],
        "smtp_host": "smtp-mail.outlook.com",
        "smtp_port": 587,
        "name": "Outlook/Hotmail"
    },
    "yahoo": {
        "domains": ["yahoo.com", "yahoo.fr", "yahoo.de", "yahoo.co.uk"],
        "smtp_host": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "name": "Yahoo"
    },
    "protonmail": {
        "domains": ["protonmail.com", "pm.me"],
        "smtp_host": "smtp.protonmail.com",
        "smtp_port": 587,
        "name": "ProtonMail"
    }
}


_DEV_MODE = not (SMTP_USER and SMTP_PASSWORD)  


def detect_email_provider(email: str) -> Tuple[Optional[str], dict]:

    email = email.lower().strip()
    

    if "@" not in email:
        return None, {}
    
    domain = email.split("@")[1]
    
   
    for provider_id, config in EMAIL_PROVIDERS.items():
        if domain in config["domains"]:
            return provider_id, config
    
    return None, {}


def get_smtp_config(email: str) -> Tuple[str, int, str]:

    if SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASSWORD:
        provider_id, config = detect_email_provider(email)
        provider_name = EMAIL_PROVIDERS.get(provider_id, {}).get("name", "Custom SMTP")
        print(f"[INFO] Configuration SMTP manuelle pour {provider_name}")
        return SMTP_HOST, SMTP_PORT, provider_name
    
    if SMTP_USER and SMTP_PASSWORD:
        provider_id, config = detect_email_provider(SMTP_USER)  
        
        if provider_id:
            provider_name = config["name"]
            smtp_host = config["smtp_host"]
            smtp_port = config["smtp_port"]
            print(f"[INFO] Envoi via {provider_name} ({smtp_host}:{smtp_port}) vers {email}")
            return smtp_host, smtp_port, provider_name
    
 
    print(f"[WARNING] Aucune configuration SMTP disponible")
    return "", 0, "Unknown"


def _build_otp_html(otp_code: str, user_name: str, expires_minutes: int = 10) -> str:
    digits = list(otp_code)
    digit_cells = "".join(
        f"""<td style="padding:4px;">
              <span style="display:inline-block;width:48px;height:56px;line-height:56px;
                           text-align:center;font-size:28px;font-weight:700;
                           background:#F0F4FF;border:2px solid #4F6EF7;
                           border-radius:10px;color:#1E3A8A;font-family:monospace;">
                {d}
              </span>
           </td>"""
        for d in digits
    )

    year = datetime.now().year
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Code de vérification OCR Intelligence</title>
</head>
<body style="margin:0;padding:0;background:#F3F4F6;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F3F4F6;padding:40px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:16px;overflow:hidden;
                      box-shadow:0 4px 24px rgba(0,0,0,0.08);max-width:96vw;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#4F6EF7 0%,#7C3AED 100%);
                        padding:32px 40px;text-align:center;">
              <div style="display:inline-flex;align-items:center;gap:10px;">
                <span style="background:rgba(255,255,255,0.2);border-radius:10px;
                             padding:8px 14px;font-size:20px;font-weight:800;
                             color:#fff;letter-spacing:1px;">AI</span>
                <span style="color:#fff;font-size:22px;font-weight:700;">OCR Intelligence</span>
              </div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 40px 32px;">
              <h2 style="margin:0 0 8px;color:#111827;font-size:22px;font-weight:700;">
                🔐 Vérification de connexion
              </h2>
              <p style="margin:0 0 24px;color:#6B7280;font-size:15px;line-height:1.6;">
                Bonjour {user_name},<br/>
                Voici votre code de vérification à usage unique.
                Il est valable <strong>{expires_minutes} minutes</strong>.
              </p>

              <!-- Code OTP -->
              <div style="text-align:center;margin:28px 0;">
                <!-- Code complet pour copier facilement -->
                <div style="background:#F9FAFB;border:2px dashed #D1D5DB;border-radius:12px;padding:20px;">
                  <p style="margin:0 0 8px;color:#6B7280;font-size:13px;font-weight:600;">VOTRE CODE DE VÉRIFICATION</p>
                  <p style="margin:0;font-size:36px;font-weight:800;color:#4F6EF7;letter-spacing:8px;font-family:monospace;">
                    {otp_code}
                  </p>
                  <p style="margin:8px 0 0;color:#9CA3AF;font-size:12px;">
                    Sélectionnez et copiez ce code (Ctrl+C)
                  </p>
                </div>
              </div>

              <!-- Alerte sécurité -->
              <div style="background:#FFF8F0;border-left:4px solid #F59E0B;
                          border-radius:8px;padding:14px 18px;margin:24px 0;">
                <p style="margin:0;color:#92400E;font-size:13px;line-height:1.5;">
                  ⚠️ <strong>Ne partagez jamais ce code.</strong>
                  OCR Intelligence ne vous demandera jamais votre code par téléphone ou email.
                  Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.
                </p>
              </div>

              <p style="margin:0;color:#9CA3AF;font-size:13px;">
                Ce code expire dans {expires_minutes} minutes et ne peut être utilisé qu'une seule fois.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#F9FAFB;padding:20px 40px;text-align:center;
                        border-top:1px solid #E5E7EB;">
              <p style="margin:0;color:#9CA3AF;font-size:12px;">
                © {year} OCR Intelligence — Tous droits réservés<br/>
                <span style="color:#D1D5DB;">Cet email a été envoyé automatiquement, ne pas y répondre.</span>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _build_otp_plain(otp_code: str, user_name: str, expires_minutes: int = 10) -> str:
    return (
        f"OCR Intelligence — Code de vérification\n"
        f"{'='*45}\n\n"
        f"Bonjour {user_name},\n\n"
        f"Votre code de vérification : {otp_code}\n\n"
        f"Ce code est valable {expires_minutes} minutes et ne peut être utilisé qu'une seule fois.\n\n"
        f"⚠️ Ne communiquez jamais ce code à personne.\n"
        f"Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n\n"
        f"— L'équipe OCR Intelligence"
    )


def send_otp_email(
    to_email: str,
    otp_code: str,
    user_name: str = "Utilisateur",
    expires_minutes: int = 10,
) -> bool:
    if _DEV_MODE:
        print("\n" + "=" * 60)
        print("[DEV MODE] Email OTP simule")
        print(f"   Destinataire : {to_email}")
        
       
        provider_id, _ = detect_email_provider(to_email)
        if provider_id:
            provider_config = EMAIL_PROVIDERS[provider_id]
            print(f"   Fournisseur  : {provider_config['name']}")
        
        print(f"   Code OTP     : {otp_code}")
        print(f"   Expire dans  : {expires_minutes} min")
        print("=" * 60 + "\n")
        return True

    try:
        
        smtp_host, smtp_port, provider_name = get_smtp_config(to_email)
        
        if not smtp_host or not smtp_port:
            print(f"[ERROR] Impossible de determiner la configuration SMTP pour {to_email}")
            return False
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{otp_code} - Votre code de connexion OCR Intelligence"
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
        msg["To"] = to_email

        plain = _build_otp_plain(otp_code, user_name, expires_minutes)
        html = _build_otp_html(otp_code, user_name, expires_minutes)

        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        context = ssl.create_default_context()

       
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())

        print(f"[SUCCESS] Email OTP envoye via {provider_name} a {to_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(
            f"[ERROR] Erreur authentification SMTP\n"
            f"   Provider: {provider_name if 'provider_name' in locals() else 'Unknown'}\n"
            f"   Verifiez SMTP_USER / SMTP_PASSWORD\n"
            f"   Pour Gmail: utilisez un 'Mot de passe d'application'\n"
            f"   Pour Outlook: activez l'authentification SMTP\n"
            f"   Detail: {str(e)}"
        )
        return False
    except smtplib.SMTPConnectError as e:
        smtp_host_info = f"{smtp_host}:{smtp_port}" if 'smtp_host' in locals() else "Unknown"
        print(f"[ERROR] Impossible de se connecter au serveur SMTP ({smtp_host_info}): {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"[ERROR] Erreur SMTP: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Erreur envoi email OTP: {e}")
        import traceback
        traceback.print_exc()
        return False
