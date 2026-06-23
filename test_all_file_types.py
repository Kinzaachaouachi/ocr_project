# -*- coding: utf-8 -*-
"""
Script de Test Multi-Formats pour PaddleOCR, Docling, EasyOCR et TrOCR
Auteur : Kinza Achaouachi (mis à jour)
"""

import os
import sys
import time
import json
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

# Vérité terrain pour les fichiers créés
IMAGE_TEXT_LINES = [
    "DOCUMENT DE TEST MULTI-FORMATS",
    "Ligne 2: Evaluation de l'OCR",
    "PaddleOCR, Docling, EasyOCR et TrOCR"
]
TEXT_CONTENT = "\n".join(IMAGE_TEXT_LINES)

# Dossier de test
test_dir = Path("test_files")
test_dir.mkdir(exist_ok=True)

# ─── Étape 1 : Génération des fichiers de test ──────────────────────────────

# 1. Image PNG
img_path = test_dir / "sample_image.png"
if not img_path.exists():
    img = Image.new("RGB", (800, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Dessiner les lignes de texte
    draw.text((40, 50), IMAGE_TEXT_LINES[0], fill=(0, 0, 0))
    draw.text((40, 120), IMAGE_TEXT_LINES[1], fill=(30, 80, 200))
    draw.text((40, 190), IMAGE_TEXT_LINES[2], fill=(0, 120, 50))
    img.save(img_path)

# 2. Document PDF
pdf_path = test_dir / "sample_document.pdf"
if not pdf_path.exists():
    try:
        import img2pdf
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(str(img_path)))
    except ImportError:
        # Fallback si img2pdf n'est pas dispo
        pass

# 3. Fichier Texte TXT
txt_path = test_dir / "sample_text.txt"
if not txt_path.exists():
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(TEXT_CONTENT)


# ─── Étape 2 : Mode exécution isolé pour chaque modèle et format ───────────
parser = argparse.ArgumentParser()
parser.add_argument("--run-model", choices=["paddleocr", "docling", "easyocr", "trocr"])
parser.add_argument("--file-type", choices=["image", "pdf", "txt"])
args = parser.parse_args()

if args.run_model and args.file_type:
    # Déterminer le fichier cible
    target_file = ""
    if args.file_type == "image":
        target_file = str(img_path)
    elif args.file_type == "pdf":
        target_file = str(pdf_path)
    elif args.file_type == "txt":
        target_file = str(txt_path)
        
    # Helper pour convertir un PDF en images si nécessaire (pour les moteurs d'OCR pure)
    def get_pdf_pages_as_images(pdf_file):
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_file)
            page_images = []
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                out_img = test_dir / f"temp_pdf_page_{i}.png"
                pix.save(str(out_img))
                page_images.append(str(out_img))
            return page_images
        except Exception as e:
            return []

    # 1. PADDLEOCR
    if args.run_model == "paddleocr":
        if args.file_type == "txt":
            print(json.dumps({"status": "unsupported", "reason": "L'OCR ne supporte pas nativement les fichiers texte brut."}))
            sys.exit(0)
            
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang="fr", use_gpu=False, show_log=False)
            
            targets = [target_file]
            if args.file_type == "pdf":
                targets = get_pdf_pages_as_images(target_file)
                if not targets:
                    raise Exception("Impossible de convertir le PDF en images.")
            
            text_extracted = []
            for img_t in targets:
                res = ocr.ocr(img_t, cls=True)
                if res and res[0]:
                    text_extracted.append("\n".join([line[1][0] for line in res[0]]))
                # Nettoyer l'image temporaire si PDF
                if args.file_type == "pdf" and os.path.exists(img_t):
                    os.remove(img_t)
                    
            print(json.dumps({"status": "success", "text": "\n".join(text_extracted)}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))

    # 2. DOCLING
    elif args.run_model == "docling":
        try:
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            res_doc = converter.convert(target_file)
            text_extracted = res_doc.document.export_to_markdown()
            print(json.dumps({"status": "success", "text": text_extracted.strip()}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))

    # 3. EASYOCR
    elif args.run_model == "easyocr":
        if args.file_type == "txt":
            print(json.dumps({"status": "unsupported", "reason": "L'OCR ne supporte pas nativement les fichiers texte brut."}))
            sys.exit(0)
            
        try:
            import easyocr
            reader = easyocr.Reader(['fr', 'en'], gpu=False)
            
            targets = [target_file]
            if args.file_type == "pdf":
                targets = get_pdf_pages_as_images(target_file)
                if not targets:
                    raise Exception("Impossible de convertir le PDF en images.")
            
            text_extracted = []
            for img_t in targets:
                res = reader.readtext(img_t)
                if res:
                    text_extracted.append("\n".join([line[1] for line in res]))
                # Nettoyer l'image temporaire si PDF
                if args.file_type == "pdf" and os.path.exists(img_t):
                    os.remove(img_t)
                    
            print(json.dumps({"status": "success", "text": "\n".join(text_extracted)}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))

    # 4. TROCR
    elif args.run_model == "trocr":
        if args.file_type == "txt":
            print(json.dumps({"status": "unsupported", "reason": "L'OCR ne supporte pas nativement les fichiers texte brut."}))
            sys.exit(0)
            
        try:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            processor = TrOCRProcessor.from_pretrained("microsoft/trocr-small-printed")
            model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-small-printed").to(device)
            
            targets = [target_file]
            if args.file_type == "pdf":
                targets = get_pdf_pages_as_images(target_file)
                if not targets:
                    raise Exception("Impossible de convertir le PDF en images.")
            
            text_extracted = []
            for img_t in targets:
                pil_img = Image.open(img_t).convert("RGB")
                pixel_values = processor(images=pil_img, return_tensors="pt").pixel_values.to(device)
                generated_ids = model.generate(pixel_values)
                text_tr = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                text_extracted.append(text_tr)
                # Nettoyer l'image temporaire si PDF
                if args.file_type == "pdf" and os.path.exists(img_t):
                    os.remove(img_t)
                    
            print(json.dumps({"status": "success", "text": "\n".join(text_extracted)}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))

    sys.exit(0)

