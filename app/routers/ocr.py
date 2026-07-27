import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from ..config.settings import UPLOADS_DIR
from ..models.database import get_db
from ..models.ocr_history import OCRHistory
from ..models.user import User
from ..services.auth_service import get_current_user
from ..services.ocr_service import (
    run_models_in_parallel,
    run_worker,
    save_ocr_result,
    calculate_benchmark_metrics,
)
from ..services.extraction_jobs import (
    get_job,
    get_active_job_for_user,
    start_extract_all_job,
    process_extract_all_file,
)
from ..utils.confidence_analyzer import (
    analyze_text_confidence,
    refine_word_confidence_list,
)
from ..utils.file_helpers import detect_file_type, MODELS_INFO
from ..utils.language_detector import (
    detect_language_by_charset,
    detect_language_from_filename,
    detect_language_from_text,
    get_best_models_for_language,
    get_language_name,
)
from ..utils.model_matrix import MODEL_MATRIX, calculate_overall_score

router = APIRouter(prefix="/api", tags=["Extraction OCR"])


@router.get("/models", tags=["Modèles"])
async def list_models(_current_user: User = Depends(get_current_user)):
    return {"models": MODELS_INFO, "total": len(MODELS_INFO)}


@router.post("/extract")
async def extract_text(
    file: UploadFile = File(..., description="Fichier à traiter"),
    model: str = Form(
        ..., description="Modèle OCR : paddleocr | docling | easyocr | trocr"
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
            detail=f"Extension non supportée : '{Path(file.filename).suffix}'",
        )

    supported = MODELS_INFO[model]["supported_formats"]
    if file_type not in supported:
        raise HTTPException(
            status_code=422,
            detail=f"Le modèle '{model}' ne supporte pas le format '{file_type}'.",
        )

    client_ip = request.client.host if request else "unknown"
    suffix = Path(file.filename).suffix.lower()
    tmp_path = None
    uploaded_file_path = None
    file_url = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_without_ext = Path(file.filename).stem
            uploaded_filename = f"{filename_without_ext}_{timestamp}{suffix}"
            uploaded_file_path = UPLOADS_DIR / uploaded_filename

            with open(tmp_path, "rb") as src:
                with open(uploaded_file_path, "wb") as dst:
                    dst.write(src.read())

            file_url = f"/uploads/{uploaded_filename}"
        except Exception as e:
            print(f"Warning: Could not save uploaded file: {e}")

        t_start = time.time()
        result = await run_in_threadpool(run_worker, model, tmp_path, file_type)
        wall_time = round(time.time() - t_start, 2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    save_ocr_result(
        db,
        current_user,
        file.filename,
        file_type,
        file_url,
        model,
        result,
        wall_time,
        client_ip,
    )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=500, detail=result.get("error", "Erreur inconnue")
        )
    if result.get("status") == "unsupported":
        raise HTTPException(
            status_code=422, detail=result.get("reason", "Format non supporté")
        )

    text = result.get("text", "")
    return {
        "status": "success",
        "model": MODELS_INFO[model]["name"],
        "model_id": model,
        "file": file.filename,
        "file_type": file_type,
        "text": text,
        "char_count": len(text),
        "word_count": len(text.split()),
        "timing": {
            "init_time_s": result.get("init_time", 0),
            "ocr_time_s": result.get("ocr_time", 0),
            "total_model_time_s": result.get("total_time", 0),
            "wall_time_s": wall_time,
        },
        "processed_at": datetime.now().isoformat(),
    }


@router.post("/extract-all")
async def extract_all_models(
    file: UploadFile = File(..., description="Fichier à traiter avec tous les modèles"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lancement asynchrone : le job continue même si l'utilisateur change de page."""
    file_type = detect_file_type(file.filename)
    if file_type is None:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non supportée : '{Path(file.filename).suffix}'",
        )

    available_models = [
        mid
        for mid, minfo in MODELS_INFO.items()
        if file_type in minfo["supported_formats"]
    ]
    if not available_models:
        raise HTTPException(
            status_code=422,
            detail=f"Aucun modèle ne supporte le format '{file_type}'",
        )

    suffix = Path(file.filename).suffix.lower()
    tmp_path = None
    file_url = None
    client_ip = request.client.host if request else "unknown"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file_content = await file.read()
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_without_ext = Path(file.filename).stem
            uploaded_filename = f"{filename_without_ext}_{timestamp}{suffix}"
            uploaded_file_path = UPLOADS_DIR / uploaded_filename

            with open(tmp_path, "rb") as src:
                with open(uploaded_file_path, "wb") as dst:
                    dst.write(src.read())

            file_url = f"/uploads/{uploaded_filename}"
        except Exception as e:
            print(f"Warning: Could not save uploaded file: {e}")

        job_id = start_extract_all_job(
            tmp_path=tmp_path,
            filename=file.filename,
            file_type=file_type,
            file_url=file_url,
            user_id=current_user.id,
            client_ip=client_ip,
        )
        # tmp_path ownership transferred to the job worker (deleted there)
        tmp_path = None

        return {
            "status": "accepted",
            "async": True,
            "job_id": job_id,
            "file": file.filename,
            "file_type": file_type,
            "file_path": file_url,
            "message": "Extraction démarrée en arrière-plan. Vous pouvez changer de page.",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/extract-all/jobs/active")
async def get_active_extract_job(
    current_user: User = Depends(get_current_user),
):
    """Job en cours (ou tout juste terminé) pour l'utilisateur connecté."""
    job = get_active_job_for_user(current_user.id)
    if not job:
        return {"status": "idle", "job": None}

    payload = {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job.get("progress", 0),
        "message": job.get("message"),
        "filename": job.get("filename"),
        "file_type": job.get("file_type"),
        "file_path": job.get("file_path"),
        "error": job.get("error"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
    }
    if job.get("status") == "completed" and job.get("result"):
        payload["result"] = job["result"]
    return {"status": job["status"], "job": payload}


@router.get("/extract-all/jobs/{job_id}")
async def get_extract_all_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job introuvable")
    if job.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")

    payload = {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job.get("progress", 0),
        "message": job.get("message"),
        "filename": job.get("filename"),
        "file_type": job.get("file_type"),
        "file_path": job.get("file_path"),
        "error": job.get("error"),
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
    }
    if job.get("status") == "completed" and job.get("result"):
        payload["result"] = job["result"]
    return payload


@router.post("/extract-all/sync")
async def extract_all_models_sync(
    file: UploadFile = File(..., description="Fichier à traiter (mode synchrone)"),
    request: Request = None,
    current_user: User = Depends(get_current_user),
):
    """Ancien mode bloquant — conservé pour compatibilité / tests."""
    file_type = detect_file_type(file.filename)
    if file_type is None:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non supportée : '{Path(file.filename).suffix}'",
        )

    suffix = Path(file.filename).suffix.lower()
    tmp_path = None
    file_url = None
    client_ip = request.client.host if request else "unknown"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file_content = await file.read()
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            uploaded_filename = (
                f"{Path(file.filename).stem}_{timestamp}{suffix}"
            )
            uploaded_file_path = UPLOADS_DIR / uploaded_filename
            with open(tmp_path, "rb") as src, open(uploaded_file_path, "wb") as dst:
                dst.write(src.read())
            file_url = f"/uploads/{uploaded_filename}"
        except Exception as e:
            print(f"Warning: Could not save uploaded file: {e}")

        return await run_in_threadpool(
            lambda: process_extract_all_file(
                tmp_path=tmp_path,
                filename=file.filename,
                file_type=file_type,
                file_url=file_url,
                user_id=current_user.id,
                client_ip=client_ip,
                job_id=None,
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/translate", tags=["Traduction"])
async def translate_file_or_text(
    target_lang: str = Form(..., description="Langue cible"),
    source_lang: str = Form("auto", description="Langue source"),
    file: UploadFile = File(None, description="Fichier à traduire"),
    text: str = Form(None, description="Texte à traduire"),
    model: str = Form("auto", description="Modèle OCR"),
    _current_user: User = Depends(get_current_user),
):
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
            detail=f"Langue non supportée. Disponibles: {', '.join(sorted(allowed_langs))}",
        )
    if source_lang != "auto" and source_lang not in allowed_langs:
        raise HTTPException(status_code=400, detail=f"Langue source non supportée.")

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
            raise HTTPException(status_code=400, detail="Type de fichier non supporté.")

        selected_model = model
        if selected_model == "auto" or selected_model not in MODELS_INFO:
            model_map = {
                "image": "paddleocr",
                "pdf": "docling",
                "txt": "docling",
                "docx": "docling",
                "xlsx": "docling",
            }
            selected_model = model_map.get(file_type, "paddleocr")

        supported = MODELS_INFO[selected_model]["supported_formats"]
        if file_type not in supported:
            raise HTTPException(
                status_code=422,
                detail=f"Modèle '{selected_model}' ne supporte pas '{file_type}'.",
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
    else:
        raise HTTPException(
            status_code=400, detail="Fournir soit un fichier, soit du texte à traduire"
        )

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Aucun texte à traduire")

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
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

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
                    "warning": "Quota API dépassé.",
                    "source_lang": source_lang_used,
                    "target_lang": target_lang,
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
            raise HTTPException(status_code=503, detail="API traduction indisponible.")
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=503, detail=f"Erreur HTTP {e.code}")
    except urllib.error.URLError as e:
        raise HTTPException(status_code=503, detail=f"Connexion impossible: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur traduction: {str(e)}")
