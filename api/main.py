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
from fastapi.responses import HTMLResponse, JSONResponse, Response, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

# Monter les fichiers statiques
api_dir = Path(__file__).parent
static_dir = api_dir / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Chemin absolu vers le worker OCR
WORKER_PATH = Path(__file__).parent / "worker.py"
PYTHON_EXE = sys.executable

# Extensions autorisées par format
ALLOWED_EXTENSIONS = {
    "image": [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"],
    "pdf": [".pdf"],
    "txt": [".txt"],
    "docx": [".docx", ".doc"],
    "xlsx": [".xlsx", ".xls"]
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
        "description": "Analyse documentaire native (PDF, DOCX, XLSX, TXT, Images). Produit du Markdown structuré.",
        "supported_formats": ["image", "pdf", "txt", "docx", "xlsx"],
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

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
        "<text y='.9em' font-size='90'>📄</text></svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/", response_class=HTMLResponse, tags=["Général"])
async def root():
    """Redirection vers l'interface web dynamique OCR."""
    # Rediriger automatiquement vers l'interface dynamique
    return FileResponse(path=static_dir / "index.html", media_type="text/html")


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
    file: UploadFile = File(..., description="Fichier à traiter (image PNG/JPG, PDF, TXT, DOCX, ou XLSX)"),
    model: str = Form(..., description="Modèle OCR à utiliser : paddleocr | docling | easyocr | trocr")
):
    """
    Extrait le texte d'un fichier (image, PDF, TXT, DOCX, ou XLSX) avec le modèle OCR choisi.

    - **file** : Le fichier à analyser (PNG, JPG, JPEG, BMP, TIFF, WEBP, PDF, TXT, DOCX, DOC, XLSX, XLS)
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
                   f"Extensions acceptées : .png, .jpg, .jpeg, .bmp, .tiff, .webp, .pdf, .txt, .docx, .doc, .xlsx, .xls"
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


@app.post("/translate", tags=["Traduction"])
async def translate_file_or_text(
    target_lang: str = Form(..., description="Langue cible : en, es, de, it, ar, fr, pt, ja, zh, ar, ru, ko, tr, nl, pl, vi"),
    file: UploadFile = File(None, description="Fichier à traduire (Image/PDF/TXT/DOCX/XLSX)"),
    text: str = Form(None, description="Texte à traduire"),
    model: str = Form("auto", description="Modèle OCR : auto|paddleocr|docling|easyocr|trocr"),
):
    """
    Traduit du texte ou le contenu d'un fichier (Image/PDF/TXT/DOCX/XLSX).
    
    Supporte:
    - Fichiers: Images (PNG, JPG, etc), PDF, Fichiers texte (TXT), Documents Word (DOCX), Classeurs Excel (XLSX)
    - Langues: en, es, de, it, ar, fr, pt, ja, zh, ru, ko, tr, nl, pl, vi
    - Modèles: auto-détection ou spécifier (paddleocr, docling, easyocr, trocr)
    """
    import urllib.parse
    import urllib.request
    
    # Valider la langue cible
    allowed_langs = {"en", "es", "de", "it", "ar", "fr", "pt", "ja", "zh", "ru", "ko", "tr", "nl", "pl", "vi"}
    if target_lang not in allowed_langs:
        raise HTTPException(status_code=400, detail=f"Langue non supportée. Langues disponibles: {', '.join(sorted(allowed_langs))}")
    
    # Étape 1: Extraire le texte
    extracted_text = ""
    file_name = ""
    file_type_used = "text"
    model_used = "direct"
    
    if file:
        # ── Traiter le fichier uploadé ──
        file_name = file.filename
        file_type = detect_file_type(file_name)
        
        if file_type is None:
            raise HTTPException(status_code=400, detail=f"Type de fichier non supporté. Acceptés: .png, .jpg, .jpeg, .bmp, .tiff, .webp, .pdf, .txt, .docx, .doc, .xlsx, .xls")
        
        # Auto-sélectionner le modèle
        selected_model = model
        if selected_model == "auto" or selected_model not in MODELS_INFO:
            if file_type == "image":
                selected_model = "paddleocr"
            elif file_type == "pdf":
                selected_model = "docling"
            elif file_type == "txt":
                selected_model = "docling"
            elif file_type == "docx":
                selected_model = "docling"
            elif file_type == "xlsx":
                selected_model = "docling"
            else:
                selected_model = "paddleocr"  # Par défaut
        
        # Vérifier que le modèle existe maintenant
        if selected_model not in MODELS_INFO:
            raise HTTPException(status_code=400, detail=f"Modèle inconnu: {selected_model}")
        
        supported = MODELS_INFO[selected_model]["supported_formats"]
        if file_type not in supported:
            raise HTTPException(status_code=422, detail=f"Modèle '{selected_model}' ne supporte pas '{file_type}'. Supportés: {supported}")
        
        # Extraire le texte du fichier
        suffix = Path(file_name).suffix.lower()
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=".") as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            result = run_worker(selected_model, tmp_path, file_type)
            
            if result.get("status") == "error":
                raise HTTPException(status_code=500, detail=f"Erreur extraction: {result.get('error')}")
            
            extracted_text = result.get("text", "")
            file_type_used = file_type
            model_used = selected_model
            
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    elif text:
        # ── Utiliser le texte fourni ──
        extracted_text = text
        file_type_used = "text"
        model_used = "direct"
    
    else:
        raise HTTPException(status_code=400, detail="Fournir soit un fichier, soit du texte à traduire")
    
    # Étape 2: Vérifier qu'il y a du texte
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Aucun texte à traduire (fichier ou texte vide)")
    
    # Étape 3: Traduire
    try:
        # Limiter le texte pour éviter les erreurs de quota API
        # Support des gros documents jusqu'à 100,000 caractères
        text_to_translate = extracted_text[:100000]  # Limiter à 100000 caractères max
        encoded_text = urllib.parse.quote(text_to_translate)
        
        # MyMemory ne supporte pas "auto", on utilise "fr" par défaut
        source_lang = "fr"
        
        # Construire l'URL avec l'email pour augmenter le quota
        url = f"https://api.mymemory.translated.net/get?q={encoded_text}&langpair={source_lang}|{target_lang}&de=kinza.achaouachi@example.com"
        
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            translation_data = json.loads(response.read().decode('utf-8'))
        
        # Vérifier la réponse
        response_status = translation_data.get("responseStatus")
        response_data = translation_data.get("responseData", {})
        translated = response_data.get("translatedText", "")
        
        # MyMemory retourne 200 même en cas d'erreur partielle
        if response_status == 200 or (response_status == 403 and translated):
            # Si le texte traduit contient "MYMEMORY WARNING", c'est un avertissement de quota
            if "MYMEMORY WARNING" in translated or "QUOTA" in translated.upper():
                # Retourner le texte original avec un avertissement
                return {
                    "status": "quota_exceeded",
                    "original_text": extracted_text[:300],
                    "translated_text": extracted_text[:300],  # Retourner l'original
                    "warning": "Quota API dépassé. Texte original retourné.",
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "file_name": file_name if file_name else None,
                    "file_type": file_type_used,
                    "model_used": model_used,
                    "char_count": len(extracted_text),
                    "word_count": len(extracted_text.split()),
                    "translated_at": datetime.now().isoformat()
                }
            
            return {
                "status": "success",
                "original_text": extracted_text[:300],
                "translated_text": translated,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "file_name": file_name if file_name else None,
                "file_type": file_type_used,
                "model_used": model_used,
                "char_count": len(extracted_text),
                "word_count": len(extracted_text.split()),
                "translated_at": datetime.now().isoformat()
            }
        else:
            # Erreur API
            error_msg = translation_data.get("responseDetails", "Erreur inconnue")
            raise HTTPException(
                status_code=503, 
                detail=f"API MyMemory: {error_msg}. Essayez plus tard ou avec un texte plus court."
            )
    
    except urllib.error.HTTPError as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Erreur HTTP {e.code}: API traduction temporairement indisponible. Réessayez dans quelques secondes."
        )
    except urllib.error.URLError as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Connexion impossible à l'API de traduction: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur traduction: {str(e)}. Vérifiez votre connexion Internet."
        )
