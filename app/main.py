from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from .config.settings import STATIC_DIR, UPLOADS_DIR
from .models.database import init_db
from .routers import (
    auth,
    dashboard,
    history,
    local_benchmark,
    ocr,
    olm_report,
    pages,
    users,
)

app = FastAPI(
    title="OCR Intelligence API",
    description=(
        "API REST complète pour l'extraction de texte via PaddleOCR, Docling, EasyOCR et TrOCR. "
        "Authentification 2FA par email (vérification compte + OTP connexion)."
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def startup_event():
    """Initialize database + apply SMTP config from .env."""

    try:
        from dotenv import load_dotenv
        from .config.settings import (
            BASE_DIR,
            SMTP_HOST,
            SMTP_PORT,
            SMTP_USER,
            SMTP_PASSWORD,
            SMTP_FROM,
            SMTP_FROM_NAME,
        )
        from .services.email_service import set_smtp_config, _normalize_smtp_password

        load_dotenv(BASE_DIR / ".env", override=True)
        import os

        host = os.getenv("SMTP_HOST", SMTP_HOST)
        port = int(os.getenv("SMTP_PORT") or SMTP_PORT or 587)
        user = os.getenv("SMTP_USER", SMTP_USER)
        password = _normalize_smtp_password(
            os.getenv("SMTP_PASSWORD", SMTP_PASSWORD) or ""
        )
        from_email = os.getenv("SMTP_FROM", SMTP_FROM) or user
        from_name = os.getenv("SMTP_FROM_NAME", SMTP_FROM_NAME) or "OCR Intelligence"

        if host and user and password:
            set_smtp_config(
                {
                    "host": host,
                    "port": port,
                    "user": user,
                    "password": password,
                    "from_email": from_email,
                    "from_name": from_name,
                    "use_ssl": port == 465,
                }
            )
            print(
                f"📧 SMTP prêt : {user} via {host}:{port} ({'SSL' if port == 465 else 'STARTTLS'})"
            )
        else:
            print("⚠️  SMTP incomplet dans .env — les emails iront en console")
    except Exception as e:
        print(f"⚠️  Impossible de charger SMTP : {e}")

    ok = init_db()
    if ok:
        print("🚀 OCR Intelligence v3.0.0 démarré")
        print("   Flux auth : 1) email vérification → 2) OTP → 3) dashboard")
        print("   Préchargement des modèles OCR en arrière-plan...")

        def _warmup_models():
            try:
                from .utils.model_workers import warmup_all_models

                warmup_all_models()
                print("✅ Modèles OCR prêts — extractions parallèles accélérées")
            except Exception as e:
                print(f"⚠️ Warmup modèles OCR: {e}")

        import threading

        threading.Thread(target=_warmup_models, daemon=True, name="ocr-warmup").start()
    else:
        print(
            "⚠️  Base de données non disponible — certaines fonctionnalités seront limitées"
        )


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Arrêt du serveur OCR Intelligence")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.middleware("http")
async def protect_app_pages(request: Request, call_next):
    path = request.url.path
    if path.startswith("/app"):
        accept = (request.headers.get("accept") or "").lower()
        is_html_nav = "text/html" in accept or accept == "*/*" or not accept
        if is_html_nav and not path.startswith("/api"):
            if not request.cookies.get("ocr_auth"):
                from fastapi.responses import RedirectResponse

                return RedirectResponse(url="/", status_code=303)
    response = await call_next(request)
    if path.startswith("/app") or path in ("/", "/register", "/reset-password", "/verify-email"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if UPLOADS_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(ocr.router)
app.include_router(history.router)
app.include_router(dashboard.router)
app.include_router(olm_report.router)
app.include_router(local_benchmark.router)


@app.get("/health", tags=["Général"])
async def health_check():
    """Full health check: DB connection, record counts, version."""
    from datetime import datetime
    from .models.database import SessionLocal
    from .models.ocr_history import OCRHistory

    db_status = "disconnected"
    db_records = 0
    db_error = None

    try:
        if SessionLocal:
            db = SessionLocal()
            db_records = db.query(OCRHistory).count()
            db_status = "connected"
            db.close()
    except Exception as e:
        db_status = "error"
        db_error = str(e)

    return {
        "status": "ok",
        "api": "OCR Intelligence API",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": {
            "status": db_status,
            "records_count": db_records,
            "error": db_error,
        },
    }


@app.get("/models", tags=["Modèles"])
async def list_models():
    """List available OCR models."""
    from .utils.model_matrix import MODELS_INFO

    return {"models": MODELS_INFO, "total": len(MODELS_INFO)}
