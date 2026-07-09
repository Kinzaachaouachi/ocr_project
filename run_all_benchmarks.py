#!/usr/bin/env python3

import os
import sys
import time
import json
import re
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw

os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_DISABLE_MKLDNN"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

DEFAULT_IMAGE = "demo_images/demo_text.png"
CORPUS_DIR = Path("corpus_test")

GROUND_TRUTH = """TEXTE DE TEST
Ligne 2: Evaluation OCR
PaddleOCR Test 2026"""

CORPUS_SAMPLES = [
    {"file": "01_texte_simple.png", "size": (520, 90), "lines": ["Bonjour le monde"]},
    {"file": "02_multiligne.png", "size": (600, 160), "lines": ["Premiere ligne", "Deuxieme ligne", "Troisieme ligne"]},
    {"file": "03_chiffres.png", "size": (480, 90), "lines": ["Facture 12345 du 23/06/2026"]},
    {"file": "04_accents_francais.png", "size": (620, 90), "lines": ["Éléphant à Noël en français"]},
    {"file": "05_majuscules.png", "size": (560, 90), "lines": ["DOCUMENT OFFICIEL CONFIDENTIEL"]},
    {"file": "06_phrase_longue.png", "size": (800, 100), "lines": ["Evaluation OCR open source avec PaddleOCR et Docling"]},
    {"file": "07_texte_bleu.png", "size": (540, 90), "lines": ["Texte en couleur bleue"], "color": (0, 80, 200)},
    {"file": "08_liste.png", "size": (500, 180), "lines": ["Item A", "Item B", "Item C", "Item D"]},
    {"file": "09_adresse.png", "size": (650, 120), "lines": ["12 rue de la Paix", "75002 Paris France"]},
    {"file": "10_ligne_unique.png", "size": (420, 70), "lines": ["OCR test rapide"]},
]


def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def calculate_accuracy(recognized, ground_truth):
    def normalize(t):
        return ' '.join(re.sub(r'[^a-z0-9\s]', '', t.lower()).split())
    norm_rec = normalize(recognized)
    norm_gt = normalize(ground_truth)
    if not norm_rec or not norm_gt:
        return 0.0
    dist = levenshtein_distance(norm_rec, norm_gt)
    return round((1 - dist / max(len(norm_rec), len(norm_gt))) * 100, 1)


def _draw_text_image(size, lines, color=(0, 0, 0)):
    img = Image.new("RGB", size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 20
    for line in lines:
        draw.text((30, y), line, fill=color)
        y += 35
    return img


def ensure_demo_image():
    demo_path = Path(DEFAULT_IMAGE)
    demo_path.parent.mkdir(parents=True, exist_ok=True)
    if not demo_path.exists():
        _draw_text_image((700, 200), GROUND_TRUTH.split("\n")).save(demo_path)
    return str(demo_path)


def ensure_corpus_test():
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    ground_truth = {}
    for sample in CORPUS_SAMPLES:
        path = CORPUS_DIR / sample["file"]
        text = "\n".join(sample["lines"])
        ground_truth[sample["file"]] = text
        if not path.exists():
            color = sample.get("color", (0, 0, 0))
            _draw_text_image(sample["size"], sample["lines"], color).save(path)
    gt_path = CORPUS_DIR / "ground_truth.json"
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2, ensure_ascii=False)
    return ground_truth



parser = argparse.ArgumentParser()
parser.add_argument("--run", choices=["paddleocr", "docling", "easyocr", "trocr"])
parser.add_argument("--image", default=None)
args = parser.parse_args()

