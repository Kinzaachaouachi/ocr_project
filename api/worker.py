# -*- coding: utf-8 -*-
"""
API Worker OCR - Exécuté en sous-processus isolé pour chaque modèle.
Usage interne uniquement (appelé par api/main.py via subprocess).

Arguments :
    --model  : paddleocr | docling | easyocr | trocr
    --file   : chemin absolu vers le fichier à traiter
    --type   : image | pdf | txt
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path

# Supprimer les avertissements
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_DISABLE_MKLDNN"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True, choices=["paddleocr", "docling", "easyocr", "trocr"])
parser.add_argument("--file", required=True)
parser.add_argument("--type", required=True, choices=["image", "pdf", "txt"])
args = parser.parse_args()

file_path = args.file
file_type = args.type


def get_pdf_pages_as_images(pdf_file):
    """Convertit chaque page d'un PDF en image PNG temporaire."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_file)
        page_images = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            out_img = Path(pdf_file).parent / f"_api_tmp_page_{i}.png"
            pix.save(str(out_img))
            page_images.append(str(out_img))
        return page_images
    except Exception as e:
        return []


def cleanup_tmp(paths):
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except Exception:
            pass


# ─── PaddleOCR ───────────────────────────────────────────────────────────────
if args.model == "paddleocr":
    if file_type == "txt":
        print(json.dumps({"status": "unsupported", "reason": "PaddleOCR ne supporte pas les fichiers .txt"}))
        sys.exit(0)
    try:
        t0 = time.time()
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang="fr", use_gpu=False, show_log=False)
        init_time = round(time.time() - t0, 2)

        tmp_files = []
        targets = [file_path]
        if file_type == "pdf":
            targets = get_pdf_pages_as_images(file_path)
            tmp_files = targets
            if not targets:
                raise Exception("Impossible de convertir le PDF en images (PyMuPDF requis).")

        t0 = time.time()
        texts = []
        for img in targets:
            res = ocr.ocr(img, cls=True)
            if res and res[0]:
                texts.append("\n".join([line[1][0] for line in res[0]]))
        ocr_time = round(time.time() - t0, 2)
        cleanup_tmp(tmp_files)

        print(json.dumps({
            "status": "success",
            "model": "PaddleOCR",
            "file_type": file_type,
            "text": "\n".join(texts),
            "init_time": init_time,
            "ocr_time": ocr_time,
            "total_time": round(init_time + ocr_time, 2)
        }))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))


# ─── Docling ─────────────────────────────────────────────────────────────────
elif args.model == "docling":
    try:
        t0 = time.time()
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        init_time = round(time.time() - t0, 2)

        t0 = time.time()
        result = converter.convert(file_path)
        text = result.document.export_to_markdown().strip()
        ocr_time = round(time.time() - t0, 2)

        print(json.dumps({
            "status": "success",
            "model": "Docling",
            "file_type": file_type,
            "text": text,
            "init_time": init_time,
            "ocr_time": ocr_time,
            "total_time": round(init_time + ocr_time, 2)
        }))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))


# ─── EasyOCR ─────────────────────────────────────────────────────────────────
elif args.model == "easyocr":
    if file_type == "txt":
        print(json.dumps({"status": "unsupported", "reason": "EasyOCR ne supporte pas les fichiers .txt"}))
        sys.exit(0)
    try:
        t0 = time.time()
        import easyocr
        reader = easyocr.Reader(['fr', 'en'], gpu=False)
        init_time = round(time.time() - t0, 2)

        tmp_files = []
        targets = [file_path]
        if file_type == "pdf":
            targets = get_pdf_pages_as_images(file_path)
            tmp_files = targets
            if not targets:
                raise Exception("Impossible de convertir le PDF en images (PyMuPDF requis).")

        t0 = time.time()
        texts = []
        for img in targets:
            res = reader.readtext(img)
            if res:
                texts.append("\n".join([line[1] for line in res]))
        ocr_time = round(time.time() - t0, 2)
        cleanup_tmp(tmp_files)

        print(json.dumps({
            "status": "success",
            "model": "EasyOCR",
            "file_type": file_type,
            "text": "\n".join(texts),
            "init_time": init_time,
            "ocr_time": ocr_time,
            "total_time": round(init_time + ocr_time, 2)
        }))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))


# ─── TrOCR ───────────────────────────────────────────────────────────────────
elif args.model == "trocr":
    if file_type == "txt":
        print(json.dumps({"status": "unsupported", "reason": "TrOCR ne supporte pas les fichiers .txt"}))
        sys.exit(0)
    try:
        t0 = time.time()
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel
        import torch
        from PIL import Image
        device = "cuda" if torch.cuda.is_available() else "cpu"
        processor = TrOCRProcessor.from_pretrained("microsoft/trocr-small-printed")
        model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-small-printed").to(device)
        init_time = round(time.time() - t0, 2)

        tmp_files = []
        targets = [file_path]
        if file_type == "pdf":
            targets = get_pdf_pages_as_images(file_path)
            tmp_files = targets
            if not targets:
                raise Exception("Impossible de convertir le PDF en images (PyMuPDF requis).")

        t0 = time.time()
        texts = []
        for img in targets:
            pil_img = Image.open(img).convert("RGB")
            pixel_values = processor(images=pil_img, return_tensors="pt").pixel_values.to(device)
            generated_ids = model.generate(pixel_values, max_new_tokens=128)
            text_tr = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            texts.append(text_tr)
        ocr_time = round(time.time() - t0, 2)
        cleanup_tmp(tmp_files)

        print(json.dumps({
            "status": "success",
            "model": "TrOCR",
            "file_type": file_type,
            "text": "\n".join(texts),
            "init_time": init_time,
            "ocr_time": ocr_time,
            "total_time": round(init_time + ocr_time, 2)
        }))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