# ─── MODE PRINCIPAL (Orchestrateur multi-format) ───────────────────────────
print("=" * 90)
print(" === RUNNER MULTI-FORMATS : EVALUATION PAR TYPE DE FICHIER ===")
print("=" * 90)
print(f"Fichiers generes dans {test_dir}/ :")
print(f"  - Image : sample_image.png")
print(f"  - PDF   : sample_document.pdf")
print(f"  - Texte : sample_text.txt")
print("-" * 90)

models = ["paddleocr", "docling", "easyocr", "trocr"]
formats = ["image", "pdf", "txt"]

results = {m: {f: {} for f in formats} for m in models}

for model in models:
    for fmt in formats:
        print(f"Test de {model:<10} sur format {fmt:<5} ...")
        cmd = [sys.executable, "test_all_file_types.py", "--run-model", model, "--file-type", fmt]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        
        try:
            json_data = None
            for line in res.stdout.strip().split("\n"):
                if line.strip().startswith("{") and line.strip().endswith("}"):
                    json_data = json.loads(line)
                    break
                    
            if json_data:
                results[model][fmt] = json_data
            else:
                results[model][fmt] = {"status": "error", "error": "No JSON detected"}
        except Exception as ex:
            results[model][fmt] = {"status": "error", "error": str(ex)}

# Afficher la matrice des résultats
print("\n" + "=" * 90)
print("                                MATRICE DE COMPATIBILITE                                ")
print("=" * 90)
print(f"| {'Modele':<12} | {'Image (.png)':<22} | {'Document (.pdf)':<22} | {'Texte (.txt)':<22} |")
print("-" * 90)

descriptions = {
    "paddleocr": "PaddleOCR",
    "docling": "Docling",
    "easyocr": "EasyOCR",
    "trocr": "TrOCR"
}

for model in models:
    img_status = results[model]["image"]["status"]
    pdf_status = results[model]["pdf"]["status"]
    txt_status = results[model]["txt"]["status"]
    
    # Formater les chaines de statut
    def fmt_status(st_data):
        if st_data["status"] == "success":
            # Extraire un aperçu du texte extrait
            txt_extracted = st_data.get("text", "")
            # Remplacer les retours à la ligne par des espaces
            txt_flat = " ".join(txt_extracted.split())
            if len(txt_flat) > 12:
                return f"OK (\"{txt_flat[:9]}...\")"
            return f"OK (\"{txt_flat}\")"
        elif st_data["status"] == "unsupported":
            return "Non supporte"
        else:
            return "Erreur / Echec"

    img_str = fmt_status(results[model]["image"])
    pdf_str = fmt_status(results[model]["pdf"])
    txt_str = fmt_status(results[model]["txt"])
    
    print(f"| {descriptions[model]:<12} | {img_str:<22} | {pdf_str:<22} | {txt_str:<22} |")

print("=" * 90)
print("\n[NOTE] Pour les formats PDF, les moteurs d'OCR pure (PaddleOCR, EasyOCR, TrOCR)")
print("   utilisent PyMuPDF (fitz) pour convertir les pages en images en arriere-plan.")
print("   Docling quant a lui convertit le PDF de maniere native avec son propre moteur de structure.")
print("=" * 90)
