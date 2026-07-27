"""Jobs OCR extract-all en arrière-plan."""

from __future__ import annotations

import os
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from ..models.database import SessionLocal
from ..models.user import User
from ..utils.confidence_analyzer import (
    analyze_text_confidence,
    refine_word_confidence_list,
)
from ..utils.file_helpers import MODELS_INFO
from ..utils.language_detector import (
    detect_language_by_charset,
    detect_language_from_filename,
    detect_language_from_text,
    get_best_models_for_language,
    get_language_name,
)
from ..utils.model_matrix import MODEL_MATRIX, calculate_overall_score
from .ocr_service import (
    calculate_benchmark_metrics,
    run_models_in_parallel,
    save_ocr_result,
)

_jobs: Dict[str, Dict[str, Any]] = {}
_lock = threading.Lock()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def get_active_job_for_user(user_id: int) -> Optional[Dict[str, Any]]:
    with _lock:
        candidates = [
            dict(j)
            for j in _jobs.values()
            if j.get("user_id") == user_id
            and j.get("status") in ("queued", "running", "uploading")
        ]
    if not candidates:
       
        with _lock:
            recent = [
                dict(j)
                for j in _jobs.values()
                if j.get("user_id") == user_id
                and j.get("status") in ("completed", "failed")
            ]
        recent.sort(key=lambda j: j.get("updated_at") or j.get("created_at") or "", reverse=True)
        return recent[0] if recent else None

    candidates.sort(key=lambda j: j.get("created_at") or "", reverse=True)
    return candidates[0]


def _start_soft_progress(job_id: str, stop_event: threading.Event) -> None:
    def _run():
        while not stop_event.wait(1.25):
            with _lock:
                job = _jobs.get(job_id)
                if not job or job.get("status") not in ("queued", "running"):
                    return
                p = float(job.get("progress") or 0)
                ceiling = float(job.get("progress_ceiling") or 35)
                if p >= ceiling:
                    continue
                step = 1.2 if p < 25 else 0.7 if p < 50 else 0.4
                job["progress"] = round(min(ceiling, p + step), 1)
                job["updated_at"] = datetime.now().isoformat()

    threading.Thread(
        target=_run, daemon=True, name=f"ocr-soft-prog-{job_id[:8]}"
    ).start()


def process_extract_all_file(
    *,
    tmp_path: str,
    filename: str,
    file_type: str,
    file_url: Optional[str],
    user_id: int,
    client_ip: str = "unknown",
    job_id: Optional[str] = None,
) -> dict:
    """Exécute les modèles OCR et enregistre l'historique."""
    soft_stop = threading.Event()
    if job_id:
        _update_job(
            job_id,
            status="running",
            progress=5,
            progress_ceiling=14,
            message="Préparation du document…",
        )
        _start_soft_progress(job_id, soft_stop)

    detected_lang_from_filename = detect_language_from_filename(filename)
    available_models = [
        mid
        for mid, minfo in MODELS_INFO.items()
        if file_type in minfo["supported_formats"]
    ]
    if not available_models:
        soft_stop.set()
        raise ValueError(f"Aucun modèle ne supporte le format '{file_type}'")

    def _on_prep_done():
        if not job_id:
            return
        _update_job(
            job_id,
            progress=16,
            progress_ceiling=28,
            message=f"Extraction en cours ({len(available_models)} modèles)…",
        )

    def _on_model_done(done: int, total: int, model_id: str):
        if not job_id:
            return
        pct = 18 + int(67 * done / max(1, total))
        name = MODELS_INFO.get(model_id, {}).get("name", model_id)
        _update_job(
            job_id,
            progress=pct,
            progress_ceiling=min(88, pct + 5),
            message=f"Modèle terminé ({done}/{total}) : {name}",
        )

    overall_start = time.time()
    try:
        futures = run_models_in_parallel(
            tmp_path,
            file_type,
            available_models,
            on_prep_done=_on_prep_done if job_id else None,
            on_model_done=_on_model_done if job_id else None,
        )
    except Exception:
        soft_stop.set()
        raise

    if job_id:
        _update_job(
            job_id,
            progress=88,
            progress_ceiling=94,
            message="Analyse et enregistrement des résultats…",
        )

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("Utilisateur introuvable")

        results = []
        detected_language = None
        detected_language_confidence = 0.0
        total = max(1, len(futures))

        for i, (model_id, result, wall_time) in enumerate(futures):
            if job_id:
                pct = 88 + int(6 * (i + 1) / total)
                _update_job(
                    job_id,
                    progress=pct,
                    progress_ceiling=min(96, pct + 2),
                    message=(
                        f"Analyse : "
                        f"{MODELS_INFO.get(model_id, {}).get('name', model_id)}"
                    ),
                )
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
                    user,
                    filename,
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

        if job_id:
            _update_job(job_id, progress=95, progress_ceiling=98, message="Finalisation…")

        return {
            "status": "success",
            "file": filename,
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
    finally:
        soft_stop.set()
        db.close()


def _update_job(job_id: str, **fields):
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        if "progress" in fields:
            try:
                new_p = float(fields["progress"])
                old_p = float(job.get("progress") or 0)
                if new_p < old_p and fields.get("status") not in ("completed", "failed"):
                    fields = {**fields, "progress": old_p}
            except (TypeError, ValueError):
                pass
        job.update(fields)
        job["updated_at"] = datetime.now().isoformat()


def start_extract_all_job(
    *,
    tmp_path: str,
    filename: str,
    file_type: str,
    file_url: Optional[str],
    user_id: int,
    client_ip: str = "unknown",
) -> str:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "user_id": user_id,
            "filename": filename,
            "file_type": file_type,
            "file_path": file_url,
            "status": "queued",
            "progress": 0,
            "message": "En file d'attente…",
            "result": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def _worker():
        try:
            result = process_extract_all_file(
                tmp_path=tmp_path,
                filename=filename,
                file_type=file_type,
                file_url=file_url,
                user_id=user_id,
                client_ip=client_ip,
                job_id=job_id,
            )
            _update_job(
                job_id,
                status="completed",
                progress=100,
                message="Extraction terminée",
                result=result,
            )
        except Exception as e:
            print(f"[OCR Job {job_id}] erreur: {e}")
            _update_job(
                job_id,
                status="failed",
                progress=100,
                message="Échec de l'extraction",
                error=str(e),
            )
        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    threading.Thread(target=_worker, daemon=True, name=f"ocr-job-{job_id[:8]}").start()
    return job_id
