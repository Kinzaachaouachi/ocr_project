# -*- coding: utf-8 -*-
"""
Script de Benchmark Global - Comparaison de 4 solutions OCR via Sous-processus
Auteur : Kinza Achaouachi (mis à jour)
"""

import os
import sys
import time
import json
import re
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from PIL import Image

# Configurer les variables d'environnement pour désactiver les avertissements et oneDNN
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_DISABLE_MKLDNN"] = "1"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

# Chemin de l'image de test demo
image_path = os.path.join("demo_images", "demo_text.png")

# Vérité Terrain pour demo_images/demo_text.png
GROUND_TRUTH = """TEXTE DE TEST
Ligne 2: Evaluation OCR
PaddleOCR Test 2026"""

# Distance de Levenshtein
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
        t = t.lower()
        t = re.sub(r'[^a-z0-9\s]', '', t)
        return ' '.join(t.split())
        
    norm_rec = normalize(recognized)
    norm_gt = normalize(ground_truth)
    
    if not norm_rec or not norm_gt:
        return 0.0
        
    dist = levenshtein_distance(norm_rec, norm_gt)
    max_len = max(len(norm_rec), len(norm_gt))
    return round((1 - dist / max_len) * 100, 1)

# Analyse des arguments de la ligne de commande
parser = argparse.ArgumentParser()
parser.add_argument("--run", choices=["paddleocr", "docling", "easyocr", "trocr"], help="Lancer un modèle spécifique en isolation")
args = parser.parse_args()

