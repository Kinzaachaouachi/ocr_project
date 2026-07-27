from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response

from ..config.settings import STATIC_DIR, BASE_DIR

router = APIRouter(include_in_schema=False)

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",
}


@router.get("/")
async def root():
    return FileResponse(
        path=STATIC_DIR / "pages" / "login.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/register")
async def register_page():
    return FileResponse(
        path=STATIC_DIR / "pages" / "register.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/reset-password")
async def reset_password_page():
    """Page de réinitialisation de mot de passe."""
    return FileResponse(
        path=STATIC_DIR / "pages" / "reset-password.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/verify-email")
async def verify_email_page():
    """Page de vérification d'email."""
    return FileResponse(
        path=STATIC_DIR / "pages" / "verify-email.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/app")
async def dashboard_page():
    """Dashboard — default page after login."""
    return FileResponse(
        path=STATIC_DIR / "pages" / "dashboard.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/app/ocr")
async def ocr_page():
    return FileResponse(
        path=STATIC_DIR / "pages" / "ocr.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/app/history")
async def history_page():
    return FileResponse(
        path=STATIC_DIR / "pages" / "history.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/app/profile")
async def profile_page():
    return FileResponse(
        path=STATIC_DIR / "pages" / "profile.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/app/olm-benchmark")
async def olm_benchmark_page():
    """Page du rapport OLM Benchmark global."""
    return FileResponse(
        path=STATIC_DIR / "pages" / "olm-benchmark.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/app/local-benchmark")
async def local_benchmark_page():
    return FileResponse(
        path=STATIC_DIR / "pages" / "local-benchmark.html",
        media_type="text/html",
        headers=NO_CACHE_HEADERS,
    )


@router.get("/benchmark", response_class=HTMLResponse)
async def benchmark_report():
    benchmark_file = BASE_DIR / "benchmark_report.html"
    if benchmark_file.exists():
        with open(benchmark_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(
        content="<h1>Rapport benchmark non disponible</h1><p>Exécutez: <code>python run_all_benchmarks.py</code></p>",
        status_code=200,
    )


@router.get("/benchmark/olm", response_class=HTMLResponse)
async def olm_benchmark_report():
    olm_file = BASE_DIR / "olm_benchmark_report.html"
    if olm_file.exists():
        with open(olm_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(
        content="<h1>olmOCR-Bench non disponible</h1><p>Exécutez: <code>python generate_olm_report.py</code></p>",
        status_code=200,
    )


@router.get("/favicon.ico")
async def favicon():
    svg = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📄</text></svg>"
    return Response(content=svg, media_type="image/svg+xml")


INTER_FONT_URLS = {
    "Inter-Light.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuOKfMZg.ttf",
    "Inter-Regular.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfMZg.ttf",
    "Inter-Medium.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuI6fMZg.ttf",
    "Inter-SemiBold.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuGKYMZg.ttf",
    "Inter-Bold.woff2": "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuFuYMZg.ttf",
}


@router.get("/assets/fonts/{font_file}")
async def inter_font_fallback(font_file: str):
    font_url = INTER_FONT_URLS.get(font_file)
    if not font_url:
        return Response(status_code=404)
    return RedirectResponse(url=font_url, status_code=307)
