from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.database import get_db
from ..models.user import User
from ..services.auth_service import get_current_user
from ..services.local_benchmark_service import (
    calculate_user_benchmark_data,
    generate_csv_report,
    generate_excel_report,
    generate_pdf_report,
    generate_word_report,
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
    """
    Download user's local benchmark report as PDF.
    Direct download - no page interface.
    """
    try:

        data = calculate_user_benchmark_data(db, current_user.id)

        pdf_bytes = generate_pdf_report(data)

        filename = f"benchmark_local_{current_user.email.split('@')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail="WeasyPrint n'est pas installé. Veuillez installer avec: pip install weasyprint",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la génération du PDF: {str(e)}"
        )


@router.get("/download/docx")
async def download_word_benchmark(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Download user's local benchmark report as Word document.
    Direct download - no page interface.
    """
    try:

        data = calculate_user_benchmark_data(db, current_user.id)

        docx_bytes = generate_word_report(data)

        filename = f"benchmark_local_{current_user.email.split('@')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="python-docx n'est pas installé. Veuillez installer avec: pip install python-docx",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du document Word: {str(e)}",
        )


@router.get("/download/excel")
async def download_excel_benchmark(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Download user's local benchmark report as Excel spreadsheet.
    Direct download - no page interface.
    """
    try:

        data = calculate_user_benchmark_data(db, current_user.id)

        excel_bytes = generate_excel_report(data)

        filename = f"benchmark_local_{current_user.email.split('@')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="openpyxl n'est pas installé. Veuillez installer avec: pip install openpyxl",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du fichier Excel: {str(e)}",
        )


@router.get("/download/csv")
async def download_csv_benchmark(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Download user's local benchmark report as CSV file.
    Direct download - no page interface.
    """
    try:

        data = calculate_user_benchmark_data(db, current_user.id)

        csv_content = generate_csv_report(data)

        filename = f"benchmark_local_{current_user.email.split('@')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la génération du CSV: {str(e)}"
        )
