from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..models.ocr_history import OCRHistory
from ..models.user import User
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/api", tags=["Historique"])


@router.get("/history")
async def get_ocr_history(
    limit: int = 50,
    model: str = None,
    status: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if limit > 200:
        limit = 200

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
                    "file_path": record.file_path,
                    "model_id": record.model_id,
                    "model_name": record.model_name,
                    "char_count": record.char_count,
                    "word_count": record.word_count,
                    "ocr_time_s": record.ocr_time_s,
                    "status": record.status,
                    "error_message": record.error_message,
                    "processed_at": (
                        record.processed_at.isoformat() if record.processed_at else None
                    ),
                    "client_ip": record.client_ip,
                    "extracted_text": record.extracted_text,
                    "text_preview": (
                        (record.extracted_text[:200] + "...")
                        if record.extracted_text and len(record.extracted_text) > 200
                        else record.extracted_text
                    ),
                    "benchmark": {
                        "precision": record.precision_score,
                        "execution_time": record.ocr_time_s,
                        "init_time": record.init_time_s,
                        "robustness": record.robustness,
                        "global_score": record.global_score,
                    },
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


@router.get("/history/stats")
async def get_ocr_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        total_extractions = (
            db.query(OCRHistory).filter(OCRHistory.user_id == current_user.id).count()
        )
        successful = (
            db.query(OCRHistory)
            .filter(
                OCRHistory.user_id == current_user.id, OCRHistory.status == "success"
            )
            .count()
        )
        failed = (
            db.query(OCRHistory)
            .filter(OCRHistory.user_id == current_user.id, OCRHistory.status == "error")
            .count()
        )

        model_stats = (
            db.query(
                OCRHistory.model_id,
                func.count(OCRHistory.id).label("count"),
                func.avg(OCRHistory.ocr_time_s).label("avg_time"),
                func.sum(OCRHistory.char_count).label("total_chars"),
                func.avg(OCRHistory.precision_score).label("avg_precision"),
                func.avg(OCRHistory.global_score).label("avg_global_score"),
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

        return {
            "status": "success",
            "global_stats": {
                "total_extractions": total_extractions,
                "successful_extractions": successful,
                "failed_extractions": failed,
                "success_rate": (
                    round((successful / total_extractions * 100), 2)
                    if total_extractions > 0
                    else 0
                ),
            },
            "model_stats": [
                {
                    "model_id": stat.model_id,
                    "extractions_count": stat.count,
                    "avg_processing_time_s": round(float(stat.avg_time or 0), 2),
                    "total_characters_processed": stat.total_chars or 0,
                    "avg_precision": round(float(stat.avg_precision or 0), 2),
                    "avg_global_score": round(float(stat.avg_global_score or 0), 2),
                }
                for stat in model_stats
            ],
            "file_type_stats": [
                {"file_type": s.file_type, "count": s.count} for s in file_type_stats
            ],
            "recent_extractions": [
                {
                    "filename": r.filename,
                    "model": r.model_id,
                    "status": r.status,
                    "processed_at": (
                        r.processed_at.isoformat() if r.processed_at else None
                    ),
                }
                for r in recent
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur calcul statistiques: {str(e)}"
        )
