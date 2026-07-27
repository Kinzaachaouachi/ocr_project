from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.database import get_db
from ..models.user import User
from ..services.olm_report_service import (
    generate_olm_report_data,
    generate_html_report,
    generate_pdf_report,
)
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/api/olm-report", tags=["OLM Benchmark Report"])


@router.get("/data")
async def get_olm_report_data(
    include_user_stats: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get OLM benchmark report data as JSON."""
    try:
        user_id = current_user.id if include_user_stats else None
        report_data = generate_olm_report_data(db, user_id=user_id)
        return report_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération des données: {str(e)}",
        )


@router.get("/html", response_class=HTMLResponse)
async def get_olm_report_html(
    include_user_stats: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get OLM benchmark report as HTML page."""
    try:
        user_id = current_user.id if include_user_stats else None
        report_data = generate_olm_report_data(db, user_id=user_id)
        html_content = generate_html_report(report_data)
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du rapport HTML: {str(e)}",
        )


@router.get("/download/pdf")
async def download_pdf_report(
    include_user_stats: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download OLM benchmark report as PDF."""
    try:
        user_id = current_user.id if include_user_stats else None
        report_data = generate_olm_report_data(db, user_id=user_id)
        pdf_bytes = generate_pdf_report(report_data)

        filename = (
            f"rapport_olm_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="WeasyPrint n'est pas installé. pip install weasyprint",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la génération du PDF: {str(e)}"
        )


@router.get("/preview")
async def preview_report(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get a preview of the report with basic statistics."""
    try:
        report_data = generate_olm_report_data(db, user_id=current_user.id)

        top_models = sorted(report_data["benchmark_matrix"], key=lambda x: x["rank"])[
            :3
        ]

        return {
            "benchmark_info": report_data["benchmark_info"],
            "top_models": [
                {
                    "rank": m["rank"],
                    "name": m["name"],
                    "overall_score": m["scores"]["overall"],
                    "std_dev": m.get("std_dev"),
                }
                for m in top_models
            ],
            "total_models": len(report_data["benchmark_matrix"]),
            "user_stats": report_data.get("user_stats"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération de l'aperçu: {str(e)}",
        )