if args.run:
    target_image = args.image or ensure_demo_image()
    if not os.path.exists(target_image):
        print(json.dumps({"status": "error", "error": f"Image not found: {target_image}"}))
        sys.exit(1)

    if args.run == "paddleocr":
        try:
            t0 = time.time()
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang="fr", use_gpu=False, show_log=False)
            init_time = time.time() - t0
            t0 = time.time()
            res = ocr.ocr(target_image, cls=True)
            ocr_time = time.time() - t0
            text = "\n".join([line[1][0] for line in res[0]]) if res and res[0] else ""
            print(json.dumps({"status": "success", "init_time": init_time, "ocr_time": ocr_time, "text": text}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
            
    elif args.run == "docling":
        try:
            t0 = time.time()
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            init_time = time.time() - t0
            t0 = time.time()
            
            import os
            abs_path = os.path.abspath(target_image)
            
            res_doc = converter.convert(abs_path)
            text = res_doc.document.export_to_markdown().strip()
            ocr_time = time.time() - t0
            print(json.dumps({"status": "success", "init_time": init_time, "ocr_time": ocr_time, "text": text}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
            
    elif args.run == "easyocr":
        try:
            t0 = time.time()
            import easyocr
            reader = easyocr.Reader(['fr', 'en'], gpu=False)
            init_time = time.time() - t0
            t0 = time.time()
            res = reader.readtext(target_image)
            ocr_time = time.time() - t0
            text = "\n".join([line[1] for line in res])
            print(json.dumps({"status": "success", "init_time": init_time, "ocr_time": ocr_time, "text": text}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
            
    elif args.run == "trocr":
        try:
            t0 = time.time()
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            processor = TrOCRProcessor.from_pretrained("microsoft/trocr-small-printed")
            model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-small-printed").to(device)
            init_time = time.time() - t0
            t0 = time.time()
            image = Image.open(target_image).convert("RGB")
            pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
            generated_ids = model.generate(pixel_values)
            text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            ocr_time = time.time() - t0
            print(json.dumps({"status": "success", "init_time": init_time, "ocr_time": ocr_time, "text": text}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
    sys.exit(0)


def main():
    print("="*80)
    print(" BENCHMARK COMPARATIF DES 4 MODELES OCR")
    print("="*80)

    image_path = ensure_demo_image()
    ensure_corpus_test()
    
    stats = {}
    models = ["paddleocr", "docling", "easyocr", "trocr"]
    
    for model in models:
        print(f"Execution {model}...")
        cmd = [sys.executable, __file__, "--run", model]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=300)
        
        json_data = None
        for line in res.stdout.strip().split("\n"):
            if line.strip().startswith("{"):
                try:
                    json_data = json.loads(line)
                    break
                except:
                    continue
        
        if json_data and json_data["status"] == "success":
            acc = calculate_accuracy(json_data["text"], GROUND_TRUTH)
            stats[model] = {
                "status": "success",
                "init_time": round(json_data["init_time"], 2),
                "ocr_time": round(json_data["ocr_time"], 2),
                "total_time": round(json_data["init_time"] + json_data["ocr_time"], 2),
                "accuracy": acc,
                "text": json_data["text"]
            }
            print(f"Précision: {acc}% | Temps: {stats[model]['ocr_time']}s")
        else:
            stats[model] = {"status": "error", "error": "Failed"}
            print(f"  ERREUR")
    
    print("\n" + "="*80)
    print("RESULTATS FINAUX")
    print("="*80)
    print(f"| {'Modele':<15} | {'Init (s)':<10} | {'OCR (s)':<10} | {'Total (s)':<10} | {'Precision (%)':<15} |")
    print("-"*80)
    
    for model in models:
        m = stats[model]
        if m["status"] == "success":
            print(f"| {model.upper():<15} | {m['init_time']:<10.2f} | {m['ocr_time']:<10.2f} | {m['total_time']:<10.2f} | {m['accuracy']:<15.1f} |")
        else:
            print(f"| {model.upper():<15} | {'ERROR':<10} | {'ERROR':<10} | {'ERROR':<10} | {'0.0':<15} |")
    print("="*80)
    
    results = {
        "timestamp": datetime.now().strftime("%d %B %Y %H:%M:%S"),
        "stats": stats
    }
    
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n Fichier sauvegardé: benchmark_results.json")
    print(" Rapport HTML disponible: http://127.0.0.1:8000/benchmark")


if __name__ == "__main__":
    main()
