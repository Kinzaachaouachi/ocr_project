"""Conversion HTML → PDF avec fallback Windows (sans GTK)."""

from __future__ import annotations

from io import BytesIO


def html_to_pdf(html_content: str) -> bytes:
    """
    Génère un PDF depuis du HTML.
    1) WeasyPrint si les libs système sont dispo
    2) sinon xhtml2pdf (fonctionne sous Windows sans GTK)
    """
    weasy_error = None
    try:
        from weasyprint import HTML

        return HTML(string=html_content).write_pdf()
    except ImportError as e:
        weasy_error = e
    except Exception as e:
        # Ex. libgobject manquant sur Windows (error 0x7e)
        weasy_error = e

    try:
        from xhtml2pdf import pisa
    except ImportError as e:
        raise RuntimeError(
            "Impossible de générer le PDF. "
            "Installez xhtml2pdf (recommandé sous Windows) : pip install xhtml2pdf "
            "ou WeasyPrint + GTK : pip install weasyprint. "
            f"Détail WeasyPrint : {weasy_error}"
        ) from e

    buf = BytesIO()
    result = pisa.CreatePDF(src=html_content, dest=buf, encoding="utf-8")
    if result.err:
        raise RuntimeError(
            f"Échec génération PDF (xhtml2pdf). WeasyPrint : {weasy_error}"
        )
    return buf.getvalue()
