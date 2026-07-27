from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.database import get_db
from ..models.user import User
from ..services.auth_service import get_current_user
from ..services.local_benchmark_service import (
    calculate_user_benchmark_data,
    generate_pdf_report,
)

router = APIRouter(prefix="/api/local-benchmark", tags=["Local Benchmark"])


@router.get("/data")
async def get_local_benchmark_data(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Return user benchmark stats as JSON for the report page."""
    try:
        data = calculate_user_benchmark_data(db, current_user.id)

        data["generated_at"] = data["generated_at"].isoformat()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@router.get("/download/pdf")
async def download_pdf_benchmark(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Download user's local benchmark report as PDF."""
    try:
        data = calculate_user_benchmark_data(db, current_user.id)
        pdf_bytes = generate_pdf_report(data)
        filename = f"benchmark_local_{current_user.email.split('@')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="WeasyPrint n'est pas installé. Veuillez installer avec: pip install weasyprint",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la génération du PDF: {str(e)}"
        )
