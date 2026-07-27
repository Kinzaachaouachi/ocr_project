from pathlib import Path

from ..config.settings import ALLOWED_EXTENSIONS


def detect_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for ftype, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return ftype
    return None


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