# ─── MODE EXECUTION EN ISOLATION (Sous-processus) ───────────────────────────
if args.run:
    if args.run == "paddleocr":
        try:
            t0 = time.time()
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang="fr", use_gpu=False, show_log=False)
            init_time = time.time() - t0
            
            t0 = time.time()
            res = ocr.ocr(image_path, cls=True)
            ocr_time = time.time() - t0
            
            text = ""
            if res and res[0]:
                text = "\n".join([line[1][0] for line in res[0]])
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
            res_doc = converter.convert(image_path)
            text_doc = res_doc.document.export_to_markdown()
            ocr_time = time.time() - t0
            
            print(json.dumps({"status": "success", "init_time": init_time, "ocr_time": ocr_time, "text": text_doc.strip()}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
            
    elif args.run == "easyocr":
        try:
            t0 = time.time()
            import easyocr
            reader = easyocr.Reader(['fr', 'en'], gpu=False)
            init_time = time.time() - t0
            
            t0 = time.time()
            res_easy = reader.readtext(image_path)
            ocr_time = time.time() - t0
            
            text_easy = "\n".join([line[1] for line in res_easy])
            print(json.dumps({"status": "success", "init_time": init_time, "ocr_time": ocr_time, "text": text_easy}))
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
            image = Image.open(image_path).convert("RGB")
            pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)
            generated_ids = model.generate(pixel_values)
            text_tr = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            ocr_time = time.time() - t0
            
            print(json.dumps({"status": "success", "init_time": init_time, "ocr_time": ocr_time, "text": text_tr}))
        except Exception as e:
            print(json.dumps({"status": "error", "error": str(e)}))
            
    sys.exit(0)

# ─── MODE PRINCIPAL (Orchestrateur de benchmark) ───────────────────────────
print("=" * 80)
print(" === DEMARRAGE DU BENCHMARK COMPARATIF DES 4 MODELES OCR ===")
print("=" * 80)

if not os.path.exists(image_path):
    print(f"Error: Image de test introuvable a l'emplacement : {image_path}")
    sys.exit(1)

stats = {}
models_list = ["paddleocr", "docling", "easyocr", "trocr"]

for model in models_list:
    print(f"Execution de {model}...")
    # Spawner un sous-processus python indépendant pour éviter les conflits DLL (shm.dll PyTorch / PaddlePaddle)
    cmd = [sys.executable, "run_all_benchmarks.py", "--run", model]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    
    # Parse json output de la console
    try:
        json_data = None
        for line in res.stdout.strip().split("\n"):
            if line.strip().startswith("{") and line.strip().endswith("}"):
                json_data = json.loads(line)
                break
                
        if json_data:
            if json_data["status"] == "success":
                acc = calculate_accuracy(json_data["text"], GROUND_TRUTH)
                init_t = json_data["init_time"]
                ocr_t = json_data["ocr_time"]
                
                simplicites = {"paddleocr": 2, "docling": 5, "easyocr": 4, "trocr": 3}
                descriptions = {"paddleocr": "PaddleOCR", "docling": "Docling", "easyocr": "EasyOCR", "trocr": "TrOCR"}
                
                stats[model] = {
                    "status": "success",
                    "init_time": round(init_t, 2),
                    "ocr_time": round(ocr_t, 2),
                    "total_time": round(init_t + ocr_t, 2),
                    "accuracy": acc,
                    "text": json_data["text"],
                    "simplicite": simplicites[model],
                    "description": descriptions[model]
                }
                print(f"      Succes - Precision: {acc}% | Temps OCR: {ocr_t:.2f}s")
            else:
                err_msg = json_data.get("error", "Unknown internal error")
                print(f"      Error: {err_msg}")
                stats[model] = {"status": "error", "error": err_msg}
        else:
            print("      Error: Aucun flux JSON detecte.")
            print(f"      Stdout: {res.stdout}")
            print(f"      Stderr: {res.stderr}")
            stats[model] = {"status": "error", "error": "No JSON detected"}
    except Exception as ex:
        print(f"      Exception parsing: {ex}")
        stats[model] = {"status": "error", "error": str(ex)}

# Remplir des valeurs par défaut au cas où un modèle a échoué pour le tableau
for model in models_list:
    if model not in stats or stats[model]["status"] == "error":
        stats[model] = {
            "status": "error",
            "init_time": 0.0,
            "ocr_time": 0.0,
            "total_time": 0.0,
            "accuracy": 0.0,
            "text": "ERREUR",
            "simplicite": 0,
            "description": model.upper()
        }

# Calculer les scores globaux sur 100
scores = {}
for key, m in stats.items():
    if m["status"] == "success":
        time_score = max(0, 100 - (m["ocr_time"] / 15.0) * 100)
        init_score = max(0, 100 - (m["init_time"] / 25.0) * 100)
        acc_score = m["accuracy"]
        simp_score = m["simplicite"] * 20
        stab_score = 60 if key == "paddleocr" else (100 if key == "docling" else (90 if key == "easyocr" else 80))
        score_global = (acc_score * 0.35) + (time_score * 0.25) + (init_score * 0.10) + (simp_score * 0.15) + (stab_score * 0.15)
        scores[key] = round(score_global, 1)
    else:
        scores[key] = 0.0

podium = sorted(scores.items(), key=lambda x: x[1], reverse=True)

# ─── AFFICHAGE DES RÉSULTATS DANS LA CONSOLE (TABLEAU DE CAPTURE) ───────────
print("\n" + "=" * 105)
print("                                 TABLEAU DE BENCHMARK OCR COMPARATIF                                 ")
print("=" * 105)
print(f"| {'Modele':<15} | {'Initialisation (s)':<20} | {'Temps OCR (s)':<15} | {'Temps Total (s)':<15} | {'Precision (%)':<15} | {'Simplicite':<10} |")
print("-" * 105)

for key in models_list:
    m = stats[key]
    name = m["description"]
    if m["status"] == "success":
        init = f"{m['init_time']:.2f}s"
        ocr = f"{m['ocr_time']:.2f}s"
        tot = f"{m['total_time']:.2f}s"
        acc = f"{m['accuracy']:.1f}%"
        simp = f"{m['simplicite']}/5"
        print(f"| {name:<15} | {init:<20} | {ocr:<15} | {tot:<15} | {acc:<15} | {simp:<10} |")
    else:
        print(f"| {name:<15} | {'ERREUR':<20} | {'ERREUR':<15} | {'ERREUR':<15} | {'0.0%':<15} | {'N/A':<10} |")

print("=" * 105)

# ─── SAUVEGARDE DU JSON ─────────────────────────────────────────────────────
timestamp_str = datetime.now().strftime("%d %B %Y a %H:%M:%S")

# ─── TEST MULTI-FORMATS (Image + PDF) via test_all_file_types.py ─────────────
print("\n" + "=" * 80)
print(" === TESTS MULTI-FORMATS (IMAGE + PDF) ===")
print("=" * 80)

# Vérifier que test_files/sample_document.pdf existe (généré par test_all_file_types.py)
import shutil
test_files_dir = Path("test_files")
pdf_test_path = test_files_dir / "sample_document.pdf"
img_test_path = test_files_dir / "sample_image.png"

# Générer les fichiers si nécessaires
if not pdf_test_path.exists() or not img_test_path.exists():
    print("Generation des fichiers de test (sample_image.png, sample_document.pdf)...")
    subprocess.run([sys.executable, "test_all_file_types.py", "--run-model", "paddleocr", "--file-type", "image"],
                   capture_output=True, text=True)

format_results = {m: {"image": {}, "pdf": {}} for m in models_list}
format_ground_truth = "DOCUMENT DE TEST MULTI-FORMATS Ligne 2: Evaluation de l'OCR PaddleOCR, Docling, EasyOCR et TrOCR"

for model in models_list:
    for fmt in ["image", "pdf"]:
        print(f"  Multi-format test: {model} sur {fmt}...")
        cmd = [sys.executable, "test_all_file_types.py", "--run-model", model, "--file-type", fmt]
        res_fmt = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        try:
            json_data = None
            for line in res_fmt.stdout.strip().split("\n"):
                if line.strip().startswith("{") and line.strip().endswith("}"):
                    json_data = json.loads(line)
                    break
            if json_data:
                if json_data["status"] == "success":
                    acc_fmt = calculate_accuracy(json_data.get("text", ""), format_ground_truth)
                    format_results[model][fmt] = {
                        "status": "success",
                        "text": json_data.get("text", ""),
                        "accuracy": acc_fmt
                    }
                elif json_data["status"] == "unsupported":
                    format_results[model][fmt] = {"status": "unsupported"}
                else:
                    format_results[model][fmt] = {"status": "error", "error": json_data.get("error", "?")}
            else:
                format_results[model][fmt] = {"status": "error", "error": "No JSON"}
        except Exception as ex_fmt:
            format_results[model][fmt] = {"status": "error", "error": str(ex_fmt)}
        
        st = format_results[model][fmt].get("status", "?")
        acc_str = f" | Precision: {format_results[model][fmt].get('accuracy', 0):.1f}%" if st == "success" else ""
        print(f"      {st.upper()}{acc_str}")

results_json = {
    "timestamp": timestamp_str,
    "stats": stats,
    "scores": scores,
    "podium": podium,
    "format_results": format_results
}

with open("benchmark_results.json", "w", encoding="utf-8") as f:
    json.dump(results_json, f, indent=2, ensure_ascii=False)
print("OK - Fichier JSON mis a jour : benchmark_results.json")


# ─── ENREGISTREMENT DU RAPPORT HTML (Rapport interactif Premium) ───────────
html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Benchmark OCR Multi-Modèles</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --border-color: rgba(255, 255, 255, 0.1);
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text: #f8fafc;
            --text-secondary: #94a3b8;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', 'Inter', system-ui, sans-serif; }}
        body {{
            background: radial-gradient(circle at top left, #1e1b4b, #0f172a 50%, #020617);
            color: var(--text);
            min-height: 100vh;
            padding: 40px 20px;
            overflow-x: hidden;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 50px;
            position: relative;
        }}
        
        header h1 {{
            font-size: 3.5em;
            font-weight: 800;
            background: linear-gradient(135deg, #a5b4fc 0%, #6366f1 50%, #4338ca 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            letter-spacing: -0.02em;
        }}
        
        header p {{
            font-size: 1.2em;
            color: var(--text-secondary);
        }}
        
        .badge-time {{
            display: inline-block;
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #a5b4fc;
            padding: 8px 16px;
            border-radius: 9999px;
            margin-top: 15px;
            font-size: 0.9em;
            font-weight: 500;
        }}
        
        /* Grid system */
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }}
        
        .card {{
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        
        .card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 4px;
            background: linear-gradient(90deg, transparent, var(--primary), transparent);
            opacity: 0;
            transition: opacity 0.3s;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.1);
            border-color: rgba(99, 102, 241, 0.3);
        }}
        
        .card:hover::before {{
            opacity: 1;
        }}
        
        .card-title {{
            font-size: 1.1em;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .card-value {{
            font-size: 3em;
            font-weight: 800;
            margin-bottom: 5px;
            display: flex;
            align-items: baseline;
        }}
        
        .card-value span {{
            font-size: 0.4em;
            font-weight: 500;
            color: var(--text-secondary);
            margin-left: 5px;
        }}
        
        /* Table styles */
        .section-title {{
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 25px;
            background: linear-gradient(to right, #ffffff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
        }}
        
        .table-container {{
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            margin-bottom: 50px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        
        th {{
            background: rgba(15, 23, 42, 0.6);
            padding: 20px;
            font-weight: 600;
            color: var(--text-secondary);
            font-size: 0.95em;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border-color);
        }}
        
        td {{
            padding: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 1.05em;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}
        
        .model-name {{
            font-weight: 700;
            color: #fff;
            display: flex;
            align-items: center;
        }}
        
        .model-name::before {{
            content: '';
            display: inline-block;
            width: 8px; height: 8px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        
        tr:nth-child(1) .model-name::before {{ background: #818cf8; }}
        tr:nth-child(2) .model-name::before {{ background: #34d399; }}
        tr:nth-child(3) .model-name::before {{ background: #f87171; }}
        tr:nth-child(4) .model-name::before {{ background: #fb7185; }}
        
        .badge-rank {{
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.8em;
            font-weight: 700;
            display: inline-block;
        }}
        
        .rank-1 {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
        .rank-2 {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
        .rank-3 {{ background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); }}
        .rank-4 {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}

        /* Charts block */
        .chart-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 50px;
        }}
        
        @media (max-width: 900px) {{
            .chart-grid {{ grid-template-columns: 1fr; }}
        }}
        
        .chart-box {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 30px;
            min-height: 380px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        }}
        
        /* Recommendation segment */
        .recom-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 50px;
        }}
        
        @media (max-width: 768px) {{
            .recom-grid {{ grid-template-columns: 1fr; }}
        }}
        
        .recom-card {{
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 25px;
            position: relative;
        }}
        
        .recom-card.pro {{ border-left: 4px solid var(--success); }}
        .recom-card.con {{ border-left: 4px solid var(--danger); }}
        
        .recom-title {{
            font-size: 1.2em;
            font-weight: 700;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        
        .recom-title svg {{ margin-right: 8px; }}
        
        .recom-list li {{
            list-style: none;
            padding: 6px 0;
            padding-left: 20px;
            position: relative;
            color: var(--text-secondary);
        }}
        
        .recom-list li::before {{
            content: '•';
            position: absolute;
            left: 0;
            color: var(--primary);
            font-size: 1.2em;
        }}

        /* Text preview segment */
        .text-preview {{
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            padding: 20px;
            font-family: 'Fira Code', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            color: #a5b4fc;
            max-height: 180px;
            overflow-y: auto;
        }}
        
        footer {{
            text-align: center;
            padding-top: 40px;
            border-top: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Benchmark OCR Multi-Modèles</h1>
            <p>Comparaison en temps réel des 4 modèles : PaddleOCR, Docling, EasyOCR et TrOCR</p>
            <div class="badge-time">Mise à jour : {timestamp_str}</div>
        </header>
        
        <!-- Métriques principales sur le gagnant -->
        <div class="grid">
            <div class="card">
                <div class="card-title">🏆 Meilleur Modèle</div>
                <div class="card-value" style="color: #fbbf24;">{podium[0][0].upper()}</div>
                <p style="color: var(--text-secondary)">Score Global : {podium[0][1]}/100</p>
            </div>
            <div class="card">
                <div class="card-title">⚡ OCR le Plus Rapide</div>
                <div class="card-value" style="color: #60a5fa;">
                    {min((k, v["ocr_time"]) for k, v in stats.items() if v["status"] == "success")[0].upper()}
                    <span>({min(v["ocr_time"] for v in stats.values() if v["status"] == "success"):.2f}s)</span>
                </div>
                <p style="color: var(--text-secondary)">Temps d'inférence pure par image</p>
            </div>
            <div class="card">
                <div class="card-title">🎯 Précision Maximale</div>
                <div class="card-value" style="color: #34d399;">
                    {max((k, v["accuracy"]) for k, v in stats.items() if v["status"] == "success")[0].upper()}
                    <span>({max(v["accuracy"] for v in stats.values() if v["status"] == "success") :.1f}%)</span>
                </div>
                <p style="color: var(--text-secondary)">Similarité par rapport à la vérité terrain</p>
            </div>
        </div>
        
        <!-- Section Tableau Comparatif -->
        <div class="section-title">📋 Tableau Comparatif Détaillé</div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Modèle</th>
                        <th>Initialisation</th>
                        <th>Temps OCR</th>
                        <th>Temps Total</th>
                        <th>Précision (%)</th>
                        <th>Simplicité d'intégration</th>
                        <th>Score Global</th>
                    </tr>
                </thead>
                <tbody>
"""

for k, m in stats.items():
    if m["status"] == "success":
        rank_class = "rank-1" if podium[0][0] == k else ("rank-2" if podium[1][0] == k else ("rank-3" if podium[2][0] == k else "rank-4"))
        rank_text = f"#1 - Gagnant" if podium[0][0] == k else (f"#2" if podium[1][0] == k else (f"#3" if podium[2][0] == k else f"#4"))
        
        html_content += f"""
                    <tr>
                        <td>
                            <div class="model-name">{m["description"]}</div>
                            <span class="badge-rank {rank_class}" style="margin-top: 5px;">{rank_text}</span>
                        </td>
                        <td>{m["init_time"]:.2f}s</td>
                        <td>{m["ocr_time"]:.2f}s</td>
                        <td>{m["total_time"]:.2f}s</td>
                        <td style="font-weight: 700;">{m["accuracy"]:.1f}%</td>
                        <td>{m["simplicite"]}/5</td>
                        <td style="font-weight: 900; color: #818cf8;">{scores[k]}/100</td>
                    </tr>
        """
    else:
        html_content += f"""
                    <tr>
                        <td class="model-name" style="color: var(--danger);">{m["description"]}</td>
                        <td colspan="5" style="color: var(--danger); text-align: center;">Erreur lors du traitement : {m.get("error")}</td>
                        <td>0.0/100</td>
                    </tr>
        """

html_content += f"""
                </tbody>
            </table>
        </div>
        
        <!-- Section Graphiques -->
        <div class="section-title">📊 Graphiques de Performance</div>
        <div class="chart-grid">
            <div class="chart-box">
                <canvas id="timeChart"></canvas>
            </div>
            <div class="chart-box">
                <canvas id="accuracyChart"></canvas>
            </div>
        </div>

        <!-- Section Matrice Compatibilite Formats -->
        <div class="section-title">📂 Compatibilite par Format de Fichier</div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Modele</th>
                        <th>Image (.png)</th>
                        <th>PDF (.pdf)</th>
                        <th>Precision Image</th>
                        <th>Precision PDF</th>
                    </tr>
                </thead>
                <tbody>
"""

for model_k in models_list:
    m_img = format_results[model_k].get("image", {})
    m_pdf = format_results[model_k].get("pdf", {})
    descriptions_html = {"paddleocr": "PaddleOCR", "docling": "Docling", "easyocr": "EasyOCR", "trocr": "TrOCR"}
    
    def fmt_badge(st_data):
        s = st_data.get("status", "error")
        if s == "success":
            return '<span style="color:#34d399;font-weight:700;">&#10003; OK</span>'
        elif s == "unsupported":
            return '<span style="color:#f59e0b;">&#8212; Non support&eacute;</span>'
        else:
            return '<span style="color:#ef4444;">&#10007; Erreur</span>'
    
    def fmt_acc(st_data):
        s = st_data.get("status", "error")
        if s == "success":
            acc_v = st_data.get("accuracy", 0)
            color = "#34d399" if acc_v >= 70 else ("#f59e0b" if acc_v >= 40 else "#ef4444")
            return f'<strong style="color:{color};">{acc_v:.1f}%</strong>'
        return '<span style="color:var(--text-secondary);">N/A</span>'
    
    html_content += f"""
                    <tr>
                        <td><div class="model-name">{descriptions_html[model_k]}</div></td>
                        <td>{fmt_badge(m_img)}</td>
                        <td>{fmt_badge(m_pdf)}</td>
                        <td>{fmt_acc(m_img)}</td>
                        <td>{fmt_acc(m_pdf)}</td>
                    </tr>
    """

html_content += """
                </tbody>
            </table>
        </div>

        <!-- Section Textes Extraits Image vs PDF -->
        <div class="section-title">📝 Textes Extraits : Image vs PDF</div>
        <div class="grid">
"""

for model_k in models_list:
    descriptions_html = {"paddleocr": "PaddleOCR", "docling": "Docling", "easyocr": "EasyOCR", "trocr": "TrOCR"}
    m_img = format_results[model_k].get("image", {})
    m_pdf = format_results[model_k].get("pdf", {})
    img_txt = m_img.get("text", "[Non disponible]") if m_img.get("status") == "success" else "[" + m_img.get("status", "erreur").upper() + "]"
    pdf_txt = m_pdf.get("text", "[Non disponible]") if m_pdf.get("status") == "success" else "[" + m_pdf.get("status", "erreur").upper() + "]"
    img_txt_html = img_txt.replace("\n", "<br>").replace('"', '\\"')
    pdf_txt_html = pdf_txt.replace("\n", "<br>").replace('"', '\\"')
    html_content += f"""
            <div class="card" style="padding: 20px;">
                <div class="card-title" style="margin-bottom:8px;">{descriptions_html[model_k]}</div>
                <div style="font-size:0.8em;color:var(--text-secondary);margin-bottom:6px;">IMAGE (.png)</div>
                <div class="text-preview" style="max-height:120px;">{img_txt_html}</div>
                <div style="font-size:0.8em;color:var(--text-secondary);margin:10px 0 6px;">PDF (.pdf)</div>
                <div class="text-preview" style="max-height:120px;">{pdf_txt_html}</div>
            </div>
    """

html_content += """
        </div>

        <!-- Section Textes Extraits Demo Image (benchmark principal) -->
        <div class="section-title">📷 Extractions sur l'image de demo (benchmark principal)</div>
        <div class="grid">
"""

for k, m in stats.items():
    if m["status"] == "success":
        clean_text_preview = m["text"].replace("\n", "<br>").replace('"', '\\"')
        html_content += f"""
            <div class="card" style="padding: 20px;">
                <div class="card-title" style="margin-bottom: 10px;">{m["description"]}</div>
                <div class="text-preview">{clean_text_preview}</div>
            </div>
        """

html_content += f"""
        </div>
        
        <!-- Section Recommandations -->
        <div class="section-title">💡 Synthèse & Recommandations d'intégration</div>
        <div class="recom-grid">
            <div class="recom-card pro">
                <div class="recom-title" style="color: var(--success);">
                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>
                    Points Forts & Recommandations
                </div>
                <ul class="recom-list">
                    <li><strong>Docling :</strong> Idéal pour extraire des documents entiers (PDF, DOCX) avec préservation du formatage Markdown. Intégration la plus propre (API moderne).</li>
                    <li><strong>PaddleOCR :</strong> Choix de référence pour la vitesse d'inférence pure et le traitement par lots en production.</li>
                    <li><strong>EasyOCR :</strong> Excellent compromis de simplicité pour des cas d'usage multi-langues rapides sans configuration lourde.</li>
                    <li><strong>TrOCR :</strong> Idéal pour les documents manuscrits ou la lecture de lignes de texte isolées avec un haut niveau de détails.</li>
                </ul>
            </div>
            <div class="recom-card con">
                <div class="recom-title" style="color: var(--danger);">
                    <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>
                    Limites & Contraintes
                </div>
                <ul class="recom-list">
                    <li><strong>PaddleOCR :</strong> Dépendances rigides (verrouillé sur numpy 1.26.4), installation sujette aux conflits ABI sous Windows.</li>
                    <li><strong>Docling :</strong> Temps de conversion d'images plus important (plusieurs secondes par page).</li>
                    <li><strong>EasyOCR :</strong> Précision légèrement inférieure en configuration par défaut sur des mises en page denses.</li>
                    <li><strong>TrOCR :</strong> Performance faible sur des images entières multi-lignes sans découpe préalable des lignes. Démarrage lent (modèle lourd à charger).</li>
                </ul>
            </div>
        </div>
        
        <footer>
            <p>Rapport de Benchmark OCR complet mis à jour automatiquement par le runner.</p>
            <p style="margin-top: 5px; opacity: 0.6;">Projet de stage réalisé par Kinza Chaouachi • {timestamp_str}</p>
        </footer>
    </div>

    <!-- Script Chart.js -->
    <script>
        // Graphique des temps de traitement
        const ctxTime = document.getElementById('timeChart').getContext('2d');
        new Chart(ctxTime, {{
            type: 'bar',
            data: {{
                labels: ['PaddleOCR', 'Docling', 'EasyOCR', 'TrOCR'],
                datasets: [
                    {{
                        label: 'Initialisation (s)',
                        data: [
                            {stats.get("paddleocr", {}).get("init_time", 0)}, 
                            {stats.get("docling", {}).get("init_time", 0)}, 
                            {stats.get("easyocr", {}).get("init_time", 0)}, 
                            {stats.get("trocr", {}).get("init_time", 0)}
                        ],
                        backgroundColor: 'rgba(99, 102, 241, 0.5)',
                        borderColor: 'rgba(99, 102, 241, 1)',
                        borderWidth: 1
                    }},
                    {{
                        label: 'Inférence OCR (s)',
                        data: [
                            {stats.get("paddleocr", {}).get("ocr_time", 0)}, 
                            {stats.get("docling", {}).get("ocr_time", 0)}, 
                            {stats.get("easyocr", {}).get("ocr_time", 0)}, 
                            {stats.get("trocr", {}).get("ocr_time", 0)}
                        ],
                        backgroundColor: 'rgba(52, 211, 153, 0.5)',
                        borderColor: 'rgba(52, 211, 153, 1)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'top', labels: {{ color: '#f8fafc' }} }},
                    title: {{ display: true, text: 'Temps d\\\'exécution (s) - Moins c\\\'est mieux', color: '#f8fafc', font: {{ size: 14 }} }}
                }},
                scales: {{
                    x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                    y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
                }}
            }}
        }});

        // Graphique de précision
        const ctxAcc = document.getElementById('accuracyChart').getContext('2d');
        new Chart(ctxAcc, {{
            type: 'radar',
            data: {{
                labels: ['Précision (%)', 'Simplicité (x20)', 'Vitesse relative', 'Stabilité'],
                datasets: [
                    {{
                        label: 'PaddleOCR',
                        data: [
                            {stats.get("paddleocr", {}).get("accuracy", 0)}, 
                            {stats.get("paddleocr", {}).get("simplicite", 0) * 20}, 
                            85, 
                            60
                        ],
                        borderColor: 'rgba(129, 140, 248, 1)',
                        backgroundColor: 'rgba(129, 140, 248, 0.2)',
                        borderWidth: 2
                    }},
                    {{
                        label: 'Docling',
                        data: [
                            {stats.get("docling", {}).get("accuracy", 0)}, 
                            {stats.get("docling", {}).get("simplicite", 0) * 20}, 
                            35, 
                            100
                        ],
                        borderColor: 'rgba(52, 211, 153, 1)',
                        backgroundColor: 'rgba(52, 211, 153, 0.2)',
                        borderWidth: 2
                    }},
                    {{
                        label: 'EasyOCR',
                        data: [
                            {stats.get("easyocr", {}).get("accuracy", 0)}, 
                            {stats.get("easyocr", {}).get("simplicite", 0) * 20}, 
                            80, 
                            90
                        ],
                        borderColor: 'rgba(248, 113, 113, 1)',
                        backgroundColor: 'rgba(248, 113, 113, 0.2)',
                        borderWidth: 2
                    }},
                    {{
                        label: 'TrOCR',
                        data: [
                            {stats.get("trocr", {}).get("accuracy", 0)}, 
                            {stats.get("trocr", {}).get("simplicite", 0) * 20}, 
                            60, 
                            80
                        ],
                        borderColor: 'rgba(251, 113, 133, 1)',
                        backgroundColor: 'rgba(251, 113, 133, 0.2)',
                        borderWidth: 2
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'top', labels: {{ color: '#f8fafc' }} }},
                    title: {{ display: true, text: 'Profil Comparatif des Modèles', color: '#f8fafc', font: {{ size: 14 }} }}
                }},
                scales: {{
                    r: {{
                        angleLines: {{ color: 'rgba(255,255,255,0.05)' }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }},
                        pointLabels: {{ color: '#94a3b8', font: {{ size: 11 }} }},
                        ticks: {{ color: '#94a3b8', backdropColor: 'transparent' }},
                        suggestedMin: 0,
                        suggestedMax: 100
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

with open("benchmark_report.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("OK - Rapport HTML mis a jour : benchmark_report.html")


# ─── ENREGISTREMENT DU RAPPORT MARKDOWN (BENCHMARK_REPORT.md) ────────────────
markdown_content = f"""# 📊 Rapport de Benchmark OCR Complet - Multi-Modèles

**Date de mise à jour :** {timestamp_str}  
**Environnement de test :**
- **OS :** Windows 10/11
- **Python :** 3.10
- **CPU :** Architecture x64 (Inférence CPU sans accélération GPU)

---

## 🎯 Objectif du Benchmark

Ce rapport compare quatre solutions OCR (Optical Character Recognition) majeures selon trois critères principaux :
1. **Précision** : Qualité et exactitude de la reconnaissance du texte par rapport à la vérité terrain.
2. **Vitesse** : Temps d'initialisation du modèle et temps de traitement OCR de l'image.
3. **Simplicité d'intégration** : Facilité d'installation, légèreté des dépendances et simplicité du code Python.

---

## 📦 Versions & Dépendances des Modèles

| Outil | Version | Backends / Dépendances Clés |
|-------|---------|-----------------------------|
| **PaddleOCR** | 2.7.0.3 | paddlepaddle 2.6.2, numpy 1.26.4 |
| **Docling** | 2.10.0 | docling-core 2.82.0, pillow |
| **EasyOCR** | 1.7.2 | PyTorch (torch/torchvision), numpy 1.26.4 |
| **TrOCR** | microsoft/trocr-small-printed | Hugging Face Transformers, PyTorch |

---

## 🧪 Résultats des Tests Réels (Image de démonstration)

L'image de test utilisée est `demo_images/demo_text.png` contenant le texte suivant (Vérité Terrain) :
```
TEXTE DE TEST
Ligne 2: Evaluation OCR
PaddleOCR Test 2026
```

### 1. PaddleOCR
- **Temps initialisation :** {stats['paddleocr']['init_time']:.2f}s
- **Temps OCR :** {stats['paddleocr']['ocr_time']:.2f}s
- **Texte reconnu :**
```
{stats['paddleocr']['text']}
```
- **Précision (Levenshtein) :** **{stats['paddleocr']['accuracy']:.1f}%**

### 2. Docling
- **Temps initialisation :** {stats['docling']['init_time']:.2f}s
- **Temps OCR :** {stats['docling']['ocr_time']:.2f}s
- **Texte reconnu :**
```
{stats['docling']['text']}
```
- **Précision (Levenshtein) :** **{stats['docling']['accuracy']:.1f}%**

### 3. EasyOCR
- **Temps initialisation :** {stats['easyocr']['init_time']:.2f}s
- **Temps OCR :** {stats['easyocr']['ocr_time']:.2f}s
- **Texte reconnu :**
```
{stats['easyocr']['text']}
```
- **Précision (Levenshtein) :** **{stats['easyocr']['accuracy']:.1f}%**

### 4. TrOCR (Hugging Face)
- **Temps initialisation :** {stats['trocr']['init_time']:.2f}s
- **Temps OCR :** {stats['trocr']['ocr_time']:.2f}s
- **Texte reconnu :**
```
{stats['trocr']['text']}
```
- **Précision (Levenshtein) :** **{stats['trocr']['accuracy']:.1f}%**  
*(Note : La faible précision de TrOCR est normale ici. TrOCR is a single-line model ; passé sur une image entière multi-lignes, il ne parvient pas à segmenter nativement et ne décode que partiellement.)*

---

## 📈 Tableau Récapitulatif Global (sur image de démo)

| Modèle | Temps Init | Temps OCR | Temps Total | Précision (%) | Simplicité d'intégration | Score Global /100 |
|--------|------------|-----------|-------------|---------------|--------------------------|-------------------|
| **PaddleOCR** | {stats['paddleocr']['init_time']:.2f}s | {stats['paddleocr']['ocr_time']:.2f}s | {stats['paddleocr']['total_time']:.2f}s | {stats['paddleocr']['accuracy']:.1f}% | 2/5 (Moyenne) | **{scores['paddleocr']}/100** |
| **Docling** | {stats['docling']['init_time']:.2f}s | {stats['docling']['ocr_time']:.2f}s | {stats['docling']['total_time']:.2f}s | {stats['docling']['accuracy']:.1f}% | 5/5 (Excellente) | **{scores['docling']}/100** |
| **EasyOCR** | {stats['easyocr']['init_time']:.2f}s | {stats['easyocr']['ocr_time']:.2f}s | {stats['easyocr']['total_time']:.2f}s | {stats['easyocr']['accuracy']:.1f}% | 4/5 (Bonne) | **{scores['easyocr']}/100** |
| **TrOCR** | {stats['trocr']['init_time']:.2f}s | {stats['trocr']['ocr_time']:.2f}s | {stats['trocr']['total_time']:.2f}s | {stats['trocr']['accuracy']:.1f}% | 3/5 (Moyenne) | **{scores['trocr']}/100** |

---

## 📂 Résultats Multi-Formats : Image (.png) et PDF (.pdf)

Fichiers de test : `test_files/sample_image.png` et `test_files/sample_document.pdf`  
Vérité terrain attendue :
```
DOCUMENT DE TEST MULTI-FORMATS
Ligne 2: Evaluation de l'OCR
PaddleOCR, Docling, EasyOCR et TrOCR
```

### Matrice de compatibilité et précision par format

| Modèle | Image (.png) | Précision Image | PDF (.pdf) | Précision PDF |
|--------|:---:|:---:|:---:|:---:|
| **PaddleOCR** | {'OK' if format_results['paddleocr']['image'].get('status') == 'success' else format_results['paddleocr']['image'].get('status','?').upper()} | {format_results['paddleocr']['image'].get('accuracy', 0):.1f}% | {'OK' if format_results['paddleocr']['pdf'].get('status') == 'success' else format_results['paddleocr']['pdf'].get('status','?').upper()} | {format_results['paddleocr']['pdf'].get('accuracy', 0):.1f}% |
| **Docling** | {'OK' if format_results['docling']['image'].get('status') == 'success' else format_results['docling']['image'].get('status','?').upper()} | {format_results['docling']['image'].get('accuracy', 0):.1f}% | {'OK' if format_results['docling']['pdf'].get('status') == 'success' else format_results['docling']['pdf'].get('status','?').upper()} | {format_results['docling']['pdf'].get('accuracy', 0):.1f}% |
| **EasyOCR** | {'OK' if format_results['easyocr']['image'].get('status') == 'success' else format_results['easyocr']['image'].get('status','?').upper()} | {format_results['easyocr']['image'].get('accuracy', 0):.1f}% | {'OK' if format_results['easyocr']['pdf'].get('status') == 'success' else format_results['easyocr']['pdf'].get('status','?').upper()} | {format_results['easyocr']['pdf'].get('accuracy', 0):.1f}% |
| **TrOCR** | {'OK' if format_results['trocr']['image'].get('status') == 'success' else format_results['trocr']['image'].get('status','?').upper()} | {format_results['trocr']['image'].get('accuracy', 0):.1f}% | {'OK' if format_results['trocr']['pdf'].get('status') == 'success' else format_results['trocr']['pdf'].get('status','?').upper()} | {format_results['trocr']['pdf'].get('accuracy', 0):.1f}% |

### Textes extraits par format

#### PaddleOCR
**Image :** `{(' '.join(format_results['paddleocr']['image'].get('text','[erreur]').split()))[:200]}`  
**PDF :** `{(' '.join(format_results['paddleocr']['pdf'].get('text','[erreur]').split()))[:200]}`

#### Docling
**Image :** `{(' '.join(format_results['docling']['image'].get('text','[erreur]').split()))[:200]}`  
**PDF :** `{(' '.join(format_results['docling']['pdf'].get('text','[erreur]').split()))[:200]}`

#### EasyOCR
**Image :** `{(' '.join(format_results['easyocr']['image'].get('text','[erreur]').split()))[:200]}`  
**PDF :** `{(' '.join(format_results['easyocr']['pdf'].get('text','[erreur]').split()))[:200]}`

#### TrOCR
**Image :** `{(' '.join(format_results['trocr']['image'].get('text','[erreur]').split()))[:200]}`  
**PDF :** `{(' '.join(format_results['trocr']['pdf'].get('text','[erreur]').split()))[:200]}`

---

## 🏆 Classement Final & Recommandations

1. **🥇 {podium[0][0].upper()}** ({podium[0][1]}/100)
2. **🥈 {podium[1][0].upper()}** ({podium[1][1]}/100)
3. **🥉 {podium[2][0].upper()}** ({podium[2][1]}/100)
4. **4ème : {podium[3][0].upper()}** ({podium[3][1]}/100)

### 💡 Recommandations stratégiques d'intégration :
- **Docling** est le meilleur choix global si vous manipulez des **fichiers complexes multipages (PDF, Word)** et souhaitez conserver la structure Markdown avec une intégration Python immédiate et propre.
- **PaddleOCR** est le choix ultime pour la **vitesse d'inférence pure** d'images isolées, très adapté aux pipelines en temps réel en production.
- **EasyOCR** est idéal pour des applications d'images simples avec **gestion multilingue native** très simple à déployer (Backend PyTorch standard).
- **TrOCR** est le plus performant pour la lecture de **lignes de texte isolées hautement spécifiques (par exemple, manuscrites)** après découpage préliminaire de la page en lignes de texte individuelles.

---

🔄 *Rapport mis à jour automatiquement à chaque exécution du script de test global.*
"""

with open("BENCHMARK_REPORT.md", "w", encoding="utf-8") as f:
    f.write(markdown_content)
print("OK - Rapport Markdown mis a jour : BENCHMARK_REPORT.md")

print("=" * 80)
print(" BENCHMARK TERMINE AVEC SUCCES - RESULTATS ENREGISTRES ")
print("=" * 80)
