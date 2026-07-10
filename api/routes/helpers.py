
import concurrent.futures
import os
import time
from pathlib import Path

from .. import model_workers


ALLOWED_EXTENSIONS = {
    "image": [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"],
    "pdf": [".pdf"],
    "txt": [".txt"],
    "docx": [".docx", ".doc"],
    "xlsx": [".xlsx", ".xls"],
}

MODELS_INFO = {
    "paddleocr": {
        "name": "PaddleOCR",
        "description": "Moteur OCR rapide et précis, supporte images et PDF (via PyMuPDF).",
        "supported_formats": ["image", "pdf"],
        "typical_accuracy": "~99%",
        "typical_speed": "~1s (inférence)",
    },
    "docling": {
        "name": "Docling",
        "description": "Analyse documentaire native (PDF, DOCX, XLSX, TXT, Images). Produit du Markdown structuré.",
        "supported_formats": ["image", "pdf", "txt", "docx", "xlsx"],
        "typical_accuracy": "~96%",
        "typical_speed": "~12s (inférence)",
    },
    "easyocr": {
        "name": "EasyOCR",
        "description": "OCR multi-langue basé sur PyTorch. Simple à utiliser, supporte images et PDF.",
        "supported_formats": ["image", "pdf"],
        "typical_accuracy": "~93%",
        "typical_speed": "~1.2s (inférence)",
    },
    "trocr": {
        "name": "TrOCR",
        "description": "Modèle Transformer Microsoft. Optimal pour lignes de texte isolées (manuscrit ou imprimé).",
        "supported_formats": ["image", "pdf"],
        "typical_accuracy": "~20% (multi-ligne sans segmentation)",
        "typical_speed": "~0.4s (inférence)",
    },
}


def detect_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for ftype, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return ftype
    return None


def run_worker(model: str, file_path: str, file_type: str) -> dict:
    try:
        if model in model_workers.INFERENCE_FUNCS:
            inference_func = model_workers.INFERENCE_FUNCS[model]
            return inference_func(file_path, file_type)
        else:
            return {
                "status": "error",
                "error": f"Modèle '{model}' non supporté",
            }
    except Exception as e:
        print(f" Erreur {model}: {str(e)}")
        return {
            "status": "error",
            "error": f"Erreur {model}: {str(e)}",
        }


def _run_worker_timed(model_id: str, file_path: str, file_type: str):
    t0 = time.time()
    result = run_worker(model_id, file_path, file_type)
    return model_id, result, round(time.time() - t0, 2)


def run_models_in_parallel(file_path: str, file_type: str, model_ids: list) -> list:
    results = []
    max_workers = max(1, len(model_ids))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_model = {
            executor.submit(_run_worker_timed, model_id, file_path, file_type): model_id
            for model_id in model_ids
        }
        for future in concurrent.futures.as_completed(future_to_model):
            model_id = future_to_model[future]
            try:
                results.append(future.result())
            except Exception as exc:
                results.append((model_id, {"status": "error", "error": str(exc)}, 0.0))
    return results
