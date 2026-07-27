from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from sqlalchemy.orm import Session

from ..config.settings import BASE_DIR
from ..models.database import get_db
from ..models.ocr_history import OCRHistory
from ..models.user import User
from ..services.auth_service import get_current_user
from ..services.benchmark_service import (
    generate_benchmark_csv,
    generate_benchmark_excel,
    get_user_benchmark_stats,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get aggregated benchmark metrics for the current user."""
    try:
        stats = get_user_benchmark_stats(db, current_user.id)
        return {"status": "success", **stats}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur calcul métriques: {str(e)}"
        )


@router.get("/export/excel")
async def export_benchmark_excel(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export benchmark data as Excel file."""
    try:
        excel_bytes = generate_benchmark_excel(db, current_user.id)
        filename = f"benchmark_{current_user.email.split('@')[0]}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur export Excel: {str(e)}")


@router.get("/export/csv")
async def export_benchmark_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export benchmark data as CSV file."""
    try:
        csv_content = generate_benchmark_csv(db, current_user.id)
        filename = f"benchmark_{current_user.email.split('@')[0]}_{datetime.now().strftime('%Y%m%d')}.csv"
        return Response(
            content=csv_content.encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur export CSV: {str(e)}")


@router.get("/benchmark/global")
async def global_benchmark(
    current_user: User = Depends(get_current_user),
):
    """Sert le HTML du rapport benchmark global."""
    benchmark_file = BASE_DIR / "benchmark_report.html"
    if benchmark_file.exists():
        return FileResponse(path=str(benchmark_file), media_type="text/html")
    return {
        "status": "not_found",
        "message": "Le rapport benchmark global n'a pas encore été généré.",
    }
