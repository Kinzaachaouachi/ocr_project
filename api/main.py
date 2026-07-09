import concurrent.futures
import json
import os
import sys
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    Response,
)
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from . import model_workers
from .auth import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    authenticate_user,
    create_access_token,
    create_user_response,
    get_current_user,
)
from .confidence_analyzer import analyze_text_confidence, annotate_text_with_confidence
from .database import OCRHistory, User, create_user, get_db, get_user_by_email, init_db
from .language_detector import (
    detect_language_by_charset,
    detect_language_from_filename,
    detect_language_from_text,
    get_best_models_for_language,
    get_language_name,
)
from .model_matrix import MODEL_MATRIX, calculate_overall_score, get_model_info

app = FastAPI(
    title="API OCR - Extraction de Texte",
    description="API REST pour extraire du texte depuis des images et des PDF via PaddleOCR, Docling, EasyOCR ou TrOCR.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)




@app.on_event("startup")
async def startup_event():
    """Démarrage du serveur sans initialisation des modèles OCR"""
    try:
        init_db()
        print("✅ Base de données connectée et initialisée")
    except Exception as e:
        print(f" Erreur de connexion à la base de données: {e}")
        print("   L'API fonctionnera sans sauvegarde d'historique")

    
    print("🚀 Serveur OCR Intelligence démarré !")
    print("   Les modèles OCR seront chargés à la première utilisation")


@app.on_event("shutdown")
async def shutdown_event():
    print("🔄 Arrêt du serveur...")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


api_dir = Path(__file__).parent
static_dir = api_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


ALLOWED_EXTENSIONS = {
    "image": [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"],
    "pdf": [".pdf"],
    "txt": [".txt"],
    "docx": [".docx", ".doc"],
    "xlsx": [".xlsx", ".xls"],
}

MODELS_INFO = {
    "paddleocr": {
        "name": "PaddleOCR",
        "description": "Moteur OCR rapide et précis, supporte images et PDF (via PyMuPDF).",
        "supported_formats": ["image", "pdf"],
        "typical_accuracy": "~99%",
        "typical_speed": "~1s (inférence)",
    },
    "docling": {
        "name": "Docling",
        "description": "Analyse documentaire native (PDF, DOCX, XLSX, TXT, Images). Produit du Markdown structuré.",
        "supported_formats": ["image", "pdf", "txt", "docx", "xlsx"],
        "typical_accuracy": "~96%",
        "typical_speed": "~12s (inférence)",
    },
    "easyocr": {
        "name": "EasyOCR",
        "description": "OCR multi-langue basé sur PyTorch. Simple à utiliser, supporte images et PDF.",
        "supported_formats": ["image", "pdf"],
        "typical_accuracy": "~93%",
        "typical_speed": "~1.2s (inférence)",
    },
    "trocr": {
        "name": "TrOCR",
        "description": "Modèle Transformer Microsoft. Optimal pour lignes de texte isolées (manuscrit ou imprimé).",
        "supported_formats": ["image", "pdf"],
        "typical_accuracy": "~20% (multi-ligne sans segmentation)",
        "typical_speed": "~0.4s (inférence)",
    },
}


def detect_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for ftype, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return ftype
    return None


def run_worker(model: str, file_path: str, file_type: str) -> dict:


    try:
        # Utilisation directe des fonctions OCR
        if model in model_workers.INFERENCE_FUNCS:
            inference_func = model_workers.INFERENCE_FUNCS[model]
            return inference_func(file_path, file_type)
        else:
            return {
                "status": "error", 
                "error": f"Modèle '{model}' non supporté"
            }
    except Exception as e:
        print(f"❌ Erreur {model}: {str(e)}")
        return {
            "status": "error",
            "error": f"Erreur {model}: {str(e)}"
        }


def _run_worker_timed(model_id: str, file_path: str, file_type: str):
    t0 = time.time()
    result = run_worker(model_id, file_path, file_type)
    return model_id, result, round(time.time() - t0, 2)


def run_models_in_parallel(file_path: str, file_type: str, model_ids: list) -> list:
    results = []
    max_workers = max(1, len(model_ids))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_model = {
            executor.submit(_run_worker_timed, model_id, file_path, file_type): model_id
            for model_id in model_ids
        }
        for future in concurrent.futures.as_completed(future_to_model):
            model_id = future_to_model[future]
            try:
                results.append(future.result())
            except Exception as exc:
                results.append((model_id, {"status": "error", "error": str(exc)}, 0.0))
    return results


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
        "<text y='.9em' font-size='90'>📄</text></svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


INTER_FONT_URLS = {
    "Inter-Light.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuOKfMZg.ttf",
    "Inter-Regular.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfMZg.ttf",
    "Inter-Medium.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuI6fMZg.ttf",
    "Inter-SemiBold.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuGKYMZg.ttf",
    "Inter-Bold.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuFuYMZg.ttf",
    "Inter-ExtraBold.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuDyYMZg.ttf",
}


@app.get("/assets/fonts/{font_file}", include_in_schema=False)
async def inter_font_fallback(font_file: str):
    font_url = INTER_FONT_URLS.get(font_file)
    if not font_url:
        raise HTTPException(status_code=404, detail="Police introuvable")
    return RedirectResponse(url=font_url, status_code=307)


NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",
}


@app.get("/", response_class=HTMLResponse, tags=["Général"])
async def root(request: Request):
    return FileResponse(
        path=static_dir / "login.html", media_type="text/html", headers=NO_CACHE_HEADERS
    )


@app.get("/app", response_class=HTMLResponse, tags=["Général"])
async def app_interface():
    return FileResponse(
        path=static_dir / "index_multi.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@app.get("/register", response_class=HTMLResponse, tags=["Général"])
async def register_page():
    return FileResponse(
        path=static_dir / "register.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )

@app.post("/api/login", response_model=TokenResponse, tags=["Authentification"])
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=401, detail="Email ou mot de passe incorrect"
            )

        user.last_login = datetime.now()
        db.commit()

        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

        user_info = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 60 * 60,  
            user=user_info,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@app.post("/api/register", response_model=TokenResponse, tags=["Authentification"])
async def register(register_data: UserRegister, db: Session = Depends(get_db)):

    try:
        existing_user = get_user_by_email(db, register_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400, detail="Un compte avec cet email existe déjà"
            )

        user = create_user(
            db=db,
            email=register_data.email,
            password=register_data.password,
            first_name=register_data.first_name,
            last_name=register_data.last_name,
        )

    
        access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
        user_info = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": None,
        }

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=24 * 60 * 60,  
            user=user_info,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")


@app.get("/api/me", response_model=UserResponse, tags=["Authentification"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@app.post("/api/logout", tags=["Authentification"])
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Déconnexion réussie", "user": current_user.email}


@app.get("/health", tags=["Général"])
async def health_check(
    _current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    db_status = "disconnected"
    db_records = 0
    db_error = None

    try:
        db_records = db.query(OCRHistory).count()
        db_status = "connected"
        print(f" Base de données: {db_records} enregistrements")
    except Exception as e:
        db_status = "error"
        db_error = str(e)
        print(f"Erreur base de données: {e}")

    return {
        "status": "ok",
        "api": "OCR REST API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "models_available": list(MODELS_INFO.keys()),
        "database": {
            "status": db_status,
            "records_count": db_records,
            "error": db_error,
        },
    }


@app.get("/benchmark", response_class=HTMLResponse, tags=["Général"])
async def benchmark_report():

    benchmark_file = Path("benchmark_report.html")
    if benchmark_file.exists():
        with open(benchmark_file, "r", encoding="utf-8") as f:
            html_content = f.read()

        return HTMLResponse(content=html_content, status_code=200)

    else:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Benchmark - Non disponible</title>
                <style>
                    body { font-family: system-ui; display: flex; justify-content: center; align-items: center;
                           min-height: 100vh; background: #F8FAFC; margin: 0; }
                    .message { text-align: center; padding: 2rem; background: white; border-radius: 12px;
                              box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; }
                    h1 { color: #2563EB; margin-bottom: 1rem; }
                    p { color: #475569; margin-bottom: 1.5rem; }
                    code { background: #F1F5F9; padding: 0.25rem 0.5rem; border-radius: 4px;
                          font-family: monospace; }
                    a { color: #2563EB; text-decoration: none; font-weight: 600; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <div class="message">
                    <h1>📊 Rapport de Benchmark</h1>
                    <p>Le rapport de benchmark n'a pas encore été généré.</p>
                    <p>Pour générer le rapport, exécutez :</p>
                    <code>python run_all_benchmarks.py</code>
                    <p style="margin-top: 1.5rem;"><a href="/">← Retour à l'extraction</a></p>
                </div>
            </body>
            </html>
            """,
            status_code=200,
        )


@app.get("/benchmark/olm", response_class=HTMLResponse, tags=["Général"])
async def olm_benchmark_report():
    olm_file = Path("olm_benchmark_report.html")
    if olm_file.exists():
        with open(olm_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    else:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>olmOCR-Bench - Non disponible</title>
                <style>
                    body { font-family: system-ui; display: flex; justify-content: center; align-items: center;
                           min-height: 100vh; background: #F8FAFC; margin: 0; }
                    .message { text-align: center; padding: 2rem; background: white; border-radius: 12px;
                              box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; }
                    h1 { color: #2563EB; margin-bottom: 1rem; }
                    p { color: #475569; margin-bottom: 1.5rem; }
                    code { background: #F1F5F9; padding: 0.25rem 0.5rem; border-radius: 4px;
                          font-family: monospace; }
                    a { color: #2563EB; text-decoration: none; font-weight: 600; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <div class="message">
                    <h1>📊 olmOCR-Bench</h1>
                    <p>Le rapport olmOCR-Bench n'a pas encore été généré.</p>
                    <p>Pour générer le rapport, exécutez :</p>
                    <code>python generate_olm_report.py</code>
                    <p style="margin-top: 1.5rem;"><a href="/">← Retour à l'extraction</a></p>
                </div>
            </body>
            </html>
            """,
            status_code=200,
        )


@app.get("/models", tags=["Modèles"])
async def list_models(_current_user: User = Depends(get_current_user)):
    return {"models": MODELS_INFO, "total": len(MODELS_INFO)}


@app.get("/history", tags=["Historique"])
async def get_ocr_history(
    limit: int = 20,
    model: str = None,
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if limit > 100:
        limit = 100

    try:
        query = db.query(OCRHistory).filter(OCRHistory.user_id == current_user.id)
        if model:
            query = query.filter(OCRHistory.model_id == model)
        if status:
            query = query.filter(OCRHistory.status == status)

        records = query.order_by(OCRHistory.processed_at.desc()).limit(limit).all()
        history = []
        for record in records:
            history.append(
                {
                    "id": record.id,
                    "filename": record.filename,
                    "file_type": record.file_type,
                    "model_id": record.model_id,
                    "model_name": record.model_name,
                    "char_count": record.char_count,
                    "word_count": record.word_count,
                    "ocr_time_s": record.ocr_time_s,
                    "status": record.status,
                    "error_message": record.error_message,
                    "processed_at": record.processed_at.isoformat()
                    if record.processed_at
                    else None,
                    "client_ip": record.client_ip,
                    "text_preview": record.extracted_text[:200] + "..."
                    if record.extracted_text and len(record.extracted_text) > 200
                    else record.extracted_text,
                }
            )

        return {
            "status": "success",
            "count": len(history),
            "filters": {"model": model, "status": status, "limit": limit},
            "history": history,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur accès base de données: {str(e)}"
        )


@app.get("/history/stats", tags=["Historique"])
async def get_ocr_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    try:
        total_extractions = (
            db.query(OCRHistory).filter(OCRHistory.user_id == current_user.id).count()
        )
        successful_extractions = (
            db.query(OCRHistory)
            .filter(
                OCRHistory.user_id == current_user.id, OCRHistory.status == "success"
            )
            .count()
        )
        failed_extractions = (
            db.query(OCRHistory)
            .filter(OCRHistory.user_id == current_user.id, OCRHistory.status == "error")
            .count()
        )

        from sqlalchemy import func

        model_stats = (
            db.query(
                OCRHistory.model_id,
                func.count(OCRHistory.id).label("count"),
                func.avg(OCRHistory.ocr_time_s).label("avg_time"),
                func.sum(OCRHistory.char_count).label("total_chars"),
            )
            .filter(
                OCRHistory.user_id == current_user.id, OCRHistory.status == "success"
            )
            .group_by(OCRHistory.model_id)
            .all()
        )

        file_type_stats = (
            db.query(OCRHistory.file_type, func.count(OCRHistory.id).label("count"))
            .filter(OCRHistory.user_id == current_user.id)
            .group_by(OCRHistory.file_type)
            .all()
        )

        recent = (
            db.query(OCRHistory)
            .filter(OCRHistory.user_id == current_user.id)
            .order_by(OCRHistory.processed_at.desc())
            .limit(5)
            .all()
        )
        recent_list = [
            {
                "filename": r.filename,
                "model": r.model_id,
                "status": r.status,
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
            }
            for r in recent
        ]

        return {
            "status": "success",
            "global_stats": {
                "total_extractions": total_extractions,
                "successful_extractions": successful_extractions,
                "failed_extractions": failed_extractions,
                "success_rate": round(
                    (successful_extractions / total_extractions * 100), 2
                )
                if total_extractions > 0
                else 0,
            },
            "model_stats": [
                {
                    "model_id": stat.model_id,
                    "extractions_count": stat.count,
                    "avg_processing_time_s": round(float(stat.avg_time or 0), 2),
                    "total_characters_processed": stat.total_chars or 0,
                }
                for stat in model_stats
            ],
            "file_type_stats": [
                {"file_type": stat.file_type, "count": stat.count}
                for stat in file_type_stats
            ],
            "recent_extractions": recent_list,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur calcul statistiques: {str(e)}"
        )


@app.post("/extract", tags=["Extraction OCR"])
async def extract_text(
    file: UploadFile = File(
        ..., description="Fichier à traiter (image PNG/JPG, PDF, TXT, DOCX, ou XLSX)"
    ),
    model: str = Form(
        ..., description="Modèle OCR à utiliser : paddleocr | docling | easyocr | trocr"
    ),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if model not in MODELS_INFO:
        raise HTTPException(
            status_code=400,
            detail=f"Modèle inconnu : '{model}'. Modèles disponibles : {list(MODELS_INFO.keys())}",
        )

    file_type = detect_file_type(file.filename)
    if file_type is None:
        raise HTTPException(
            status_code=400,
            detail=f"Extension de fichier non supportée : '{Path(file.filename).suffix}'. "
            f"Extensions acceptées : .png, .jpg, .jpeg, .bmp, .tiff, .webp, .pdf, .txt, .docx, .doc, .xlsx, .xls",
        )

    supported = MODELS_INFO[model]["supported_formats"]
    if file_type not in supported:
        raise HTTPException(
            status_code=422,
            detail=f"Le modèle '{model}' ne supporte pas le format '{file_type}'. "
            f"Formats supportés par ce modèle : {supported}",
        )

    client_ip = request.client.host if request else "unknown"
    suffix = Path(file.filename).suffix.lower()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        t_start = time.time()
        result = await run_in_threadpool(run_worker, model, tmp_path, file_type)
        wall_time = round(time.time() - t_start, 2)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    if result.get("status") == "error":
        try:
            ocr_entry = OCRHistory(
                user_id=current_user.id,
                filename=file.filename,
                file_type=file_type,
                model_id=model,
                model_name=MODELS_INFO[model]["name"],
                extracted_text=None,
                char_count=0,
                word_count=0,
                ocr_time_s=0,
                status="error",
                error_message=result.get("error", "Erreur inconnue du worker OCR")[
                    :65535
                ],
                processed_at=datetime.now(),
                client_ip=client_ip,
            )
            db.add(ocr_entry)
            db.commit()
            print(f"✓ Sauvegardé échec DB: {model} - {file.filename}")
        except Exception as db_error:
            print(f"⚠ Erreur DB échec: {db_error}")
            db.rollback()

        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Erreur inconnue du worker OCR."),
        )

    if result.get("status") == "unsupported":
        try:
            ocr_entry = OCRHistory(
                user_id=current_user.id,
                filename=file.filename,
                file_type=file_type,
                model_id=model,
                model_name=MODELS_INFO[model]["name"],
                extracted_text=None,
                char_count=0,
                word_count=0,
                ocr_time_s=0,
                status="unsupported",
                error_message=result.get("reason", "Format non supporté")[:65535],
                processed_at=datetime.now(),
                client_ip=client_ip,
            )
            db.add(ocr_entry)
            db.commit()
            print(f" Sauvegardé format non supporté DB: {model} - {file.filename}")
        except Exception as db_error:
            print(f" Erreur DB format non supporté: {db_error}")
            db.rollback()

        raise HTTPException(
            status_code=422, detail=result.get("reason", "Format non supporté.")
        )

    text = result.get("text", "")
    char_count = len(text)
    word_count = len(text.split())

    try:
        ocr_entry = OCRHistory(
            user_id=current_user.id,
            filename=file.filename,
            file_type=file_type,
            model_id=model,
            model_name=MODELS_INFO[model]["name"],
            extracted_text=text[:65535],  # Limite MySQL TEXT
            char_count=char_count,
            word_count=word_count,
            ocr_time_s=result.get("ocr_time", 0),
            status="success",
            error_message=None,
            processed_at=datetime.now(),
            client_ip=client_ip,
        )
        db.add(ocr_entry)
        db.commit()
        print(f" Sauvegardé succès DB: {model} - {file.filename}")
    except Exception as db_error:
        print(f"Erreur DB succès: {db_error}")
        db.rollback()

    return {
        "status": "success",
        "model": MODELS_INFO[model]["name"],
        "model_id": model,
        "file": file.filename,
        "file_type": file_type,
        "text": text,
        "char_count": char_count,
        "word_count": word_count,
        "timing": {
            "init_time_s": result.get("init_time", 0),
            "ocr_time_s": result.get("ocr_time", 0),
            "total_model_time_s": result.get("total_time", 0),
            "wall_time_s": wall_time,
        },
        "processed_at": datetime.now().isoformat(),
    }


@app.post("/extract-all", tags=["Extraction OCR"])
async def extract_all_models(
    file: UploadFile = File(..., description="Fichier à traiter avec tous les modèles"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    file_type = detect_file_type(file.filename)
    if file_type is None:
        raise HTTPException(
            status_code=400,
            detail=f"Extension de fichier non supportée : '{Path(file.filename).suffix}'",
        )

    suffix = Path(file.filename).suffix.lower()
    tmp_path = None
    file_content = None

    client_ip = request.client.host if request else "unknown"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file_content = await file.read()
            tmp.write(file_content)
            tmp_path = tmp.name

        detected_lang_from_filename = detect_language_from_filename(file.filename)
        available_models = []
        for model_id, model_info in MODELS_INFO.items():
            if file_type in model_info["supported_formats"]:
                available_models.append(model_id)

        if not available_models:
            raise HTTPException(
                status_code=422,
                detail=f"Aucun modèle ne supporte le format '{file_type}'",
            )

        
        results = []
        overall_start = time.time()
        detected_language = None
        detected_language_confidence = 0.0

        futures = await run_in_threadpool(
            run_models_in_parallel, tmp_path, file_type, available_models
        )

        for model_id, result, wall_time in futures:
            try:
                if result.get("status") == "success":
                    text = result.get("text", "")
                    word_confidence_data = result.get("word_confidence", [])

                    if text and len(text.strip()) > 20:
                        try:
                            lang_code, lang_confidence = detect_language_from_text(text)
                            if detected_lang_from_filename:
                                detected_language = detected_lang_from_filename
                                detected_language_confidence = 0.95
                            elif lang_confidence > detected_language_confidence:
                                detected_language = lang_code
                                detected_language_confidence = lang_confidence
                        except Exception:
                            if not detected_language:
                                detected_language, detected_language_confidence = (
                                    detect_language_by_charset(text)
                                )

                    char_count = len(text)
                    word_count = len(text.split())

                    confidence_stats = analyze_text_confidence(word_confidence_data)

                    model_matrix_score = calculate_overall_score(model_id)

                    results.append(
                        {
                            "model_id": model_id,
                            "model_name": MODELS_INFO[model_id]["name"],
                            "status": "success",
                            "text": text,
                            "word_confidence": word_confidence_data,
                            "confidence_stats": confidence_stats,
                            "char_count": char_count,
                            "word_count": word_count,
                            "timing": {
                                "init_time_s": result.get("init_time", 0),
                                "ocr_time_s": result.get("ocr_time", 0),
                                "total_time_s": result.get("total_time", 0),
                                "wall_time_s": wall_time,
                            },
                            "quality_score": 0,  # Calculé après la boucle (scoring relatif)
                            "model_score": model_matrix_score,
                            "language_support": detected_language
                            in MODEL_MATRIX.get(model_id, {}).get("languages", []),
                        }
                    )

                    try:
                        ocr_entry = OCRHistory(
                            user_id=current_user.id,
                            filename=file.filename,
                            file_type=file_type,
                            model_id=model_id,
                            model_name=MODELS_INFO[model_id]["name"],
                            extracted_text=text[:65535],  # Limite MySQL TEXT
                            char_count=char_count,
                            word_count=word_count,
                            ocr_time_s=result.get("ocr_time", 0),
                            status="success",
                            error_message=None,
                            processed_at=datetime.now(),
                            client_ip=client_ip,
                        )
                        db.add(ocr_entry)
                        db.commit()
                        print(f"✓ Sauvegardé en DB: {model_id} - {file.filename}")
                    except Exception as db_error:
                        print(f"⚠ Erreur DB pour {model_id}: {db_error}")
                        db.rollback()

                else:
                    results.append(
                        {
                            "model_id": model_id,
                            "model_name": MODELS_INFO[model_id]["name"],
                            "status": "error",
                            "error": result.get("error", "Erreur inconnue"),
                            "quality_score": 0,
                        }
                    )

                    try:
                        ocr_entry = OCRHistory(
                            user_id=current_user.id,
                            filename=file.filename,
                            file_type=file_type,
                            model_id=model_id,
                            model_name=MODELS_INFO[model_id]["name"],
                            extracted_text=None,
                            char_count=0,
                            word_count=0,
                            ocr_time_s=0,
                            status="error",
                            error_message=result.get("error", "Erreur inconnue")[
                                :65535
                            ],
                            processed_at=datetime.now(),
                            client_ip=client_ip,
                        )
                        db.add(ocr_entry)
                        db.commit()
                        print(f"✓ Sauvegardé échec DB: {model_id} - {file.filename}")
                    except Exception as db_error:
                        print(f"⚠ Erreur DB échec pour {model_id}: {db_error}")
                        db.rollback()

            except Exception as e:
                results.append(
                    {
                        "model_id": model_id,
                        "model_name": MODELS_INFO[model_id]["name"],
                        "status": "error",
                        "error": str(e),
                        "quality_score": 0,
                    }
                )

                try:
                    ocr_entry = OCRHistory(
                        user_id=current_user.id,
                        filename=file.filename,
                        file_type=file_type,
                        model_id=model_id,
                        model_name=MODELS_INFO[model_id]["name"],
                        extracted_text=None,
                        char_count=0,
                        word_count=0,
                        ocr_time_s=0,
                        status="error",
                        error_message=str(e)[:65535],
                        processed_at=datetime.now(),
                        client_ip=client_ip,
                    )
                    db.add(ocr_entry)
                    db.commit()
                    print(f" Sauvegardé exception DB: {model_id} - {file.filename}")
                except Exception as db_error:
                    print(f" Erreur DB exception pour {model_id}: {db_error}")
                    db.rollback()

      
        successful_results = [r for r in results if r["status"] == "success"]
        if successful_results:
            max_char_count = max(r["char_count"] for r in successful_results) or 1
            min_ocr_time = min(r["timing"]["ocr_time_s"] for r in successful_results) or 0.01

            for r in successful_results:
                
                avg_conf = r.get("confidence_stats", {}).get("avg_confidence", 0.75)
                confidence_score = avg_conf * 100

                
                text_completeness = (r["char_count"] / max_char_count) * 100

                
                ocr_time = r["timing"]["ocr_time_s"] or 0.01
                speed_score = min(100, (min_ocr_time / ocr_time) * 100)

                
                language_score = 100 if r.get("language_support") else 0

                
                static_score = r.get("model_score", 0)

                
                quality_score = (
                    confidence_score * 0.30     
                    + text_completeness * 0.25   
                    + static_score * 0.20        
                    + language_score * 0.15     
                    + speed_score * 0.10          
                )

                r["quality_score"] = round(quality_score, 1)

        results.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        overall_time = round(time.time() - overall_start, 2)

        best_result = next((r for r in results if r["status"] == "success"), None)

        if not detected_language:
            detected_language = "fr"
            detected_language_confidence = 0.5

        recommended_models = get_best_models_for_language(detected_language)

        return {
            "status": "success",
            "file": file.filename,
            "file_type": file_type,
            "detected_language": {
                "code": detected_language,
                "name": get_language_name(detected_language),
                "confidence": round(detected_language_confidence, 2),
                "detection_method": "filename"
                if detected_lang_from_filename
                else "text_analysis",
            },
            "recommended_models": recommended_models,
            "total_models_tested": len(results),
            "successful_extractions": sum(
                1 for r in results if r["status"] == "success"
            ),
            "best_model": best_result["model_id"] if best_result else None,
            "best_model_name": best_result["model_name"] if best_result else None,
            "total_processing_time_s": overall_time,
            "results": results,
            "processed_at": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/translate", tags=["Traduction"])
async def translate_file_or_text(
    target_lang: str = Form(
        ...,
        description="Langue cible : en, es, de, it, ar, fr, pt, ja, zh, ru, ko, tr, nl, pl, vi",
    ),
    source_lang: str = Form(
        "auto",
        description="Langue source : auto|fr|en|es|de|it|ar|pt|ja|zh|ru|ko|tr|nl|pl|vi",
    ),
    file: UploadFile = File(
        None, description="Fichier à traduire (Image/PDF/TXT/DOCX/XLSX)"
    ),
    text: str = Form(None, description="Texte à traduire"),
    model: str = Form(
        "auto", description="Modèle OCR : auto|paddleocr|docling|easyocr|trocr"
    ),
    _current_user: User = Depends(get_current_user),
):

    import urllib.parse
    import urllib.request

    allowed_langs = {
        "en",
        "es",
        "de",
        "it",
        "ar",
        "fr",
        "pt",
        "ja",
        "zh",
        "ru",
        "ko",
        "tr",
        "nl",
        "pl",
        "vi",
    }
    if target_lang not in allowed_langs:
        raise HTTPException(
            status_code=400,
            detail=f"Langue non supportée. Langues disponibles: {', '.join(sorted(allowed_langs))}",
        )
    if source_lang != "auto" and source_lang not in allowed_langs:
        raise HTTPException(
            status_code=400,
            detail=f"Langue source non supportée. Langues disponibles: auto, {', '.join(sorted(allowed_langs))}",
        )

    extracted_text = ""
    file_name = ""
    file_type_used = "text"
    model_used = "direct"
    source_lang_used = source_lang
    source_confidence = None

    if file:
        file_name = file.filename
        file_type = detect_file_type(file_name)

        if file_type is None:
            raise HTTPException(
                status_code=400,
                detail=f"Type de fichier non supporté. Acceptés: .png, .jpg, .jpeg, .bmp, .tiff, .webp, .pdf, .txt, .docx, .doc, .xlsx, .xls",
            )

        selected_model = model
        if selected_model == "auto" or selected_model not in MODELS_INFO:
            if file_type == "image":
                selected_model = "paddleocr"
            elif file_type == "pdf":
                selected_model = "docling"
            elif file_type == "txt":
                selected_model = "docling"
            elif file_type == "docx":
                selected_model = "docling"
            elif file_type == "xlsx":
                selected_model = "docling"
            else:
                selected_model = "paddleocr" 

        if selected_model not in MODELS_INFO:
            raise HTTPException(
                status_code=400, detail=f"Modèle inconnu: {selected_model}"
            )

        supported = MODELS_INFO[selected_model]["supported_formats"]
        if file_type not in supported:
            raise HTTPException(
                status_code=422,
                detail=f"Modèle '{selected_model}' ne supporte pas '{file_type}'. Supportés: {supported}",
            )

        suffix = Path(file_name).suffix.lower()
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name

            result = await run_in_threadpool(
                run_worker, selected_model, tmp_path, file_type
            )

            if result.get("status") == "error":
                raise HTTPException(
                    status_code=500, detail=f"Erreur extraction: {result.get('error')}"
                )

            extracted_text = result.get("text", "")
            file_type_used = file_type
            model_used = selected_model

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    elif text:
        extracted_text = text
        file_type_used = "text"
        model_used = "direct"

    else:
        raise HTTPException(
            status_code=400, detail="Fournir soit un fichier, soit du texte à traduire"
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400, detail="Aucun texte à traduire (fichier ou texte vide)"
        )

    try:
        text_to_translate = extracted_text[:100000]
        encoded_text = urllib.parse.quote(text_to_translate)

        if source_lang_used == "auto":
            detected_lang, detected_score = detect_language_from_text(extracted_text)
            if detected_lang in allowed_langs:
                source_lang_used = detected_lang
                source_confidence = detected_score
            else:
                source_lang_used = "en"
                source_confidence = 0.5

        url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair={source_lang_used}|{target_lang}&de=kinza.achaouachi@example.com"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

        with urllib.request.urlopen(req, timeout=15) as response:
            translation_data = json.loads(response.read().decode("utf-8"))

        response_status = translation_data.get("responseStatus")
        response_data = translation_data.get("responseData", {})
        translated = response_data.get("translatedText", "")

        if response_status == 200 or (response_status == 403 and translated):
            if "MYMEMORY WARNING" in translated or "QUOTA" in translated.upper():
                return {
                    "status": "quota_exceeded",
                    "original_text": extracted_text[:300],
                    "translated_text": extracted_text[:300],
                    "warning": "Quota API dépassé. Texte original retourné.",
                    "source_lang": source_lang_used,
                    "source_confidence": source_confidence,
                    "target_lang": target_lang,
                    "file_name": file_name if file_name else None,
                    "file_type": file_type_used,
                    "model_used": model_used,
                    "char_count": len(extracted_text),
                    "word_count": len(extracted_text.split()),
                    "translated_at": datetime.now().isoformat(),
                }

            return {
                "status": "success",
                "original_text": extracted_text[:300],
                "translated_text": translated,
                "source_lang": source_lang_used,
                "source_confidence": source_confidence,
                "target_lang": target_lang,
                "file_name": file_name if file_name else None,
                "file_type": file_type_used,
                "model_used": model_used,
                "char_count": len(extracted_text),
                "word_count": len(extracted_text.split()),
                "translated_at": datetime.now().isoformat(),
            }
        else:
            error_msg = translation_data.get("responseDetails", "Erreur inconnue")
            raise HTTPException(
                status_code=503,
                detail=f"API MyMemory: {error_msg}. Essayez plus tard ou avec un texte plus court.",
            )

    except urllib.error.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Erreur HTTP {e.code}: API traduction temporairement indisponible. Réessayez dans quelques secondes.",
        )
    except urllib.error.URLError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Connexion impossible à l'API de traduction: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur traduction: {str(e)}. Vérifiez votre connexion Internet.",
        )
