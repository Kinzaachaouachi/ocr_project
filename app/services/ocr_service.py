import concurrent.futures
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from ..models.ocr_history import OCRHistory
from ..models.user import User
from ..utils import model_workers
from ..utils.file_helpers import detect_file_type, MODELS_INFO
from ..utils.confidence_analyzer import (
    analyze_text_confidence,
    refine_word_confidence_list,
)
from ..utils.language_detector import (
    detect_language_by_charset,
    detect_language_from_filename,
    detect_language_from_text,
    get_best_models_for_language,
    get_language_name,
)
from ..utils.model_matrix import MODEL_MATRIX, calculate_overall_score


def run_worker(
    model: str,
    file_path: str,
    file_type: str,
    *,
    prepared_images=None,
    skip_enhance: bool = False,
    docling_path: str = None,
) -> dict:
    """Run a single OCR model worker."""
    try:
        if model not in model_workers.INFERENCE_FUNCS:
            return {"status": "error", "error": f"Modèle '{model}' non supporté"}

        inference_func = model_workers.INFERENCE_FUNCS[model]
        kwargs = {"skip_enhance": skip_enhance}
        if prepared_images is not None:
            kwargs["prepared_images"] = prepared_images
        if model == "docling" and docling_path:
            kwargs["docling_path"] = docling_path
        return inference_func(file_path, file_type, **kwargs)
    except Exception as e:
        print(f"Erreur {model}: {str(e)}")
        return {"status": "error", "error": f"Erreur {model}: {str(e)}"}


def _run_worker_timed(
    model_id: str,
    file_path: str,
    file_type: str,
    *,
    prepared_images=None,
    skip_enhance: bool = False,
    docling_path: str = None,
):
    t0 = time.time()
    result = run_worker(
        model_id,
        file_path,
        file_type,
        prepared_images=prepared_images,
        skip_enhance=skip_enhance,
        docling_path=docling_path,
    )
    return model_id, result, round(time.time() - t0, 2)


def run_models_in_parallel(file_path: str, file_type: str, model_ids: list) -> list:
    """
    Run OCR models concurrently with shared preprocessing:
    - PDF→images converted once
    - large images downscaled once
    - heavy per-model enhance skipped (already resized)
    """
    results = []
    shared = None
    try:
        t_prep = time.time()
        shared = model_workers.prepare_shared_ocr_inputs(file_path, file_type)
        prep_s = round(time.time() - t_prep, 2)
        print(
            f"⚡ Préparation partagée OCR: {prep_s}s "
            f"({len(shared.get('images') or [])} image(s))"
        )

        prepared_images = shared.get("images") or None
        docling_path = shared.get("docling_path") or file_path
        
        image_models = {"paddleocr", "easyocr", "trocr"}

        max_workers = max(1, len(model_ids))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_model = {}
            for model_id in model_ids:
                use_shared = (
                    prepared_images is not None
                    and model_id in image_models
                    and file_type in ("image", "pdf")
                )
                future = executor.submit(
                    _run_worker_timed,
                    model_id,
                    file_path,
                    file_type,
                    prepared_images=prepared_images if use_shared else None,
                    skip_enhance=True,
                    docling_path=docling_path if model_id == "docling" else None,
                )
                future_to_model[future] = model_id

            for future in concurrent.futures.as_completed(future_to_model):
                model_id = future_to_model[future]
                try:
                    results.append(future.result())
                except Exception as exc:
                    results.append(
                        (model_id, {"status": "error", "error": str(exc)}, 0.0)
                    )
    finally:
        if shared and shared.get("cleanup"):
            model_workers.cleanup_tmp(shared["cleanup"])

    return results


def calculate_benchmark_metrics(result: dict, model_id: str) -> dict:
    """
    Calculate benchmark metrics for a single OCR extraction result.
    Returns dict with precision_score, init_time_s, robustness, global_score.
    """
    if result.get("status") != "success":
        return {
            "precision_score": 0.0,
            "init_time_s": 0.0,
            "robustness": 0.0,
            "global_score": 0.0,
        }

    word_confidence = refine_word_confidence_list(
        result.get("word_confidence", []),
        model_id=model_id,
        text=result.get("text", ""),
    )

    result["word_confidence"] = word_confidence
    confidence_stats = analyze_text_confidence(word_confidence)

    precision = round(confidence_stats.get("avg_confidence", 0.0) * 100, 2)

    init_time = result.get("init_time", 0.0)

    high_pct = confidence_stats.get("high_confidence_percentage", 0.0)
    word_count = len(result.get("text", "").split())
    text_score = min(100, word_count / 5)
    robustness = round((high_pct * 0.7 + text_score * 0.3), 2)

    ocr_time = result.get("ocr_time", 1.0) or 1.0
    speed_score = min(100, (1.0 / ocr_time) * 50)

    static_score = calculate_overall_score(model_id)

    global_score = round(
        precision * 0.35 + speed_score * 0.15 + robustness * 0.25 + static_score * 0.25,
        2,
    )

    return {
        "precision_score": precision,
        "init_time_s": init_time,
        "robustness": robustness,
        "global_score": global_score,
    }


def save_ocr_result(
    db: Session,
    user: User,
    filename: str,
    file_type: str,
    file_path: str,
    model_id: str,
    result: dict,
    wall_time: float,
    client_ip: str,
) -> OCRHistory:
    """Save an OCR extraction result to the database with benchmark metrics."""
    try:
        if result.get("status") == "success":
            text = result.get("text", "")
            metrics = calculate_benchmark_metrics(result, model_id)

            entry = OCRHistory(
                user_id=user.id,
                filename=filename,
                file_type=file_type,
                file_path=file_path,
                model_id=model_id,
                model_name=MODELS_INFO[model_id]["name"],
                extracted_text=text[:65535],
                char_count=len(text),
                word_count=len(text.split()),
                ocr_time_s=result.get("ocr_time", 0),
                status="success",
                error_message=None,
                processed_at=datetime.now(),
                client_ip=client_ip,
                precision_score=metrics["precision_score"],
                init_time_s=metrics["init_time_s"],
                robustness=metrics["robustness"],
                global_score=metrics["global_score"],
            )
        else:
            status_val = "error" if result.get("status") == "error" else "unsupported"
            error_msg = result.get("error", result.get("reason", "Erreur inconnue"))

            entry = OCRHistory(
                user_id=user.id,
                filename=filename,
                file_type=file_type,
                file_path=file_path,
                model_id=model_id,
                model_name=MODELS_INFO[model_id]["name"],
                extracted_text=None,
                char_count=0,
                word_count=0,
                ocr_time_s=0,
                status=status_val,
                error_message=str(error_msg)[:65535],
                processed_at=datetime.now(),
                client_ip=client_ip,
                precision_score=0.0,
                init_time_s=0.0,
                robustness=0.0,
                global_score=0.0,
            )

        db.add(entry)
        db.commit()
        print(f" Sauvegardé en DB: {model_id} - {filename} (path: {file_path})")
        return entry

    except Exception as db_error:
        print(f" Erreur DB pour {model_id}: {db_error}")
        db.rollback()
        return None
