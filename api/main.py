# -*- coding: utf-8 -*-
"""
API REST OCR - FastAPI
Auteur : Kinza Achaouachi

Endpoints :
  GET  /              → Page d'accueil HTML
  GET  /health        → Statut de l'API
  GET  /models        → Liste des modèles disponibles
  POST /extract       → Extraction OCR (upload fichier + choix du modèle)
  GET  /docs          → Documentation Swagger automatique (FastAPI)
"""

import os
import sys
import json
import time
import uuid
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ─── Initialisation de l'application ─────────────────────────────────────────

app = FastAPI(
    title="API OCR - Extraction de Texte",
    description="API REST pour extraire du texte depuis des images et des PDF via PaddleOCR, Docling, EasyOCR ou TrOCR.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Autoriser toutes les origines (CORS) pour faciliter les tests frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chemin absolu vers le worker OCR
WORKER_PATH = Path(__file__).parent / "worker.py"
PYTHON_EXE = sys.executable

# Extensions autorisées par format
ALLOWED_EXTENSIONS = {
    "image": [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"],
    "pdf": [".pdf"],
    "txt": [".txt"]
}

MODELS_INFO = {
    "paddleocr": {
        "name": "PaddleOCR",
        "description": "Moteur OCR rapide et précis, supporte images et PDF (via PyMuPDF).",
        "supported_formats": ["image", "pdf"],
        "typical_accuracy": "~99%",
        "typical_speed": "~1s (inférence)"
    },
    "docling": {
        "name": "Docling",
        "description": "Analyse documentaire native (PDF, DOCX, TXT, Images). Produit du Markdown structuré.",
        "supported_formats": ["image", "pdf", "txt"],
        "typical_accuracy": "~96%",
        "typical_speed": "~12s (inférence)"
    },
    "easyocr": {
        "name": "EasyOCR",
        "description": "OCR multi-langue basé sur PyTorch. Simple à utiliser, supporte images et PDF.",
        "supported_formats": ["image", "pdf"],
        "typical_accuracy": "~93%",
        "typical_speed": "~1.2s (inférence)"
    },
    "trocr": {
        "name": "TrOCR",
        "description": "Modèle Transformer Microsoft. Optimal pour lignes de texte isolées (manuscrit ou imprimé).",
        "supported_formats": ["image", "pdf"],
        "typical_accuracy": "~20% (multi-ligne sans segmentation)",
        "typical_speed": "~0.4s (inférence)"
    }
}


# ─── Utilitaire : détecter le type de fichier ─────────────────────────────────

def detect_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for ftype, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return ftype
    return None


# ─── Utilitaire : appeler le worker dans un sous-processus isolé ──────────────

def run_worker(model: str, file_path: str, file_type: str) -> dict:
    """
    Lance api/worker.py dans un sous-processus Python indépendant.
    Nécessaire pour isoler PaddleOCR (PaddlePaddle) de TrOCR/EasyOCR (PyTorch)
    car leurs DLL Windows (shm.dll) entrent en conflit dans un même processus.
    """
    cmd = [
        PYTHON_EXE,
        str(WORKER_PATH),
        "--model", model,
        "--file", file_path,
        "--type", file_type
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300  # 5 minutes max
    )

    # Chercher la première ligne JSON dans la sortie
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)

    # Aucun JSON trouvé → erreur
    return {
        "status": "error",
        "error": result.stderr.strip() or "Aucune sortie JSON du worker."
    }


# ─── ENDPOINTS ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, tags=["Général"])
async def root():
    """Page d'accueil de l'API avec liens vers la documentation."""
    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API OCR - Extraction de Texte</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Inter', sans-serif;
                background: radial-gradient(circle at top left, #1e1b4b, #0f172a 50%, #020617);
                color: #f8fafc;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 40px 20px;
            }
            .container { max-width: 900px; width: 100%; }
            h1 {
                font-size: 3em;
                font-weight: 800;
                background: linear-gradient(135deg, #a5b4fc, #6366f1 50%, #4338ca);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 10px;
                letter-spacing: -0.02em;
            }
            .subtitle { color: #94a3b8; font-size: 1.1em; margin-bottom: 50px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
            .card {
                background: rgba(30, 41, 59, 0.7);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
                padding: 24px;
                backdrop-filter: blur(16px);
                transition: transform 0.2s, border-color 0.2s;
                text-decoration: none;
                color: inherit;
                display: block;
            }
            .card:hover { transform: translateY(-4px); border-color: rgba(99,102,241,0.4); }
            .card-icon { font-size: 2em; margin-bottom: 12px; }
            .card-title { font-size: 1.1em; font-weight: 700; margin-bottom: 6px; }
            .card-desc { color: #94a3b8; font-size: 0.9em; line-height: 1.5; }
            .badge {
                display: inline-block;
                background: rgba(16, 185, 129, 0.15);
                border: 1px solid rgba(16, 185, 129, 0.3);
                color: #34d399;
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 0.8em;
                font-weight: 600;
                margin-bottom: 30px;
            }
            .models { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
            .model-tag {
                background: rgba(99,102,241,0.1);
                border: 1px solid rgba(99,102,241,0.2);
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 0.85em;
                font-weight: 600;
                color: #a5b4fc;
            }
            footer { text-align: center; margin-top: 40px; color: #475569; font-size: 0.85em; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="badge">● API en ligne</div>
            <h1>API OCR</h1>
            <p class="subtitle">Extraction automatique de texte depuis images et PDF — PaddleOCR · Docling · EasyOCR · TrOCR</p>

            <div class="grid">
                <a href="/docs" class="card">
                    <div class="card-icon">📖</div>
                    <div class="card-title">Documentation Swagger</div>
                    <div class="card-desc">Interface interactive pour tester tous les endpoints directement dans le navigateur.</div>
                </a>
                <a href="/redoc" class="card">
                    <div class="card-icon">📋</div>
                    <div class="card-title">Documentation ReDoc</div>
                    <div class="card-desc">Documentation complète générée automatiquement avec schémas de réponses.</div>
                </a>
                <a href="/health" class="card">
                    <div class="card-icon">💚</div>
                    <div class="card-title">Health Check</div>
                    <div class="card-desc">Vérifier que l'API est opérationnelle et obtenir les informations de version.</div>
                </a>
                <a href="/models" class="card">
                    <div class="card-icon">🤖</div>
                    <div class="card-title">Modèles disponibles</div>
                    <div class="card-desc">Liste complète des modèles OCR avec leurs formats supportés et performances.</div>
                </a>
            </div>

            <div style="background: rgba(30,41,59,0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 24px; margin-bottom: 30px;">
                <div style="font-weight: 700; margin-bottom: 16px; color: #e2e8f0;">🚀 Endpoint principal</div>
                <code style="background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2); border-radius: 8px; padding: 12px 16px; display: block; color: #a5b4fc; font-size: 0.95em;">
                    POST /extract<br>
                    &nbsp;&nbsp;file: &lt;image.png | document.pdf | fichier.txt&gt;<br>
                    &nbsp;&nbsp;model: paddleocr | docling | easyocr | trocr
                </code>
            </div>

            <div style="font-weight: 600; margin-bottom: 12px; color: #94a3b8;">Modèles OCR intégrés :</div>
            <div class="models">
                <div class="model-tag">🔴 PaddleOCR — Images &amp; PDF</div>
                <div class="model-tag">🟠 Docling — PDF, TXT, Images</div>
                <div class="model-tag">🟢 EasyOCR — Images &amp; PDF</div>
                <div class="model-tag">🟣 TrOCR — Images (ligne unique)</div>
            </div>

            <footer>Projet de stage — Kinza Achaouachi · Évaluation d'outils OCR open source</footer>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/health", tags=["Général"])
async def health_check():
    """Vérifie que l'API est opérationnelle."""
    return {
        "status": "ok",
        "api": "OCR REST API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "models_available": list(MODELS_INFO.keys())
    }


@app.get("/models", tags=["Modèles"])
async def list_models():
    """Retourne la liste des modèles OCR disponibles avec leurs caractéristiques."""
    return {
        "models": MODELS_INFO,
        "total": len(MODELS_INFO)
    }


@app.post("/extract", tags=["Extraction OCR"])
async def extract_text(
    file: UploadFile = File(..., description="Fichier à traiter (image PNG/JPG, PDF, ou TXT)"),
    model: str = Form(..., description="Modèle OCR à utiliser : paddleocr | docling | easyocr | trocr")
):
    """
    Extrait le texte d'un fichier (image, PDF ou TXT) avec le modèle OCR choisi.

    - **file** : Le fichier à analyser (PNG, JPG, JPEG, BMP, TIFF, WEBP, PDF, TXT)
    - **model** : Le moteur OCR à utiliser (`paddleocr`, `docling`, `easyocr`, `trocr`)

    Retourne le texte extrait, les temps d'exécution, et les métadonnées.
    """

    # Valider le modèle
    if model not in MODELS_INFO:
        raise HTTPException(
            status_code=400,
            detail=f"Modèle inconnu : '{model}'. Modèles disponibles : {list(MODELS_INFO.keys())}"
        )

    # Valider le type de fichier
    file_type = detect_file_type(file.filename)
    if file_type is None:
        raise HTTPException(
            status_code=400,
            detail=f"Extension de fichier non supportée : '{Path(file.filename).suffix}'. "
                   f"Extensions acceptées : .png, .jpg, .jpeg, .bmp, .tiff, .webp, .pdf, .txt"
        )

    # Vérifier la compatibilité modèle ↔ format
    supported = MODELS_INFO[model]["supported_formats"]
    if file_type not in supported:
        raise HTTPException(
            status_code=422,
            detail=f"Le modèle '{model}' ne supporte pas le format '{file_type}'. "
                   f"Formats supportés par ce modèle : {supported}"
        )

    # Sauvegarder le fichier uploadé dans un fichier temporaire
    suffix = Path(file.filename).suffix.lower()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=".") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Lancer le worker en sous-processus isolé
        t_start = time.time()
        result = run_worker(model, tmp_path, file_type)
        wall_time = round(time.time() - t_start, 2)

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Délai d'attente dépassé (300s). Réessayez avec un fichier plus petit.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
    finally:
        # Toujours nettoyer le fichier temporaire
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    # Gérer les cas d'erreur retournés par le worker
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Erreur inconnue du worker OCR."))

    if result.get("status") == "unsupported":
        raise HTTPException(status_code=422, detail=result.get("reason", "Format non supporté."))

    # Réponse succès
    return {
        "status": "success",
        "model": MODELS_INFO[model]["name"],
        "model_id": model,
        "file": file.filename,
        "file_type": file_type,
        "text": result.get("text", ""),
        "char_count": len(result.get("text", "")),
        "word_count": len(result.get("text", "").split()),
        "timing": {
            "init_time_s": result.get("init_time", 0),
            "ocr_time_s": result.get("ocr_time", 0),
            "total_model_time_s": result.get("total_time", 0),
            "wall_time_s": wall_time
        },
        "processed_at": datetime.now().isoformat()
    }
