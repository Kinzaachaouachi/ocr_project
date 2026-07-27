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
    file_type = detect_file_type(file.filename)
    if file_type is None:
        raise HTTPException(
            status_code=400,
            detail=f"Extension non supportée : '{Path(file.filename).suffix}'",
        )

    suffix = Path(file.filename).suffix.lower()
    tmp_path = None
    uploaded_file_path = None
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
            file_url = None
            print(f"Warning: Could not save uploaded file: {e}")

        detected_lang_from_filename = detect_language_from_filename(file.filename)
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
                    word_confidence_data = refine_word_confidence_list(
                        result.get("word_confidence", []),
                        model_id=model_id,
                        text=text,
                    )
                    result["word_confidence"] = word_confidence_data

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

                    confidence_stats = analyze_text_confidence(word_confidence_data)
                    model_matrix_score = calculate_overall_score(model_id)
                    metrics = calculate_benchmark_metrics(result, model_id)

                    results.append(
                        {
                            "model_id": model_id,
                            "model_name": MODELS_INFO[model_id]["name"],
                            "status": "success",
                            "text": text,
                            "word_confidence": word_confidence_data,
                            "confidence_stats": confidence_stats,
                            "char_count": len(text),
                            "word_count": len(text.split()),
                            "timing": {
                                "init_time_s": result.get("init_time", 0),
                                "ocr_time_s": result.get("ocr_time", 0),
                                "total_time_s": result.get("total_time", 0),
                                "wall_time_s": wall_time,
                            },
                            "quality_score": 0,
                            "model_score": model_matrix_score,
                            "benchmark": metrics,
                            "language_support": detected_language
                            in MODEL_MATRIX.get(model_id, {}).get("languages", []),
                        }
                    )
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

                save_ocr_result(
                    db,
                    current_user,
                    file.filename,
                    file_type,
                    file_url,
                    model_id,
                    result,
                    wall_time,
                    client_ip,
                )

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

        successful_results = [r for r in results if r["status"] == "success"]
        if successful_results:
            max_char_count = max(r["char_count"] for r in successful_results) or 1
            min_ocr_time = (
                min(r["timing"]["ocr_time_s"] for r in successful_results) or 0.01
            )

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

        return {
            "status": "success",
            "file": file.filename,
            "file_type": file_type,
            "file_path": file_url,
            "detected_language": {
                "code": detected_language,
                "name": get_language_name(detected_language),
                "confidence": round(detected_language_confidence, 2),
                "detection_method": (
                    "filename" if detected_lang_from_filename else "text_analysis"
                ),
            },
            "recommended_models": get_best_models_for_language(detected_language),
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
