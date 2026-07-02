

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
parser.add_argument("--type", required=True, choices=["image", "pdf", "txt", "docx", "xlsx"])
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
        # Certains builds de paddleocr n'acceptent plus l'argument `show_log`.
        # On tente d'abord avec, puis on retombe sur une initialisation sans cet argument.
        try:
            ocr = PaddleOCR(use_angle_cls=True, lang="fr", use_gpu=False, show_log=False)
        except TypeError:
            ocr = PaddleOCR(use_angle_cls=True, lang="fr", use_gpu=False)
        init_time = round(time.time() - t0, 2)

        tmp_files = []
        targets = [file_path]
        if file_type == "pdf":
            targets = get_pdf_pages_as_images(file_path)
            tmp_files = targets
            if not targets:
                raise Exception("Impossible de convertir le PDF en images (PyMuPDF requis).")

        t0 = time.time()
        all_lines = []
        word_confidence_data = []

        for img in targets:
            res = ocr.ocr(img, cls=True)
            if res and res[0]:
                # Trier les lignes par position verticale pour préserver l'ordre
                sorted_lines = sorted(res[0], key=lambda x: x[0][0][1])

                prev_y = None
                for line in sorted_lines:
                    text = line[1][0]
                    confidence = line[1][1]
                    y_pos = line[0][0][1]

                    # Détecter les lignes vides (grand écart vertical)
                    if prev_y is not None and (y_pos - prev_y) > 50:
                        all_lines.append("")

                    all_lines.append(text)

                    # Stocker la confiance par mot
                    words = text.split()
                    for word in words:
                        word_confidence_data.append({
                            "word": word,
                            "confidence": round(confidence, 2)
                        })

                    prev_y = y_pos

        ocr_time = round(time.time() - t0, 2)
        cleanup_tmp(tmp_files)

        print(json.dumps({
            "status": "success",
            "model": "PaddleOCR",
            "file_type": file_type,
            "text": "\n".join(all_lines),
            "word_confidence": word_confidence_data,
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
        
        # Docling nécessite un chemin absolu valide
        abs_file_path = os.path.abspath(file_path)
        
        # Convertir le chemin en objet Path pour Docling
        from pathlib import Path as PathlibPath
        result = converter.convert(PathlibPath(abs_file_path))
        text = result.document.export_to_markdown().strip()
        ocr_time = round(time.time() - t0, 2)

        # Pour Docling, estimer la confiance à 0.85 (pas de scores individuels disponibles)
        word_confidence_data = []
        words = text.split()
        for word in words:
            if word.strip():
                word_confidence_data.append({
                    "word": word,
                    "confidence": 0.85
                })

        print(json.dumps({
            "status": "success",
            "model": "Docling",
            "file_type": file_type,
            "text": text,
            "word_confidence": word_confidence_data,
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
        all_lines = []
        word_confidence_data = []
        
        for img in targets:
            res = reader.readtext(img)
            if res:
                # Trier par position verticale
                sorted_lines = sorted(res, key=lambda x: x[0][0][1])
                
                prev_y = None
                for line in sorted_lines:
                    text = line[1]
                    confidence = line[2]
                    y_pos = line[0][0][1]
                    
                    # Détecter les lignes vides
                    if prev_y is not None and (y_pos - prev_y) > 50:
                        all_lines.append("")
                    
                    all_lines.append(text)
                    
                    # Stocker la confiance par mot
                    words = text.split()
                    for word in words:
                        word_confidence_data.append({
                            "word": word,
                            "confidence": round(confidence, 2)
                        })
                    
                    prev_y = y_pos
                    
        ocr_time = round(time.time() - t0, 2)
        cleanup_tmp(tmp_files)

        print(json.dumps({
            "status": "success",
            "model": "EasyOCR",
            "file_type": file_type,
            "text": "\n".join(all_lines),
            "word_confidence": word_confidence_data,
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
        word_confidence_data = []
        
        for img in targets:
            pil_img = Image.open(img).convert("RGB")
            pixel_values = processor(images=pil_img, return_tensors="pt").pixel_values.to(device)
            generated_ids = model.generate(pixel_values, max_new_tokens=128)
            text_tr = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            texts.append(text_tr)
            
            # TrOCR: confiance estimée à 0.75
            words = text_tr.split()
            for word in words:
                if word.strip():
                    word_confidence_data.append({
                        "word": word,
                        "confidence": 0.75
                    })
                    
        ocr_time = round(time.time() - t0, 2)
        cleanup_tmp(tmp_files)

        print(json.dumps({
            "status": "success",
            "model": "TrOCR",
            "file_type": file_type,
            "text": "\n".join(texts),
            "word_confidence": word_confidence_data,
            "init_time": init_time,
            "ocr_time": ocr_time,
            "total_time": round(init_time + ocr_time, 2)
        }))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
